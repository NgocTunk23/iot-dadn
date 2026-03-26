# from fastapi import FastAPI, Body, Query
# from fastapi.responses import HTMLResponse
# from fastapi.middleware.cors import CORSMiddleware
# from motor.motor_asyncio import AsyncIOMotorClient
# from datetime import datetime, timedelta, timezone
# import os
# import uvicorn

# app = FastAPI()

# # 1. Cấu hình CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 2. Kết nối MongoDB
# MONGO_URL = os.getenv("MONGO_URL", "mongodb://db:27017")
# client = AsyncIOMotorClient(MONGO_URL)
# db = client.iot_database
# collection = db.sensor_history

# latest_sensor_data = {}

# @app.get("/", response_class=HTMLResponse)
# async def dashboard():
#     if not latest_sensor_data:
#         return "<h1>Đang chờ dữ liệu từ Yolobit...</h1>"
    
#     html_content = f"""
#     <html>
#         <head>
#             <title>IoT Dashboard - Toon</title>
#             <meta http-equiv="refresh" content="2">
#             <style>
#                 body {{ font-family: sans-serif; text-align: center; padding: 50px; background: #f4f4f4; }}
#                 .card {{ background: white; padding: 20px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 300px; }}
#                 .val {{ font-size: 2em; color: #007bff; font-weight: bold; }}
#             </style>
#         </head>
#         <body>
#             <div class="card">
#                 <h1>Dữ liệu Cảm Biến</h1>
#                 <p>Nhiệt độ: <span class="val">{latest_sensor_data.get('temp', '--')} °C</span></p>
#                 <p>Độ ẩm: <span class="val">{latest_sensor_data.get('humi', '--')} %</span></p>
#                 <p>Ánh sáng: <span class="val">{latest_sensor_data.get('light', '--')} %</span></p>
#                 <hr>
#                 <p>Cập nhật cuối: {latest_sensor_data.get('time', '--')}</p>
#             </div>
#         </body>
#     </html>
#     """
#     return html_content

# @app.post("/update")
# async def handle_data(payload: dict = Body(...)):
#     global latest_sensor_data
#     # Lấy thời gian hiện tại theo múi giờ UTC+7
#     tz_vn = timezone(timedelta(hours=7))
#     now_vn = datetime.now(tz_vn)
    
#     # Cấu trúc đồng nhất với script import
#     payload["_id"] = now_vn  # Khóa chính là thời gian hiện tại
#     payload["date"] = now_vn.strftime("%Y-%m-%d")
#     payload["time"] = now_vn.strftime("%H:%M:%S")
    
#     try:
#         await collection.insert_one(payload.copy())
#         latest_sensor_data = payload
#         print(f"--- Đã lưu DB: {payload['time']} ---")
#     except Exception as e:
#         print(f"Lỗi DB: {e}")
#     return {"status": "Success"}

# # API lấy dữ liệu theo ngày - ĐÃ SỬA LỖI TRẢ VỀ RỖNG []
# @app.get("/api/history-by-date")
# async def get_history_by_date(date: str = Query("2026-03-06")):
#     try:
#         # Tìm theo trường 'date' (dạng string) và sắp xếp theo '_id' (thời gian)
#         cursor = collection.find({"date": date}).sort("_id", 1)
#         results = await cursor.to_list(length=100)

#         for item in results:
#             # RẤT QUAN TRỌNG: Chuyển _id (datetime) sang string để JSON không bị lỗi rỗng
#             item["_id"] = str(item["_id"])
#         return results
#     except Exception as e:
#         return {"error": str(e)}
    

# @app.get("/api/sensor-data")
# async def get_latest_data():
#     if not latest_sensor_data:
#         return {"temp": "--", "humi": "--", "light": "--", "time": "Đang chờ..."}
    
#     # RẤT QUAN TRỌNG: Chuyển _id thành string trước khi trả về để tránh lỗi JSON
#     data_to_send = latest_sensor_data.copy()
#     if "_id" in data_to_send:
#         data_to_send["_id"] = str(data_to_send["_id"])
        
#     return data_to_send

# if __name__ == '__main__':
#     uvicorn.run(app, host='0.0.0.0', port=5000)






from fastapi import FastAPI, Body, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
import os
import uvicorn
from module.module3 import SceneManager, apply_scene_to_status
from module.module2 import (
    ThresholdManager,
    NotificationChannelManager,
    AutomationRuleManager,
    DangerChecker,
    AlertDispatcher,
)

