from datetime import datetime, timezone, timedelta
from collections import defaultdict

LOG_LEVEL_ORDER = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}


class LogManager:
    def __init__(self, logs_collection, config_collection):
        self.logs_collection = logs_collection
        self.config_collection = config_collection
        self.tz_vn = timezone(timedelta(hours=7))

    # =========================
    # HELPER
    # =========================
    async def _get_current_log_level(self) -> str:
        config = await self.config_collection.find_one({"type": "logging"})
        return config.get("level", "INFO") if config else "INFO"

    # =========================
    # UC004.6 - GHI LOG
    # =========================
    async def log_event(self, device_id, level: str, message: str, value=None):
        current_level = await self._get_current_log_level()

        if LOG_LEVEL_ORDER.get(level, 1) < LOG_LEVEL_ORDER.get(current_level, 1):
            return {"status": "skipped"}

        log_data = {
            "device_id": str(device_id),
            "level": level,
            "message": message,
            "value": value,
            "timestamp": datetime.now(self.tz_vn),  # ✅ luôn là datetime
        }

        await self.logs_collection.insert_one(log_data)
        return {"status": "success"}

    # =========================
    # UC004.2 - LOG LEVEL
    # =========================
    async def set_log_level(self, level: str):
        if level not in LOG_LEVEL_ORDER:
            return {"status": "error", "message": "Invalid level"}

        await self.config_collection.update_one(
            {"type": "logging"},
            {"$set": {"level": level, "updated_at": datetime.now(self.tz_vn)}},
            upsert=True,
        )
        return {"status": "success", "log_level": level}

    # =========================
    # UC004.1 - STRATEGY
    # =========================
    async def set_strategy(self, strategy: str):
        valid = {"frequency", "average", "trend"}
        if strategy not in valid:
            return {"status": "error", "message": "Invalid strategy"}

        await self.config_collection.update_one(
            {"type": "analysis"},
            {"$set": {"strategy": strategy, "updated_at": datetime.now(self.tz_vn)}},
            upsert=True,
        )
        return {"status": "success", "strategy": strategy}

    # =========================
    # UC004.5 - GET LOGS
    # =========================
    async def get_logs(self, level=None, device_id=None, limit=100):
        query = {}
        if level:
            query["level"] = level
        if device_id:
            query["device_id"] = str(device_id)

        cursor = self.logs_collection.find(query).sort("timestamp", -1).limit(limit)

        logs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])

            # ✅ chỉ format khi trả API
            if isinstance(doc.get("timestamp"), datetime):
                doc["timestamp"] = (
                    doc["timestamp"]
                    .astimezone(self.tz_vn)
                    .strftime("%Y-%m-%d %H:%M:%S")
                )

            logs.append(doc)

        return logs

    # =========================
    # UC004.3 + UC004.4 - REPORT
    # =========================
    async def get_report(self, period="day"):
        now = datetime.now(self.tz_vn)

        if period == "week":
            from_time = now - timedelta(days=7)
        elif period == "month":
            from_time = now - timedelta(days=30)
        else:
            from_time = now - timedelta(days=1)

        cursor = self.logs_collection.find({"timestamp": {"$gte": from_time}}).sort(
            "timestamp", 1
        )

        logs = []
        async for doc in cursor:
            logs.append(doc)

        config = await self.config_collection.find_one({"type": "analysis"})
        strategy = config.get("strategy", "frequency") if config else "frequency"

        analysis = analyze_logs(logs, strategy, period)

        return {
            "period": period,
            "from": from_time.strftime("%Y-%m-%d %H:%M:%S"),
            "to": now.strftime("%Y-%m-%d %H:%M:%S"),
            "total_logs": len(logs),
            "strategy": analysis.get("strategy"),
            "data": analysis.get("data"),
        }

    # =========================
    # GET CONFIG
    # =========================
    async def get_config(self):
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


# =========================
# CORE ANALYSIS ENGINE
# =========================
def analyze_logs(logs: list, strategy: str, period: str = "day") -> dict:

    if strategy == "frequency":
        result = defaultdict(int)
        for log in logs:
            level = log.get("level", "UNKNOWN")
            result[level] += 1
        return {"strategy": strategy, "data": dict(result)}

    elif strategy == "average":
        sum_val = defaultdict(float)
        count = defaultdict(int)

        for log in logs:
            dev = str(log.get("device_id", "unknown"))
            val = log.get("value")

            if isinstance(val, (int, float)):
                sum_val[dev] += val
                count[dev] += 1

            elif isinstance(val, dict):
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
        buckets = defaultdict(lambda: defaultdict(int))

        for log in logs:
            ts = log.get("timestamp")
            level = log.get("level", "INFO")

            # ✅ chỉ xử lý datetime (không parse string nữa)
            if not isinstance(ts, datetime):
                continue

            if period == "day":
                label = ts.strftime("%H:00")
            else:
                label = ts.strftime("%Y-%m-%d")

            buckets[label]["count"] += 1
            buckets[label][level] += 1

        sorted_labels = sorted(buckets.keys())
        data = [{"label": lbl, **buckets[lbl]} for lbl in sorted_labels]

        return {"strategy": strategy, "data": data}

    else:
        return {"strategy": strategy, "data": {}}
