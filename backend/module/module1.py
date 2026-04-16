import asyncio
from fastapi import APIRouter, Query
import math
import random
from datetime import datetime, timedelta, timezone
import time as _time

# --- ROUTER MODULE 1 ---
router = APIRouter(prefix="/api")
_dashboard_analytics = None

# --- BIẾN GIÁM SÁT KẾT NỐI (UC001.3) ---
last_sensor_update_time = None
is_sensor_connected = False
connection_timeout_seconds = 30
latest_sensor_data = {}

def init_module1(analytics):
    global _dashboard_analytics
    _dashboard_analytics = analytics

def update_latest_sensor_data(payload):
    """Cập nhật dữ liệu cảm biến mới nhất (gọi từ server.py)"""
    global latest_sensor_data
    
    # Chuẩn hóa dữ liệu Servo (ID 6) trong payload trước khi lưu
    if "numberdevices" in payload:
        for dev in payload["numberdevices"]:
            if dev.get("numberdevice") == 6:
                try:
                    dev["status"] = 90 if int(dev.get("status", 0)) >= 45 else 0
                except (ValueError, TypeError):
                    dev["status"] = 0
                    
    latest_sensor_data = payload

def update_sensor_connection(now_vn):
    """Cập nhật thời điểm nhận dữ liệu mới nhất (gọi từ server.py)"""
    global last_sensor_update_time, is_sensor_connected
    last_sensor_update_time = now_vn
    if not is_sensor_connected:
        is_sensor_connected = True
        return True # Trạng thái vừa thay đổi từ False sang True
    return False

async def check_sensor_connection():
    """
    UC001.3 - Cảnh báo mất kết nối (Background Task)
    """
    global is_sensor_connected, last_sensor_update_time
    while True:
        await asyncio.sleep(5)
        if last_sensor_update_time and is_sensor_connected:
            tz_vn = timezone(timedelta(hours=7))
            now_vn = datetime.now(tz_vn)
            # Chuyển last_sensor_update_time sang aware nếu chưa có tzinfo để so sánh
            # (server.py đang dùng naive datetime cho DB nhưng aware cho so sánh)
            # Tuy nhiên server.py truyền vào naive (now_vn.replace(tzinfo=None))
            # Ta nên đồng bộ hết về naive hoặc aware. 
            # Trong server.py doc ghi: now_vn = datetime.now(tz_vn).replace(tzinfo=None)
            
            diff = (now_vn.replace(tzinfo=None) - last_sensor_update_time).total_seconds()
            
            if diff > connection_timeout_seconds:
                is_sensor_connected = False
                print(f"--- !!! CẢNH BÁO: Mất kết nối cảm biến (quá {connection_timeout_seconds}s) !!! ---")
                
                # Ghi log nguy hiểm
                if _dashboard_analytics and _dashboard_analytics.danger_collection is not None:
                    danger_data = {
                        "_id": now_vn,
                        "time": now_vn, # MongoDB sẽ tự convert sang UTC
                        "houseid": latest_sensor_data.get("houseid", "HS001"),
                        "type": f"Mất kết nối cảm biến (Quá {connection_timeout_seconds} giây)",
                        "value": {}
                    }
                    try:
                        await _dashboard_analytics.danger_collection.insert_one(danger_data)
                        print("--- Đã lưu log mất kết nối vào database ---")
                    except Exception as e:
                        print(f"Lỗi ghi log mất kết nối: {e}")

def start_monitoring():
    """Bắt đầu chạy background task giám sát"""
    asyncio.create_task(check_sensor_connection())

# --- ENDPOINTS MODULE 1 ---

@router.get("/sensor-data")
async def get_latest_data():
    """
    UC001.2 - Xem thông số môi trường
    Trả về dữ liệu môi trường mới nhất cho giao diện web.
    """
    import module.module3 as module3
    if not latest_sensor_data:
        return {"temp": "--", "humi": "--", "light": "--", "time": "Chờ...", "connected": is_sensor_connected}
    
    data_to_send = latest_sensor_data.copy()
    if "_id" in data_to_send:
        data_to_send["_id"] = str(data_to_send["_id"])
    #! Gửi thêm trạng thái thiết bị hiện tại cho Dashboard React
    data_to_send["numberdevice"] = module3.device_status
    # Gửi trạng thái kết nối
    data_to_send["connected"] = is_sensor_connected
    return data_to_send