app = FastAPI()

# 1. Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Kết nối MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://db:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.iot_database
collection = db.sensor_history
danger_collection = db.danger_logs   # Bảng log nguy hiểm
device_log_collection = db.device_logs # Bảng log thiết bị
scenes_collection = db.scenes        # Bảng kịch bản
scene_manager = SceneManager(scenes_collection)
thresholds_collection     = db.thresholds           
notif_channel_collection  = db.notification_channels 
automation_rules_col      = db.automation_rules      
 
threshold_mgr   = ThresholdManager(thresholds_collection)
channel_mgr     = NotificationChannelManager(notif_channel_collection)
rule_mgr        = AutomationRuleManager(automation_rules_col)
alert_dispatcher = AlertDispatcher(danger_collection, notif_channel_collection)

# --- BIẾN TOÀN CỤC ---
latest_sensor_data = {}
#! MẶC ĐỊNH LỆNH BE: 7 thiết bị (Đèn 1-5, Servo 6, Quạt 7)
device_status = [[1, False], [2, False], [3, False], [4, False], [5, False], [6, 0], [7, 0]]
# Biến phụ để so sánh sự thay đổi log
last_device_status = {}
# Lưu trạng thái nguy hiểm để báo về Yolobit
is_danger_global = False

# Biến UC001.3
last_sensor_update_time = None
is_sensor_connected = False
connection_timeout_seconds = 30


# --- ENDPOINT NHẬN DỮ LIỆU TỪ YOLOBIT ---

async def _process_danger_and_rules(payload, house_id, now_vn):
    global is_danger_global, device_status

    temp  = payload.get("temp",  0)
    humi  = payload.get("humi",  0)
    light = payload.get("light", 0)
    sensor_data = {"temp": temp, "humi": humi, "light": light}

    print(f"[DEBUG] Sensor data: {sensor_data}")

    thresholds = await threshold_mgr.get_thresholds(house_id)
    print(f"[DEBUG] Thresholds từ DB: {thresholds}")

    result = DangerChecker.check(sensor_data, thresholds)
    print(f"[DEBUG] Kết quả check: {result}")

    is_danger_global = result["is_danger"]

    triggered_rules = []

    # UC002.3: Đánh giá kịch bản tự động
    device_status, triggered_rules = await rule_mgr.evaluate_and_apply(
        house_id, sensor_data, device_status
    )

    if result["is_danger"]:
        print(f"[MODULE2] NGUY HIỂM! Vi phạm: {result['violations']}")
        channels_doc = await notif_channel_collection.find_one({"_id": house_id})
        print(f"[DEBUG] Channels trong DB: {channels_doc}")

        has_changes = any(
           c.get("changed")
           for rule in triggered_rules
           for c in rule.get("changes", [])
        )
        if not has_changes and triggered_rules:
           triggered_rules = [{
             "rule_name": triggered_rules[0]["rule_name"],
             "changes": [{"device_name": "Tất cả thiết bị", 
                         "changed": False,
                         "note": "Không có thay đổi so với trạng thái hiện tại"}]
        }]

        await alert_dispatcher.dispatch(
           house_id, result["violations"], sensor_data, device_status,
           triggered_rules=triggered_rules
        )
    else:
      await alert_dispatcher.auto_stop_alert(house_id, device_status, False)


