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
from module.module4 import LogManager

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
danger_collection = db.danger_logs  # Bảng log nguy hiểm
device_log_collection = db.device_logs  # Bảng log thiết bị
scenes_collection = db.scenes  # Bảng kịch bản
scene_manager = SceneManager(scenes_collection)

# Module 4 - Logging & Analysis
log_collection = db.logs
config_collection = db.config

log_manager = LogManager(log_collection, config_collection)

# --- BIẾN TOÀN CỤC ---
latest_sensor_data = {}
#! MẶC ĐỊNH LỆNH BE: 7 thiết bị (Đèn 1-5, Servo 6, Quạt 7)
device_status = [
    [1, False],
    [2, False],
    [3, False],
    [4, False],
    [5, False],
    [6, 0],
    [7, 0],
]
# Biến phụ để so sánh sự thay đổi log
last_device_status = {}
# Lưu trạng thái nguy hiểm để báo về Yolobit
is_danger_global = False

# Biến UC001.3
last_sensor_update_time = None
is_sensor_connected = False
connection_timeout_seconds = 30


# --- ENDPOINT NHẬN DỮ LIỆU TỪ YOLOBIT ---
@app.post("/update")
async def handle_data(payload: dict = Body(...)):
    global latest_sensor_data, last_device_status, is_danger_global
    tz_vn = timezone(timedelta(hours=7))
    now_vn = datetime.now(tz_vn)

    # Payload từ Yolobit main3.py có dạng:
    # { houseid: "HS001", temp: 30, humi: 60, light: 50, numberdevices: [{numberdevice: 1, status: True}, ...] }
    house_id = payload.get("houseid", "HS001")

    common_time = now_vn
    payload["time"] = common_time  # Dùng làm PK / _id
    payload["date"] = now_vn.strftime("%Y-%m-%d")  # Phục vụ Lọc API

    # 1. Ghi vào bảng sensor_history
    sensor_entry = payload.copy()
    sensor_entry["_id"] = common_time  # MongoDB PK

    try:
        await collection.insert_one(sensor_entry)
        latest_sensor_data = payload

        # UC001.3: Cập nhật connection status
        global last_sensor_update_time, is_sensor_connected
        last_sensor_update_time = now_vn
        if not is_sensor_connected:
            is_sensor_connected = True
            print("--- Cảm biến đã KẾT NỐI lại ---")

        print(
            f"--- Đã nhận dữ liệu từ Yolobit (House {house_id}) lúc: {now_vn.strftime('%H:%M:%S')} ---"
        )

        # 2. MODULE ĐIỀU KIỆN VƯỢT NGƯỠNG (Lấy tạm ngưỡng cứng, sau này lấy từ House DB)
        temp = payload.get("temp", 0)
        light = payload.get("light", 0)
        humi = payload.get("humi", 0)

        thresh_temp_max = 35
        thresh_light_max = 90

        if temp > thresh_temp_max or light > thresh_light_max:
            is_danger_global = True
            danger_data = {
                "_id": common_time,
                "time": common_time,
                "houseid": house_id,
                "type": "Vượt ngưỡng an toàn",
                "value": {"temp": temp, "humi": humi, "light": light},
            }
            await danger_collection.insert_one(danger_data)
            print("--- !!! ĐÃ GHI LOG NGUY HIỂM !!! ---")
            # [MODULE 4] UC004.6 - Ghi log WARNING khi vượt ngưỡng
            await log_manager.log_event(
                device_id="sensor",
                level="WARNING",
                message="Sensor value exceeded threshold",
                value={"temp": temp, "humi": humi, "light": light},
            )
        else:
            is_danger_global = False

        # [MODULE 4] UC004.6 - Ghi log INFO mỗi lần nhận sensor data
        await log_manager.log_event(
            device_id="sensor",
            level="INFO",
            message="Sensor data received",
            value={"temp": temp, "humi": humi, "light": light},
        )

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
                timestamp_str = common_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                dev_id_in_db = f"{timestamp_str}{dev_num}"

                device_log = {
                    "_id": dev_id_in_db,
                    "time": common_time,
                    "houseid": house_id,
                    "numberdevice": dev_num,
                    "status": stat,
                    "reason": "Yolobit tự động cập nhật hoặc User bấm",
                }

                await device_log_collection.update_one(
                    {"_id": dev_id_in_db}, {"$set": device_log}, upsert=True
                )

                last_device_status[dev_num] = stat
                print(f"--- Đã ghi Log thiết bị ID {dev_num} thay đổi thành {stat} ---")
                # [MODULE 4] UC004.6 - Ghi log khi thiết bị thay đổi trạng thái
                await log_manager.log_event(
                    device_id=dev_num,
                    level="INFO",
                    message="Device status changed",
                    value=stat,
                )

    except Exception as e:
        print(f"Lỗi DB: {e}")
    return {"status": "Success"}


