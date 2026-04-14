from fastapi import FastAPI, Body, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
import os
import uvicorn
from module.module2 import (
    ThresholdManager,
    NotificationChannelManager,
    AutomationRuleManager,
    DangerChecker,
    AlertDispatcher,
    init_module2,
    process_danger_and_rules,
    router as module2_router,
)
from module.module3 import (
    SceneManager,
    init_module3,
    router as module3_router,
    device_status as shared_device_status,
)
import module.module3 as module3
from module.module1 import DashboardAnalytics, init_module1, router as module1_router
from module.module4 import init_module4, router as module4_router

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
collection = db.Sensor_history
danger_collection = db.Danger_log  # Bảng log nguy hiểm
device_log_collection = db.Device_log  # Bảng log thiết bị
system_update_collection = db.System_update_log  # Bảng log cập nhật hệ thống
scenes_collection = db.Mode  # Bảng kịch bản
scene_manager = SceneManager(scenes_collection)
init_module3(scene_manager)
automation_rules_col = db.Scenario  # Ánh xạ sang bảng Scenario theo ERD
house_col = db.House  # THÊM MỚI: đọc emailtowarning, teletowarning
logupdate_collection = db.Logupdate
threshold_mgr = ThresholdManager(house_col, logupdate_collection)
channel_mgr = NotificationChannelManager(house_col)
rule_mgr = AutomationRuleManager(automation_rules_col, threshold_mgr)
alert_dispatcher = AlertDispatcher(danger_collection, channel_mgr)

init_module4(
    collection,
    danger_collection,
    device_log_collection,
    logupdate_collection,  # ← db.Logupdate
    threshold_mgr=threshold_mgr,
)

# Biến toàn cục từ module được chia sẻ
# Biến phụ để so sánh sự thay đổi log
last_device_status = {item[0]: item[1] for item in shared_device_status}
# Lưu trạng thái nguy hiểm để báo về Yolobit
is_danger_global = False

init_module2(
    app, threshold_mgr, channel_mgr, rule_mgr, alert_dispatcher, danger_collection
)
app.state.device_status = shared_device_status
app.state.is_danger_global = False
app.state.latest_sensor_data = {}
app.state.last_pir_state = False
app.include_router(module2_router)

# --- ENDPOINT NHẬN DỮ LIỆU TỪ YOLOBIT ---