@app.post("/update")
async def handle_data(payload: dict = Body(...)):
    global latest_sensor_data, last_device_status, is_danger_global
    tz_vn = timezone(timedelta(hours=7))
    now_vn = datetime.now(tz_vn)
    
    # Payload từ Yolobit main3.py có dạng:
    # { houseid: "HS001", temp: 30, humi: 60, light: 50, numberdevices: [{numberdevice: 1, status: True}, ...] }
    house_id = payload.get("houseid", "HS001")
    
    common_time = now_vn 
    payload["time"] = common_time # Dùng làm PK / _id
    payload["date"] = now_vn.strftime("%Y-%m-%d") # Phục vụ Lọc API 
    
    # 1. Ghi vào bảng sensor_history
    sensor_entry = payload.copy()
    sensor_entry["_id"] = common_time # MongoDB PK
    
    try:
        await collection.insert_one(sensor_entry)
        latest_sensor_data = payload
        
        # UC001.3: Cập nhật connection status
        global last_sensor_update_time, is_sensor_connected
        last_sensor_update_time = now_vn
        if not is_sensor_connected:
            is_sensor_connected = True
            print("--- Cảm biến đã KẾT NỐI lại ---")
            
        print(f"--- Đã nhận dữ liệu từ Yolobit (House {house_id}) lúc: {now_vn.strftime('%H:%M:%S')} ---")

        # 2. MODULE ĐIỀU KIỆN VƯỢT NGƯỠNG (Lấy tạm ngưỡng cứng, sau này lấy từ House DB)
        temp = payload.get('temp', 0)
        light = payload.get('light', 0)
        humi = payload.get('humi', 0)
        
        await _process_danger_and_rules(payload, house_id, now_vn)

        # 3. GHI LOG THIẾT BỊ (Bảng Device_log)
        # Yolobit gửi mảng `numberdevices` dạng dictionary: [{"numberdevice": 1, "status": True}, ...]
        devices_status_array = payload.get("numberdevices", [])
        
        for dev in devices_status_array:
            dev_num = dev.get("numberdevice")
            stat = dev.get("status")
            
            # Chỉ ghi log nếu trạng thái thay đổi so với lần cuối
            # key của dict last_device_status là dev_num
            if last_device_status.get(dev_num) != stat:
                
                # Format ID: ISODate + number ví dụ 2026-03-09T05:55:25.836Z1
                timestamp_str = common_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                dev_id_in_db = f"{timestamp_str}{dev_num}"
                
                device_log = {
                    "_id": dev_id_in_db,
                    "time": common_time,
                    "houseid": house_id,
                    "numberdevice": dev_num,
                    "status": stat,
                    "reason": "Yolobit tự động cập nhật hoặc User bấm"
                }
                
                await device_log_collection.update_one(
                    {"_id": dev_id_in_db},
                    {"$set": device_log},
                    upsert=True
                )
                
                last_device_status[dev_num] = stat
                print(f"--- Đã ghi Log thiết bị ID {dev_num} thay đổi thành {stat} ---")

    except Exception as e:
        print(f"Lỗi DB: {e}")
    return {"status": "Success"}

@app.get("/api/sensor-data")# ? NÀY LÀ HIỂN THỊ DASH BOARD CHỨ ÉO PHẢI FE CỦA MÌNH, FE NẰM TRONG APP.jsx
async def get_latest_data():
    """
    UC001.2 - Xem thông số môi trường
    Trả về dữ liệu môi trường mới nhất cho giao diện web.
    """
    if not latest_sensor_data:
        return {"temp": "--", "humi": "--", "light": "--", "time": "Chờ...", "connected": is_sensor_connected}
    
    data_to_send = latest_sensor_data.copy()
    if "_id" in data_to_send:
        data_to_send["_id"] = str(data_to_send["_id"])
    #! Gửi thêm trạng thái thiết bị hiện tại cho Dashboard React
    data_to_send["numberdevice"] = device_status
    # Gửi trạng thái kết nối
    data_to_send["connected"] = is_sensor_connected
    return data_to_send

# --- ENDPOINT MỚI (ĐỂ ĐIỀU KHIỂN) ---

#! Yolobit sẽ gọi GET vào đây để lấy lệnh
@app.get("/api/get-commands")
async def get_commands():
    # Trả về format mới: dict -> array of objects
    commands_array = [{"numberdevice": item[0], "status": item[1]} for item in device_status]
    return {
        "numberdevices": commands_array,
        "is_danger": is_danger_global # Push cờ nguy hiểm xuống Yolobit
    }


#! Frontend hoặc File khác gọi POST vào đây để thay đổi trạng thái
@app.post("/api/control")
async def update_control(payload: dict = Body(...)):
    global device_status
    # Nhận dữ liệu: {"commands": [[2, True], [6, 85]]}
    new_cmd = payload.get("commands")
    if new_cmd:
        device_status = new_cmd
        print(f"--- Lệnh điều khiển mới: {device_status} ---")
        return {"status": "Updated"}
    return {"status": "Error"}, 400

# --- API KỊCH BẢN (MODULE 3) ---