@router.get("/sensor-comparison")
async def get_sensor_comparison():
    """Trả về dữ liệu so sánh lấy từ DB."""
    return await _dashboard_analytics.get_sensor_comparison_data()

@router.get("/weekly-trend")
async def get_weekly_trend(period: str = Query("week")):
    """Legacy endpoint — redirect to realtime."""
    return await _dashboard_analytics.get_realtime_trend_data()

@router.get("/realtime-trend")
async def get_realtime_trend():
    """Trả về dữ liệu xu hướng realtime từ DB."""
    return await _dashboard_analytics.get_realtime_trend_data()

@router.get("/sensor-alerts")
async def get_sensor_alerts():
    """Trả về cảnh báo lấy từ collection nguy hiểm."""
    return await _dashboard_analytics.get_sensor_alerts_data()

@router.get("/history-by-date")
async def get_history_by_date(date: str = Query("2026-03-09")):
    """Lấy lịch sử cảm biến theo ngày từ DB."""
    try:
        cursor = _dashboard_analytics.sensor_collection.find({"date": date}).sort("_id", 1)
        results = await cursor.to_list(length=100)
        for item in results:
            item["_id"] = str(item["_id"])
        return results
    except Exception as e:
        return {"error": str(e)}

# --- IN-MEMORY SENSOR HISTORY (for mock comparison & realtime trend) ---
# Mỗi entry: {"timestamp": float, "temp": float, "humi": float, "light": int}
_sensor_history = []
_MAX_HISTORY = 500  # Lưu tối đa 500 bản ghi

def record_sensor_reading(temp, humi, light):
    """Ghi nhận 1 lần đọc cảm biến vào bộ nhớ tạm (gọi từ mock_server)."""
    _sensor_history.append({
        "timestamp": _time.time(),
        "temp": temp, "humi": humi, "light": light,
    })
    if len(_sensor_history) > _MAX_HISTORY:
        _sensor_history = _sensor_history[-_MAX_HISTORY:]


# --- STATIC MOCK FUNCTIONS FOR MOCK_SERVER.PY ---

def get_sensor_comparison_data():
    """
    So sánh sensor hiện tại:
      TH1 (ưu tiên): So với trung bình trong ngày.
      TH2 (dự phòng): Nếu dữ liệu ngày < 3 bản ghi → so sánh với 5 phút trước.
    """
    now = _time.time()

    # Thu thập dữ liệu ngày (từ 00:00 hôm nay)
    tz_vn = timezone(timedelta(hours=7))
    today_start = datetime.now(tz_vn).replace(hour=0, minute=0, second=0, microsecond=0)
    today_ts = today_start.timestamp()

    today_data = [r for r in _sensor_history if r["timestamp"] >= today_ts]

    if len(today_data) >= 3 and len(_sensor_history) > 0:
        # TH1: So sánh với trung bình ngày
        avg_temp = sum(r["temp"] for r in today_data) / len(today_data)
        avg_humi = sum(r["humi"] for r in today_data) / len(today_data)
        avg_light = sum(r["light"] for r in today_data) / len(today_data)

        current = _sensor_history[-1]
        return {
            "temp": {"delta": round(current["temp"] - avg_temp, 1), "label": "So với trung bình ngày"},
            "humi": {"delta": round(current["humi"] - avg_humi, 1), "label": "So với trung bình ngày"},
            "light": {"delta": round(current["light"] - avg_light), "label": "So với trung bình ngày"},
        }

    # TH2: So sánh với 5 phút trước
    five_min_ago = now - 300
    old_data = [r for r in _sensor_history if r["timestamp"] <= five_min_ago]
    if old_data and len(_sensor_history) > 0:
        old = old_data[-1]
        current = _sensor_history[-1]
        return {
            "temp": {"delta": round(current["temp"] - old["temp"], 1), "label": "So với 5 phút trước"},
            "humi": {"delta": round(current["humi"] - old["humi"], 1), "label": "So với 5 phút trước"},
            "light": {"delta": round(current["light"] - old["light"]), "label": "So với 5 phút trước"},
        }

    # Chưa có dữ liệu → fallback cứng
    return {
        "temp": {"delta": 1.2, "label": "So với trung bình ngày"},
        "humi": {"delta": -2.1, "label": "So với trung bình ngày"},
        "light": {"delta": 30, "label": "So với trung bình ngày"},
    }