@app.post("/update")
async def handle_data(payload: dict = Body(...)):
    global last_device_status, is_danger_global
    tz_vn = timezone(timedelta(hours=7))
    now_vn = datetime.now(tz_vn).replace(tzinfo=None)  #!

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

        import module.module1 as module1_mod

        module1_mod.update_latest_sensor_data(payload)
        app.state.latest_sensor_data = payload
        # UC001.3: Cập nhật connection status (Ủy quyền cho module1)
        import module.module1 as module1_mod

        if module1_mod.update_sensor_connection(now_vn):
            print("--- Cảm biến đã KẾT NỐI lại ---")

        print(
            f"--- Đã nhận dữ liệu từ Yolobit (House {house_id}) lúc: {now_vn.strftime('%H:%M:%S')} ---"
        )

        # 2. MODULE ĐIỀU KIỆN VƯỢT NGƯỠNG (Lấy tạm ngưỡng cứng, sau này lấy từ House DB)
        temp = payload.get("temp", 0)
        light = payload.get("light", 0)
        humi = payload.get("humi", 0)

        is_danger_val, new_status_val = await process_danger_and_rules(
            app, payload, house_id
        )
        is_danger_global = is_danger_val
        module3.device_status = new_status_val

        # 3.1 GHI LOG THIẾT BỊ DO NGƯỜI DÙNG BẤM CÔNG TẮC HOẶC TỰ ĐỘNG
        devices_status_array = payload.get("numberdevices", [])

        # Lấy tên kịch bản tự động đang chạy (nếu có)
        active_rule = app.state.rule_mgr.get_active_rule_name(house_id)

        for dev in devices_status_array:
            dev_num = dev.get("numberdevice")
            stat = dev.get("status")

            if last_device_status.get(dev_num) != stat:
                # Phân biệt lý do linh hoạt hơn
                if dev_num == 1:
                    reason_str = "Người dùng cấu hình chống trộm"
                else:
                    if active_rule:
                        reason_str = f"Tự động (Theo kịch bản: {active_rule})"
                    else:
                        reason_str = "Người dùng điều khiển thủ công"

                timestamp_str = common_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                dev_id_in_db = f"{timestamp_str}{dev_num}"
                old_status = last_device_status.get(dev_num)

                device_log = {
                    "_id": dev_id_in_db,
                    "time": common_time,
                    "houseid": house_id,
                    "numberdevice": dev_num,
                    "old_status": old_status,
                    "new_status": stat,
                    "reason": reason_str,
                }
                await device_log_collection.update_one(
                    {"_id": dev_id_in_db}, {"$set": device_log}, upsert=True
                )
                last_device_status[dev_num] = stat
                print(f"--- Đã ghi Log thiết bị ID {dev_num} ({reason_str}) ---")

        # 3.2 GHI LOG KHI CẢM BIẾN PIR PHÁT HIỆN CÓ NGƯỜI (TÍN HIỆU NGẦM)
        pir_active = payload.get("pir_active")
        if pir_active is not None:
            if app.state.last_pir_state != pir_active:
                if pir_active == True:
                    reason_str = "Hệ thống phát hiện có người (Đèn sáng)"
                else:
                    reason_str = "Hệ thống ngừng phát hiện người (Đèn tắt tạm thời)"

                timestamp_str = common_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                dev_id_in_db = f"{timestamp_str}PIR"

                device_log = {
                    "_id": dev_id_in_db,
                    "time": common_time,
                    "houseid": house_id,
                    "numberdevice": 1,  # Gắn mác ID 1 để hiện lên bảng log trên UI
                    "old_status": app.state.last_pir_state,
                    "new_status": pir_active,
                    "reason": reason_str,
                }
                await device_log_collection.update_one(
                    {"_id": dev_id_in_db}, {"$set": device_log}, upsert=True
                )
                app.state.last_pir_state = pir_active
                print(f"--- Đã ghi Log PIR: {reason_str} ---")

    except Exception as e:
        print(f"Lỗi DB: {e}")
    return {"status": "Success"}


# --- ENDPOINT MỚI (ĐỂ ĐIỀU KHIỂN) ---


#! Yolobit sẽ gọi GET vào đây để lấy lệnh
@app.get("/api/get-commands")
async def get_commands():
    # Trả về format mới: dict -> array of objects
    commands_array = [
        {"numberdevice": item[0], "status": item[1]} for item in module3.device_status
    ]
    return {
        "numberdevices": commands_array,
        "is_danger": is_danger_global,  # Push cờ nguy hiểm xuống Yolobit
    }


#! Frontend hoặc File khác gọi POST vào đây để thay đổi trạng thái
@app.post("/api/control")
async def update_control(payload: dict = Body(...)):
    # Nhận dữ liệu: {"commands": [[2, True], [6, 85]]}
    new_cmd = payload.get("commands")
    if new_cmd:
        module3.device_status = new_cmd
        app.state.device_status = new_cmd
        print(f"--- Lệnh điều khiển mới: {module3.device_status} ---")
        return {"status": "Updated"}
    return {"status": "Error"}, 400


# --- INCLUDE ROUTER MODULE 3 ---
app.include_router(module3_router)

# --- PHÂN TÍCH & BIỂU ĐỒ (MODULE 1) ---
dashboard_analytics = DashboardAnalytics(collection, danger_collection)
init_module1(dashboard_analytics)
app.include_router(module1_router)

app.include_router(module4_router)


@app.on_event("startup")
async def startup_event():
    # Khởi chạy các background tasks khi server bắt đầu
    import module.module1 as module1_mod

    module1_mod.start_monitoring()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