@app.post("/api/scenes")
async def create_scene(payload: dict = Body(...)):
    scene_name = payload.get("scene_name")
    actions = payload.get("actions")
    trigger_type = payload.get("trigger_type", "manual")
    trigger_time = payload.get("trigger_time", "")
    
    if not scene_name or not actions:
         return {"status": "Error", "message": "Missing scene_name or actions"}, 400
         
    res = await scene_manager.setup_scene(scene_name, actions, trigger_type, trigger_time)
    if res["status"] == "success":
        return res
    return res, 500

@app.post("/api/activate-scene")
async def activate_scene_endpoint(payload: dict = Body(...)):
    global device_status
    scene_name = payload.get("scene_name")
    if not scene_name:
        return {"status": "Error", "message": "Missing scene_name"}, 400
        
    actions = await scene_manager.get_scene_actions(scene_name)
    if actions is None:
        return {"status": "Error", "message": "Scene not found"}, 404
        
    device_status = apply_scene_to_status(device_status, actions)
    print(f"--- Kích hoạt kịch bản '{scene_name}'. Lệnh mới: {device_status} ---")
    return {"status": "Success", "new_commands": device_status}

@app.get("/api/scenes")
async def get_all_scenes():
    """Lấy danh sách tất cả chế độ/kịch bản đã lưu."""
    try:
        cursor = scenes_collection.find({})
        results = await cursor.to_list(length=100)
        for item in results:
            item["_id"] = str(item["_id"])
            if "updated_at" in item:
                item["updated_at"] = str(item["updated_at"])
        return results
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/scenes")
async def delete_scene(scene_name: str = Query(...)):
    """Xóa một chế độ/kịch bản theo tên."""
    try:
        result = await scenes_collection.delete_one({"scene_name": scene_name})
        if result.deleted_count > 0:
            return {"status": "Deleted", "scene_name": scene_name}
        return {"status": "Not Found"}
    except Exception as e:
        return {"error": str(e)}

# --- API PHÂN TÍCH & BIỂU ĐỒ (MODULE 1) MONGODB ---
from module.module1 import DashboardAnalytics

dashboard_analytics = DashboardAnalytics(collection, danger_collection)

@app.get("/api/sensor-comparison")
async def get_sensor_comparison():
    """Trả về dữ liệu so sánh lấy từ DB."""
    return await dashboard_analytics.get_sensor_comparison_data()

@app.get("/api/weekly-trend")
async def get_weekly_trend(period: str = Query("week")):
    """Legacy endpoint — redirect to realtime."""
    return await dashboard_analytics.get_realtime_trend_data()

@app.get("/api/realtime-trend")
async def get_realtime_trend():
    """Trả về dữ liệu xu hướng realtime từ DB."""
    return await dashboard_analytics.get_realtime_trend_data()

@app.get("/api/sensor-alerts")
async def get_sensor_alerts():
    """Trả về cảnh báo lấy từ collection nguy hiểm."""
    return await dashboard_analytics.get_sensor_alerts_data()


# --- CÁC API KHÁC GIỮ NGUYÊN ---
@app.get("/api/history-by-date")
async def get_history_by_date(date: str = Query("2026-03-09")):
    try:
        cursor = collection.find({"date": date}).sort("_id", 1)
        results = await cursor.to_list(length=100)
        for item in results:
            item["_id"] = str(item["_id"])
        return results
    except Exception as e:
        return {"error": str(e)}

# --- UC001.3 - Background Task Kiểm tra Mất kết nối ---
import asyncio

async def check_sensor_connection():
    """
    UC001.3 - Cảnh báo mất kết nối
    Kiểm tra định kỳ mỗi 5 giây. Nếu quá 30 giây không có dữ liệu, đánh dấu mất kết nối và ghi log nguy hiểm.
    """
    global is_sensor_connected, last_sensor_update_time
    while True:
        await asyncio.sleep(5)
        if last_sensor_update_time and is_sensor_connected:
            tz_vn = timezone(timedelta(hours=7))
            now_vn = datetime.now(tz_vn)
            diff = (now_vn - last_sensor_update_time).total_seconds()
            
            if diff > connection_timeout_seconds:
                is_sensor_connected = False
                print(f"--- !!! CẢNH BÁO: Mất kết nối cảm biến (quá {connection_timeout_seconds}s) !!! ---")
                
                # Ghi log nguy hiểm
                danger_data = {
                    "_id": now_vn,
                    "time": now_vn,
                    "houseid": "HS001",
                    "type": f"Mất kết nối cảm biến (Quá {connection_timeout_seconds} giây)",
                    "value": {}
                }
                try:
                    await danger_collection.insert_one(danger_data)
                    print("--- Đã lưu log mất kết nối vào database ---")
                except Exception as e:
                    print(f"Lỗi ghi log mất kết nối: {e}")