def get_realtime_trend_data():
    """
    Trả về 7 điểm dữ liệu ứng với: 30, 25, 20, 15, 10, 5, 0 phút trước.
    Nếu chưa đủ dữ liệu thật, sinh dữ liệu giả mô phỏng realtime.
    """
    now = _time.time()
    intervals = [30, 25, 20, 15, 10, 5, 0]  # phút trước
    labels = ["30", "25", "20", "15", "10", "5", "Hiện tại"]

    temp_data, humi_data, light_data = [], [], []

    for idx, mins in enumerate(intervals):
        target_ts = now - mins * 60
        # Tìm bản ghi gần nhất với thời điểm target
        closest = None
        min_diff = float("inf")
        for r in _sensor_history:
            diff = abs(r["timestamp"] - target_ts)
            if diff < min_diff:
                min_diff = diff
                closest = r

        if closest and min_diff < 180:  # Cho phép sai lệch 3 phút
            temp_data.append({"label": labels[idx], "value": closest["temp"]})
            humi_data.append({"label": labels[idx], "value": closest["humi"]})
            light_data.append({"label": labels[idx], "value": closest["light"]})
        else:
            # Sinh dữ liệu giả mô phỏng realistic
            base_temp = 28.5 + 1.2 * math.sin(mins * 0.12)
            base_humi = 65.0 + 3.0 * math.cos(mins * 0.1)
            base_light = 750 + 80 * math.sin(mins * 0.15)
            temp_data.append({"label": labels[idx], "value": round(base_temp + random.uniform(-0.3, 0.3), 1)})
            humi_data.append({"label": labels[idx], "value": round(base_humi + random.uniform(-1, 1), 1)})
            light_data.append({"label": labels[idx], "value": max(0, int(base_light + random.uniform(-15, 15)))})

    return {"temp": temp_data, "humi": humi_data, "light": light_data}


def get_sensor_alerts_data():
    """Trả về cảnh báo & nhận định dựa trên xu hướng (mock tạm thời để ghép FE)."""
    return [
        {
            "type": "warning", "title": "Nhiệt độ có xu hướng tăng",
            "message": "Nhiệt độ trung bình đã tăng 1.2°C so với tuần trước, cần theo dõi để điều chỉnh hệ thống làm mát phù hợp."
        },
        {
            "type": "info", "title": "Độ ẩm trong ngưỡng ổn định",
            "message": "Độ ẩm dao động từ 65-70%, nằm trong khoảng lý tưởng cho môi trường sống."
        },
        {
            "type": "success", "title": "Ánh sáng đạt chuẩn",
            "message": "Mức ánh sáng trung bình 840 lux, phù hợp cho hoạt động hàng ngày."
        },
    ]


# --- REAL DB ANALYTICS CLASS FOR SERVER.PY ---