@app.get(
    "/api/sensor-data"
)  # ? NÀY LÀ HIỂN THỊ DASH BOARD CHỨ ÉO PHẢI FE CỦA MÌNH, FE NẰM TRONG APP.jsx
async def get_latest_data():
    """
    UC001.2 - Xem thông số môi trường
    Trả về dữ liệu môi trường mới nhất cho giao diện web.
    """
    if not latest_sensor_data:
        return {
            "temp": "--",
            "humi": "--",
            "light": "--",
            "time": "Chờ...",
            "connected": is_sensor_connected,
        }

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
    commands_array = [
        {"numberdevice": item[0], "status": item[1]} for item in device_status
    ]
    return {
        "numberdevices": commands_array,
        "is_danger": is_danger_global,  # Push cờ nguy hiểm xuống Yolobit
    }


#! Frontend hoặc File khác gọi POST vào đây để thay đổi trạng thái
@app.post("/api/control")
async def update_control(payload: dict = Body(...)):
    global device_status
    # Nhận dữ liệu: {"commands": [[2, True], [6, 85]]}
    new_cmd = payload.get("commands")
    if new_cmd:
        device_status = new_cmd
        # [MODULE 4] UC004.6 - Ghi log khi user điều khiển thiết bị
        await log_manager.log_event(
            device_id="system",
            level="INFO",
            message="User control devices",
            value=new_cmd,
        )
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

    res = await scene_manager.setup_scene(
        scene_name, actions, trigger_type, trigger_time
    )
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
    # [MODULE 4] UC004.6 - Ghi log khi kích hoạt kịch bản
    await log_manager.log_event(
        device_id="scene",
        level="INFO",
        message=f"Scene activated: {scene_name}",
        value=actions,
    )
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

<<<<<<< HEAD

# --- API PHÂN TÍCH & BIỂU ĐỒ (MODULE 1) MOCK CHO FRONTEND ---
import random, math
=======
# --- API PHÂN TÍCH & BIỂU ĐỒ (MODULE 1) MONGODB ---
from module.module1 import DashboardAnalytics

dashboard_analytics = DashboardAnalytics(collection, danger_collection)
>>>>>>> 26962896db25a6eae4099ad3399e6aaea624c840


@app.get("/api/sensor-comparison")
async def get_sensor_comparison():
    """Trả về dữ liệu so sánh lấy từ DB."""
    return await dashboard_analytics.get_sensor_comparison_data()


@app.get("/api/weekly-trend")
async def get_weekly_trend(period: str = Query("week")):
<<<<<<< HEAD
    """Trả về dữ liệu xu hướng theo chu kỳ (mock tạm thời để ghép FE)."""
    if period == "month":
        return {
            "temp": [
                {"day": f"Tuần {i}", "value": round(28.0 + random.uniform(-1, 1), 1)}
                for i in range(1, 5)
            ],
            "humi": [
                {"day": f"Tuần {i}", "value": round(65.0 + random.uniform(-3, 3), 1)}
                for i in range(1, 5)
            ],
            "light": [
                {"day": f"Tuần {i}", "value": int(800 + random.uniform(-50, 50))}
                for i in range(1, 5)
            ],
        }
    elif period == "year":
        return {
            "temp": [
                {"day": f"Tháng {i}", "value": round(27.0 + math.sin(i) * 2, 1)}
                for i in range(1, 13)
            ],
            "humi": [
                {"day": f"Tháng {i}", "value": round(60.0 + math.cos(i) * 5, 1)}
                for i in range(1, 13)
            ],
            "light": [
                {"day": f"Tháng {i}", "value": int(750 + math.sin(i) * 100)}
                for i in range(1, 13)
            ],
        }
    else:
        return {
            "temp": [
                {"day": "T2", "value": 28.0},
                {"day": "T3", "value": 28.5},
                {"day": "T4", "value": 29.0},
                {"day": "T5", "value": 28.8},
                {"day": "T6", "value": 28.2},
                {"day": "T7", "value": 27.5},
                {"day": "CN", "value": 27.8},
            ],
            "humi": [
                {"day": "T2", "value": 65.0},
                {"day": "T3", "value": 68.0},
                {"day": "T4", "value": 67.0},
                {"day": "T5", "value": 69.0},
                {"day": "T6", "value": 71.0},
                {"day": "T7", "value": 66.0},
                {"day": "CN", "value": 65.5},
            ],
            "light": [
                {"day": "T2", "value": 810},
                {"day": "T3", "value": 860},
                {"day": "T4", "value": 850},
                {"day": "T5", "value": 880},
                {"day": "T6", "value": 870},
                {"day": "T7", "value": 840},
                {"day": "CN", "value": 820},
            ],
        }