last_triggered_minute = ""

async def check_scene_timers():
    """Background task lặp mỗi 10 giây để kiểm tra và kích hoạt các scene hẹn giờ."""
    global device_status, last_triggered_minute
    while True:
        await asyncio.sleep(10)
        tz_vn = timezone(timedelta(hours=7))
        now_str = datetime.now(tz_vn).strftime("%H:%M")
        
        # Tránh trigger nhiều lần trong cùng 1 phút
        if now_str == last_triggered_minute:
            continue

        try:
            # Tìm các kịch bản có trigger_type='timer' và khớp thời gian hiện tại
            cursor = scenes_collection.find({"trigger_type": "timer", "trigger_time": now_str})
            scenes = await cursor.to_list(length=100)
            
            triggered_any = False
            for scene in scenes:
                print(f"\n[AUTO-TRIGGER] Đã đến {now_str}. Tự động kích hoạt: {scene.get('scene_name')}")
                # Dùng lại hàm helper từ module3
                device_status = apply_scene_to_status(device_status, scene.get("actions", []))
                triggered_any = True
                
            if triggered_any:
                last_triggered_minute = now_str
                print(f"--- Lệnh điều khiển mới sau Auto-Trigger: {device_status} ---")
        except Exception as e:
            print(f"Lỗi khi check_scene_timers: {e}")

@app.on_event("startup")
async def startup_event():
    # Khởi chạy các background tasks khi server bắt đầu
    asyncio.create_task(check_sensor_connection())
    asyncio.create_task(check_scene_timers())



@app.get("/api/notification-channels")
async def get_notification_channels(houseid: str = "HS001"):
    """Lấy danh sách kênh thông báo và trạng thái hiện tại."""
    data = await channel_mgr.get_channels(houseid)
    return data
 
@app.post("/api/notification-channels")
async def update_notification_channel(payload: dict = Body(...)):
    """
    Bật/tắt kênh và cập nhật thông tin liên hệ.
    Body: { "houseid": "HS001", "channel": "sms", "enabled": true, "phone": "0901234567" }
          { "houseid": "HS001", "channel": "email", "enabled": true, "address": "a@b.com" }
          { "houseid": "HS001", "channel": "app",   "enabled": true }
    """
    houseid      = payload.get("houseid", "HS001")
    channel      = payload.get("channel")
    enabled      = payload.get("enabled", True)
    contact_info = {}
    if "phone"   in payload: contact_info["phone"]   = payload["phone"]
    if "address" in payload: contact_info["address"] = payload["address"]
    if "bot_token" in payload: contact_info["bot_token"] = payload["bot_token"]  # ← thêm
    if "chat_id"   in payload: contact_info["chat_id"]   = payload["chat_id"]
    res = await channel_mgr.update_channel(houseid, channel, enabled, contact_info or None)
    if res["status"] == "error":
        return res, 400
    return res
 
 
# ====== UC002.2 - Ngưỡng an toàn ======
 
@app.get("/api/thresholds")
async def get_thresholds(houseid: str = "HS001"):
    """Lấy ngưỡng an toàn hiện tại."""
    return await threshold_mgr.get_thresholds(houseid)
 
@app.post("/api/thresholds")
async def set_threshold(payload: dict = Body(...)):
    """
    Lưu ngưỡng mới cho một cảm biến.
    Body: { "houseid": "HS001", "sensor": "temp", "min": 10, "max": 40 }
    """
    houseid = payload.get("houseid", "HS001")
    sensor  = payload.get("sensor")
    min_val = payload.get("min")
    max_val = payload.get("max")
 
    if sensor is None or min_val is None or max_val is None:
        return {"status": "error", "message": "Thiếu trường sensor, min hoặc max."}, 400
 
    res = await threshold_mgr.set_threshold(houseid, sensor, min_val, max_val)
    if res["status"] == "error":
        return res, 400
    return res
 