class DashboardAnalytics:
    def __init__(self, sensor_collection, danger_collection=None):
        self.sensor_collection = sensor_collection
        self.danger_collection = danger_collection
        self.tz_vn = timezone(timedelta(hours=7))

    async def get_sensor_comparison_data(self):
        now_vn = datetime.now(self.tz_vn).replace(tzinfo=None)
        today_start_str = now_vn.strftime("%Y-%m-%d")
        
        # 1. Đo thời gian hệ thống thật sự chạy bằng cách xem record cũ nhất và mới nhất
        latest_cursor = self.sensor_collection.find({"date": today_start_str}).sort("time", -1).limit(1)
        latest_docs = await latest_cursor.to_list(1)
        
        oldest_cursor = self.sensor_collection.find({"date": today_start_str}).sort("time", 1).limit(1)
        oldest_docs = await oldest_cursor.to_list(1)
        
        if not latest_docs or not oldest_docs:
            return {
                "temp": {"delta": 0, "label": "Chưa đủ dữ liệu"},
                "humi": {"delta": 0, "label": "Chưa đủ dữ liệu"},
                "light": {"delta": 0, "label": "Chưa đủ dữ liệu"}
            }
            
        current = latest_docs[0]
        oldest = oldest_docs[0]
        
        diff_minutes = (current["time"] - oldest["time"]).total_seconds() / 60.0
        
        if diff_minutes < 4.8:
            # TH3: Dưới 5 phút
            return {
                "temp": {"delta": 0, "label": "Chưa đủ dữ liệu"},
                "humi": {"delta": 0, "label": "Chưa đủ dữ liệu"},
                "light": {"delta": 0, "label": "Chưa đủ dữ liệu"}
            }
        elif diff_minutes < 60:
            # TH2: Đã chạy từ 5 phút đến 1 tiếng
            five_min_ago = current["time"] - timedelta(minutes=5)
            old_cursor = self.sensor_collection.find({"time": {"$lte": five_min_ago}}).sort("time", -1).limit(1)
            old_docs = await old_cursor.to_list(1)
            
            if old_docs:
                old = old_docs[0]
                return {
                    "temp": {"delta": round(current.get("temp", 0) - old.get("temp", 0), 1), "label": "So với 5 phút trước"},
                    "humi": {"delta": round(current.get("humi", 0) - old.get("humi", 0), 1), "label": "So với 5 phút trước"},
                    "light": {"delta": round(current.get("light", 0) - old.get("light", 0)), "label": "So với 5 phút trước"}
                }
            return {
                "temp": {"delta": 0, "label": "Chưa đủ dữ liệu"},
                "humi": {"delta": 0, "label": "Chưa đủ dữ liệu"},
                "light": {"delta": 0, "label": "Chưa đủ dữ liệu"}
            }
        else:
            # TH1: Chạy qua 1 tiếng
            pipeline_today = [
                {"$match": {"date": today_start_str}},
                {"$group": {
                    "_id": None,
                    "avg_temp": {"$avg": "$temp"},
                    "avg_humi": {"$avg": "$humi"},
                    "avg_light": {"$avg": "$light"},
                }}
            ]
            today_res = await self.sensor_collection.aggregate(pipeline_today).to_list(1)
            
            if today_res:
                avg_data = today_res[0]
                return {
                    "temp": {"delta": round(current.get("temp", 0) - avg_data.get("avg_temp", 0), 1), "label": "So với trung bình ngày"},
                    "humi": {"delta": round(current.get("humi", 0) - avg_data.get("avg_humi", 0), 1), "label": "So với trung bình ngày"},
                    "light": {"delta": round(current.get("light", 0) - avg_data.get("avg_light", 0)), "label": "So với trung bình ngày"}
                }
            return {
                "temp": {"delta": 0, "label": "Chưa đủ dữ liệu"},
                "humi": {"delta": 0, "label": "Chưa đủ dữ liệu"},
                "light": {"delta": 0, "label": "Chưa đủ dữ liệu"}
            }

    async def get_realtime_trend_data(self):
        # 1. ĐÃ SỬA: Thêm .replace(tzinfo=None) để khớp với DB
        now_vn = datetime.now(self.tz_vn).replace(tzinfo=None)
        intervals = [30, 25, 20, 15, 10, 5, 0]
        labels = ["30", "25", "20", "15", "10", "5", "Hiện tại"]
        
        today_start_str = now_vn.strftime("%Y-%m-%d")
        
        try:
            oldest_cursor = self.sensor_collection.find({"date": today_start_str}).sort("time", 1).limit(1)
            oldest_docs = await oldest_cursor.to_list(1)
            
            if not oldest_docs:
                return {
                    "temp": [{"label": lb, "value": 0} for lb in labels],
                    "humi": [{"label": lb, "value": 0} for lb in labels],
                    "light": [{"label": lb, "value": 0} for lb in labels]
                }
                
            oldest_time = oldest_docs[0]["time"]
            
            # 2. ĐÃ SỬA: Xoá bỏ khối code check tzinfo cũ, trừ trực tiếp cực kỳ đơn giản
            diff_total_minutes = (now_vn - oldest_time).total_seconds() / 60.0
            
            res_temp, res_humi, res_light = [], [], []

            for idx, mins in enumerate(intervals):
                if mins > diff_total_minutes + 1: 
                    res_temp.append({"label": labels[idx], "value": 0})
                    res_humi.append({"label": labels[idx], "value": 0})
                    res_light.append({"label": labels[idx], "value": 0})
                else:
                    target_time = now_vn - timedelta(minutes=mins)
                    min_bound = target_time - timedelta(minutes=5)
                    
                    cursor = self.sensor_collection.find({
                        "time": {"$gte": min_bound, "$lte": target_time}
                    }).sort("time", -1).limit(1)
                    
                    docs = await cursor.to_list(1)
                    if docs:
                        doc = docs[0]
                        res_temp.append({"label": labels[idx], "value": doc.get("temp", 0)})
                        res_humi.append({"label": labels[idx], "value": doc.get("humi", 0)})
                        res_light.append({"label": labels[idx], "value": doc.get("light", 0)})
                    else:
                        res_temp.append({"label": labels[idx], "value": 0})
                        res_humi.append({"label": labels[idx], "value": 0})
                        res_light.append({"label": labels[idx], "value": 0})
                        
            return {
                "temp": res_temp,
                "humi": res_humi,
                "light": res_light
            }
            
        except Exception as e:
            print(f"[LỖI REALTIME-TREND]: {e}")
            return {
                "temp": [{"label": lb, "value": 0} for lb in labels],
                "humi": [{"label": lb, "value": 0} for lb in labels],
                "light": [{"label": lb, "value": 0} for lb in labels]
            }

    async def get_sensor_alerts_data(self):
        alerts = []
        if self.danger_collection is not None:
            try:
                danger_docs = await self.danger_collection.find().sort("time", -1).limit(3).to_list(3)
                for doc in danger_docs:
                    t = doc.get("time")
                    
                    # 1. Xử lý múi giờ Việt Nam
                    if isinstance(t, datetime):
                        vn_time = t
                        time_str = vn_time.strftime("%H:%M %d/%m")
                    else:
                        time_str = str(t)
                    
                    # 2. Xử lý bóc tách giá trị cảm biến để hiển thị đẹp hơn
                    val = doc.get('value', {})
                    if isinstance(val, dict):
                        # Lấy giá trị, nếu thiếu thì để '--' cho an toàn
                        temp = val.get('temp', '--')
                        humi = val.get('humi', '--')
                        light = val.get('light', '--')
                        sensor_detail = f"Nhiệt độ: {temp} độ C, Độ ẩm: {humi} %, Ánh sáng: {light}%"
                    else:
                        sensor_detail = str(val)

                    alerts.append({
                        "type": "warning", 
                        "title": f"Cảnh báo: {doc.get('type')}",
                        "message": f"Phát hiện lúc {time_str}. Vui lòng kiểm tra lại hệ thống. {sensor_detail}"
                    })
            except Exception as e:
                print(f"Lỗi lấy cảnh báo: {e}")

        if len(alerts) < 3:
            alerts.append({
                "type": "info", "title": "Độ ẩm hiện tại",
                "message": "Độ ẩm đang được giám sát từ cảm biến."
            })
            alerts.append({
                "type": "success", "title": "Hệ thống hoạt động",
                "message": "Cảm biến đang gửi dữ liệu bình thường."
            })
            
        return alerts[:3]