=======
    """Legacy endpoint — redirect to realtime."""
    return await dashboard_analytics.get_realtime_trend_data()

@app.get("/api/realtime-trend")
async def get_realtime_trend():
    """Trả về dữ liệu xu hướng realtime từ DB."""
    return await dashboard_analytics.get_realtime_trend_data()
>>>>>>> 26962896db25a6eae4099ad3399e6aaea624c840


@app.get("/api/sensor-alerts")
async def get_sensor_alerts():
<<<<<<< HEAD
    """Trả về cảnh báo & nhận định dựa trên xu hướng (mock tạm thời để ghép FE)."""
    return [
        {
            "type": "warning",
            "title": "Nhiệt độ có xu hướng tăng",
            "message": "Nhiệt độ trung bình đã tăng 1.2°C so với tuần trước, cần theo dõi để điều chỉnh hệ thống làm mát phù hợp.",
        },
        {
            "type": "info",
            "title": "Độ ẩm trong ngưỡng ổn định",
            "message": "Độ ẩm dao động từ 65-70%, nằm trong khoảng lý tưởng cho môi trường sống.",
        },
        {
            "type": "success",
            "title": "Ánh sáng đạt chuẩn",
            "message": "Mức ánh sáng trung bình 840 lux, phù hợp cho hoạt động hàng ngày.",
        },
    ]
=======
    """Trả về cảnh báo lấy từ collection nguy hiểm."""
    return await dashboard_analytics.get_sensor_alerts_data()
>>>>>>> 26962896db25a6eae4099ad3399e6aaea624c840


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
                print(
                    f"--- !!! CẢNH BÁO: Mất kết nối cảm biến (quá {connection_timeout_seconds}s) !!! ---"
                )

                # Ghi log nguy hiểm
                danger_data = {
                    "_id": now_vn,
                    "time": now_vn,
                    "houseid": "HS001",
                    "type": f"Mất kết nối cảm biến (Quá {connection_timeout_seconds} giây)",
                    "value": {},
                }
                try:
                    await danger_collection.insert_one(danger_data)
                    print("--- Đã lưu log mất kết nối vào database ---")
                except Exception as e:
                    print(f"Lỗi ghi log mất kết nối: {e}")
                # [MODULE 4] UC004.6 - Ghi log ERROR khi mất kết nối cảm biến
                try:
                    await log_manager.log_event(
                        device_id="sensor",
                        level="ERROR",
                        message=f"Sensor disconnected (no data for {connection_timeout_seconds}s)",
                        value={},
                    )
                except Exception as e:
                    print(f"Lỗi ghi Module 4 log mất kết nối: {e}")


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


# ================================================================
# [MODULE 4] API LOGGING & ANALYSIS - UC004
# ================================================================


@app.get("/api/logs")
async def get_logs(
    level: str = Query(
        None, description="Lọc theo level: DEBUG | INFO | WARNING | ERROR"
    ),
    device_id: str = Query(None, description="Lọc theo thiết bị"),
    limit: int = Query(100, description="Số dòng tối đa trả về"),
):
    """UC004.5 - Xem lịch sử log thô, có hỗ trợ filter."""
    return await log_manager.get_logs(level=level, device_id=device_id, limit=limit)


@app.get("/api/reports")
async def get_reports(
    period: str = Query("day", description="Chu kỳ: day | week | month"),
):
    """UC004.3 + UC004.4 - Xem báo cáo phân tích theo chu kỳ."""
    return await log_manager.get_report(period=period)


@app.put("/api/config/log-level")
async def set_log_level(payload: dict = Body(...)):
    """
    UC004.2 - Cấu hình mức log tối thiểu.
    Body: { "level": "WARNING" }
    Hợp lệ: DEBUG | INFO | WARNING | ERROR
    """
    level = payload.get("level", "INFO")
    return await log_manager.set_log_level(level)


@app.put("/api/config/strategy")
async def set_strategy(payload: dict = Body(...)):
    """
    UC004.1 - Cấu hình chiến lược phân tích.
    Body: { "strategy": "trend" }
    Hợp lệ: frequency | average | trend
    """
    strategy = payload.get("strategy", "frequency")
    return await log_manager.set_strategy(strategy)


@app.get("/api/config")
async def get_config():
    """Xem cấu hình log hiện tại (log_level + strategy)."""
    return await log_manager.get_config()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
