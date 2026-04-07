from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Thứ tự ưu tiên của log level (càng cao càng nghiêm trọng)
LOG_LEVEL_ORDER = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}


class LogManager:
    def __init__(self, logs_collection, config_collection):
        self.logs_collection = logs_collection
        self.config_collection = config_collection
        self.tz_vn = timezone(timedelta(hours=7))

    # =============================================
    # HELPER: Lấy log level hiện tại từ DB config
    # =============================================
    async def _get_current_log_level(self) -> str:
        config = await self.config_collection.find_one({"type": "logging"})
        return config.get("level", "INFO") if config else "INFO"

    # =============================================
    # UC004.6 - GHI LOG (có check level filter)
    # =============================================
    async def log_event(self, device_id, level: str, message: str, value=None):
        """
        Ghi log vào DB.
        - Chỉ ghi nếu level của event >= level được cấu hình trong UC004.2.
        - Ví dụ: config level = WARNING → bỏ qua DEBUG và INFO.
        """
        current_level = await self._get_current_log_level()

        # So sánh mức độ: bỏ qua nếu event nhỏ hơn ngưỡng config
        if LOG_LEVEL_ORDER.get(level, 1) < LOG_LEVEL_ORDER.get(current_level, 1):
            return {
                "status": "skipped",
                "reason": f"level {level} below threshold {current_level}",
            }

        log_data = {
            "device_id": str(device_id),
            "level": level,
            "message": message,
            "value": value,
            "timestamp": datetime.now(self.tz_vn),
        }

        await self.logs_collection.insert_one(log_data)
        return {"status": "success"}

    # =============================================
    # UC004.2 - CẤU HÌNH LOG LEVEL
    # =============================================
    async def set_log_level(self, level: str):
        """
        Đặt mức log tối thiểu. Hợp lệ: DEBUG | INFO | WARNING | ERROR.
        """
        if level not in LOG_LEVEL_ORDER:
            return {
                "status": "error",
                "message": f"Invalid level: {level}. Valid: {list(LOG_LEVEL_ORDER.keys())}",
            }

        await self.config_collection.update_one(
            {"type": "logging"},
            {"$set": {"level": level, "updated_at": datetime.now(self.tz_vn)}},
            upsert=True,
        )
        return {"status": "success", "log_level": level}

    # =============================================
    # UC004.1 - CẤU HÌNH CHIẾN LƯỢC PHÂN TÍCH
    # =============================================
    async def set_strategy(self, strategy: str):
        """
        Đặt chiến lược phân tích. Hợp lệ: frequency | average | trend.
        - frequency : đếm số lần theo level
        - average   : tính trung bình value theo thiết bị
        - trend     : nhóm theo giờ/ngày, trả data vẽ chart
        """
        valid = {"frequency", "average", "trend"}
        if strategy not in valid:
            return {
                "status": "error",
                "message": f"Invalid strategy: {strategy}. Valid: {list(valid)}",
            }

        await self.config_collection.update_one(
            {"type": "analysis"},
            {"$set": {"strategy": strategy, "updated_at": datetime.now(self.tz_vn)}},
            upsert=True,
        )
        return {"status": "success", "strategy": strategy}

    # =============================================
    # UC004.5 - XEM LOG THÔ (có filter)
    # =============================================
    async def get_logs(
        self, level: str = None, device_id: str = None, limit: int = 100
    ):
        """
        Lấy danh sách log thô.
        - level     : lọc theo mức (INFO / WARNING / ERROR / DEBUG)
        - device_id : lọc theo thiết bị
        - limit     : giới hạn số dòng trả về (mặc định 100)
        """
        query = {}
        if level:
            query["level"] = level
        if device_id:
            query["device_id"] = str(device_id)

        cursor = self.logs_collection.find(query).sort("timestamp", -1).limit(limit)
        logs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            # Serialize datetime → string để JSON không lỗi
            if isinstance(doc.get("timestamp"), datetime):
                doc["timestamp"] = doc["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            logs.append(doc)
        return logs

    # =============================================
    # UC004.3 + UC004.4 - BÁO CÁO & PHÂN TÍCH
    # =============================================
    async def get_report(self, period: str = "day"):
        """
        Tạo báo cáo phân tích theo chu kỳ.
        - period: day | week | month
        Chiến lược phân tích lấy từ config UC004.1.
        """
        # Xác định khoảng thời gian lọc
        now = datetime.now(self.tz_vn)
        if period == "week":
            from_time = now - timedelta(days=7)
        elif period == "month":
            from_time = now - timedelta(days=30)
        else:  # day
            from_time = now - timedelta(days=1)

        # Query log trong khoảng thời gian
        cursor = self.logs_collection.find({"timestamp": {"$gte": from_time}}).sort(
            "timestamp", 1
        )

        logs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            logs.append(doc)

        # Lấy strategy hiện tại
        config = await self.config_collection.find_one({"type": "analysis"})
        strategy = config.get("strategy", "frequency") if config else "frequency"

        # Chạy phân tích UC004.4
        analysis = analyze_logs(logs, strategy, period)

        return {
            "period": period,
            "from": from_time.strftime("%Y-%m-%d %H:%M:%S"),
            "to": now.strftime("%Y-%m-%d %H:%M:%S"),
            "total_logs": len(logs),
            **analysis,
        }

    # =============================================
    # XEM CONFIG HIỆN TẠI
    # =============================================
    async def get_config(self):
        """Trả về cấu hình log level + strategy đang áp dụng."""
        logging_cfg = await self.config_collection.find_one({"type": "logging"})
        analysis_cfg = await self.config_collection.find_one({"type": "analysis"})

        return {
            "log_level": logging_cfg.get("level", "INFO") if logging_cfg else "INFO",
            "strategy": (
                analysis_cfg.get("strategy", "frequency")
                if analysis_cfg
                else "frequency"
            ),
        }


# ==================================================
# UC004.4 - CORE ANALYSIS ENGINE (Pure function)
# ==================================================
def analyze_logs(logs: list, strategy: str, period: str = "day") -> dict:
    """
    Nhận danh sách log thô, trả về kết quả phân tích theo strategy.

    strategy = "frequency" → đếm log theo level
    strategy = "average"   → tính trung bình value số theo device_id
    strategy = "trend"     → nhóm theo mốc thời gian (hour nếu day, day nếu week/month)
    """

    if strategy == "frequency":
        # -------------------------------------------
        # Đếm số lần xuất hiện của từng level
        # Kết quả: {"INFO": 42, "WARNING": 5, "ERROR": 1}
        # -------------------------------------------
        result = defaultdict(int)
        for log in logs:
            level = log.get("level", "UNKNOWN")
            result[level] += 1
        return {"strategy": strategy, "data": dict(result)}

    elif strategy == "average":
        # -------------------------------------------
        # Tính trung bình value (nếu là số) theo device_id
        # Kết quả: {"sensor": 28.5, "1": 0.6}
        # -------------------------------------------
        sum_val = defaultdict(float)
        count = defaultdict(int)

        for log in logs:
            dev = str(log.get("device_id", "unknown"))
            val = log.get("value")
            if isinstance(val, (int, float)):
                sum_val[dev] += val
                count[dev] += 1
            elif isinstance(val, dict):
                # value dạng {"temp": 30, "humi": 60} → tính trung bình từng key
                for k, v in val.items():
                    if isinstance(v, (int, float)):
                        key = f"{dev}.{k}"
                        sum_val[key] += v
                        count[key] += 1

        result = {}
        for key in sum_val:
            result[key] = round(sum_val[key] / count[key], 2)

        return {"strategy": strategy, "data": result}

    elif strategy == "trend":
        # -------------------------------------------
        # Nhóm log theo mốc thời gian để vẽ chart
        # - period = "day"          → nhóm theo giờ  (00:00 → 23:00)
        # - period = "week/month"   → nhóm theo ngày (2026-03-01 → ...)
        # Kết quả: [{"label": "08:00", "count": 5, "WARNING": 2, "ERROR": 1}, ...]
        # -------------------------------------------
        buckets = defaultdict(lambda: defaultdict(int))

        for log in logs:
            ts = log.get("timestamp")
            level = log.get("level", "INFO")

            # Parse timestamp nếu là string
            if isinstance(ts, str):
                try:
                    ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue

            if not isinstance(ts, datetime):
                continue

            if period == "day":
                label = ts.strftime("%H:00")  # Nhóm theo giờ
            else:
                label = ts.strftime("%Y-%m-%d")  # Nhóm theo ngày

            buckets[label]["count"] += 1
            buckets[label][level] += 1

        # Sắp xếp theo label (thời gian tăng dần)
        sorted_labels = sorted(buckets.keys())
        data = [{"label": lbl, **buckets[lbl]} for lbl in sorted_labels]

        return {"strategy": strategy, "data": data}

    else:
        return {
            "strategy": strategy,
            "data": {},
            "error": f"Unknown strategy: {strategy}",
        }