@app.post("/api/thresholds/reset")
async def reset_thresholds(payload: dict = Body(...)):
    """UC002.2 Alternative Flow: Đặt lại về mặc định."""
    houseid = payload.get("houseid", "HS001")
    return await threshold_mgr.reset_to_default(houseid)
 
 
# ====== UC002.3 - Kịch bản tự động hóa ======
 
@app.get("/api/automation-rules")
async def get_automation_rules(houseid: str = "HS001"):
    """Lấy danh sách kịch bản của nhà."""
    return await rule_mgr.get_rules(houseid)
 
@app.post("/api/automation-rules")
async def create_automation_rule(payload: dict = Body(...)):
    """
    Tạo kịch bản mới.
    Body:
    {
      "houseid": "HS001",
      "name": "Bật còi khi nhiệt độ cao",
      "condition": {"sensor": "temp", "op": "gt", "value": 38},
      "actions": [{"numberdevice": 7, "status": 100}],
      "enabled": true
    }
    Operators: gt, lt, gte, lte, eq
    """
    houseid   = payload.get("houseid", "HS001")
    name      = payload.get("name")
    condition = payload.get("condition")
    actions   = payload.get("actions")
    enabled   = payload.get("enabled", True)
 
    res = await rule_mgr.add_rule(houseid, name, condition, actions, enabled)
    if res["status"] == "error":
        return res, 400
    return res
 
@app.delete("/api/automation-rules")
async def delete_automation_rule(houseid: str = "HS001", name: str = ""):
    """UC002.3 Alternative Flow: Xóa kịch bản."""
    return await rule_mgr.delete_rule(houseid, name)
 
@app.patch("/api/automation-rules/toggle")
async def toggle_automation_rule(payload: dict = Body(...)):
    """Bật/tắt kịch bản mà không xóa."""
    houseid = payload.get("houseid", "HS001")
    name    = payload.get("name")
    enabled = payload.get("enabled", True)
    return await rule_mgr.toggle_rule(houseid, name, enabled)
 
 
# ====== UC002.4 - Kiểm tra thủ công (debug/test endpoint) ======
 
@app.get("/api/check-danger")
async def check_danger_now(houseid: str = "HS001"):
    """
    UC002.4: Kiểm tra tức thì xem dữ liệu mới nhất có vượt ngưỡng không.
    Dùng để test / debug mà không cần chờ Yolobit gửi.
    """
    if not latest_sensor_data:
        return {"is_danger": False, "message": "Chưa có dữ liệu cảm biến."}
 
    thresholds = await threshold_mgr.get_thresholds(houseid)
    sensor_data = {
        "temp":  latest_sensor_data.get("temp",  0),
        "humi":  latest_sensor_data.get("humi",  0),
        "light": latest_sensor_data.get("light", 0),
    }
    result = DangerChecker.check(sensor_data, thresholds)
    result["thresholds_used"] = thresholds
    result["sensor_data"]     = sensor_data
    return result
 
 
# ====== UC002.5 - Lịch sử sự cố ======
 
@app.get("/api/danger-logs")
async def get_danger_logs(houseid: str = "HS001", limit: int = 50):
    tz_vn = timezone(timedelta(hours=7))
    cursor  = danger_collection.find({"houseid": houseid}).sort("_id", -1).limit(limit)
    results = await cursor.to_list(length=limit)
    for item in results:
        item["_id"] = str(item["_id"])
        t = item.get("time")
        if t is None:
            item["time"] = "--"
        elif hasattr(t, 'tzinfo') and t.tzinfo is not None:
            item["time"] = t.astimezone(tz_vn).strftime("%Y-%m-%dT%H:%M:%S+07:00")
        else:
            item["time"] = (t + timedelta(hours=7)).strftime("%Y-%m-%dT%H:%M:%S+07:00")
    return results
 
@app.post("/api/stop-alert")
async def manual_stop_alert(payload: dict = Body(...)):
    """
    UC002.5 Alternative Flow: Người dùng nhấn 'Tắt báo động' thủ công.
    """
    global device_status, is_danger_global
    houseid = payload.get("houseid", "HS001")
    for item in device_status:
        if item[0] == 7:
            item[1] = 0
    is_danger_global = False
    print(f"[MODULE2][UC002.5] Người dùng TẮT báo động thủ công (house: {houseid})")
    return {"status": "success", "message": "Đã tắt báo động."}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)