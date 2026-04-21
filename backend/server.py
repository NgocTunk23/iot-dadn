from fastapi import FastAPI, Body, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
import os
import uvicorn
from contextlib import asynccontextmanager  # <--- Thêm dòng này

# Import các Module
from module.module2 import (
    ThresholdManager, NotificationChannelManager, AutomationRuleManager,
    DangerChecker, AlertDispatcher, init_module2,
    process_danger_and_rules, router as module2_router, sync_device_state
)
from module.module3 import SceneManager, init_module3, router as module3_router
import module.module3 as module3
from module.module1 import DashboardAnalytics, init_module1, router as module1_router
from module.module4 import init_module4, router as module4_router

# TẠO HÀM LIFESPAN MỚI (Chèn vào TRƯỚC chỗ app = FastAPI)
@asynccontextmanager
async def lifespan(app: FastAPI):
    import module.module1 as module1_mod
    module1_mod.start_monitoring()
    from module.module2 import initialize_default_house 
    await initialize_default_house(db.House)
    
    print("\n--- DANH SÁCH API ROUTES ĐÃ ĐĂNG KÝ ---")
    for route in app.routes:
        print(f"DEBUG_ROUTE: {route.path} (Methods: {route.methods})")
    print("---------------------------------------\n")
    
    yield  # Bắt buộc phải có chữ yield này
    
    print("Server đang tắt...")


# SỬA LẠI CÁCH KHỞI TẠO APP (Thay cho app = FastAPI() cũ)
app = FastAPI(lifespan=lifespan)

# 1. Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Kết nối MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.iot_database

# 3. Khởi tạo các Module (Thứ tự quan trọng)
threshold_mgr = ThresholdManager(db.House, db.Logupdate)
channel_mgr = NotificationChannelManager(db.House)
rule_mgr = AutomationRuleManager(db.Scenario, threshold_mgr)
alert_dispatcher = AlertDispatcher(db.Danger_log, channel_mgr)

scene_manager = SceneManager(db.Mode)
init_module3(scene_manager, db.House)

dashboard_analytics = DashboardAnalytics(db.Sensor_history, db.Danger_log)
init_module1(dashboard_analytics)

init_module2(app, threshold_mgr, channel_mgr, rule_mgr, alert_dispatcher, db.Danger_log)
init_module4(db.Sensor_history, db.Danger_log, db.Device_log, db.Logupdate, threshold_mgr=threshold_mgr)

# 4. Include Routers (Sử dụng prefix /api TẬP TRUNG tại đây)
app.include_router(module3_router, prefix="/api")
app.include_router(module1_router) # module1_router đã có sẵn prefix /api bên trong file module1.py
app.include_router(module2_router)
app.include_router(module4_router)

# Biến toàn cục & State
last_device_status = {} 
app.state.rule_mgr = rule_mgr

# --- ENDPOINT NHẬN DỮ LIỆU TỪ YOLOBIT ---

@app.post("/update")
async def handle_data(payload: dict = Body(...)):
    global last_device_status
    now_utc = datetime.now(timezone.utc)
    now_vn = now_utc + timedelta(hours=7)
    house_id = payload.get("houseid", "HS001")
    
    await sync_device_state(db.House, house_id, payload.get("numberdevices", []))
    payload["time"] = now_utc
    payload["date"] = now_vn.strftime("%Y-%m-%d")
    
    house_config = await db.House.find_one({"_id.houseid": house_id})
    dev_map = {d.get("numberdevice"): d for d in house_config.get("numberdevices", [])} if house_config else {}

    sensor_entry = payload.copy()
    sensor_entry["_id"] = f"{now_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')}_{house_id}" 
    
    if "numberdevices" in sensor_entry:
        for d in sensor_entry["numberdevices"]:
            num = d.get("numberdevice")
            if "type" not in d: d["type"] = dev_map.get(num, {}).get("type", "unknown")

    try:
        await db.Sensor_history.insert_one(sensor_entry)
        from module.module1 import update_latest_sensor_data, update_sensor_connection
        update_latest_sensor_data(payload)
        update_sensor_connection(now_utc)

        is_danger, new_status = await process_danger_and_rules(app, payload, house_id)
        module3.device_status_map[house_id] = new_status

        if house_id not in last_device_status: last_device_status[house_id] = {}
        active_rule = rule_mgr.get_active_rule_name(house_id)
        for dev in payload.get("numberdevices", []):
            num, stat = dev.get("numberdevice"), dev.get("status")
            if last_device_status[house_id].get(num) != stat:
                from module.module3 import log_device_state
                reason = f"Tự động (Kịch bản: {active_rule})" if active_rule else "Thiết bị phản hồi trạng thái"
                await log_device_state(house_id, num, dev_map.get(num, {}).get("type", "unknown"), stat, reason=reason)
                last_device_status[house_id][num] = stat
    except Exception as e: print(f"[SERVER] Lỗi: {e}")
    return {"status": "Success"}

@app.get("/api/get-commands")
async def get_commands(houseid: str = Query("HS001")):
    current_status = module3.device_status_map.get(houseid, [])
    return {
        "numberdevices": [{"numberdevice": item[0], "status": item[1]} for item in current_status],
        "is_danger": getattr(app.state, "is_danger_global", False)
    }

@app.get("/api/house-info")
async def get_house_info(houseid: str, username: str):
    print(f"\n[DEBUG] Đang tra cứu nhà với houseid={houseid}, username={username}") # <-- Thêm dòng này
    try:
        house_config = await db.House.find_one({
            "_id.houseid": houseid,
            "_id.username": username
        })
        print(f"[DEBUG] Kết quả tìm được: {house_config}") # <-- Thêm dòng này
        
        if house_config:
            return house_config
        return {"error": "Không tìm thấy thông tin nhà cho user này."}
    except Exception as e:
        print(f"[API LỖI] /api/house-info: {e}")
        return {"error": "Lỗi truy vấn Database"}
    
# @app.on_event("startup")
# async def startup_event():
#     import module.module1 as module1_mod
#     module1_mod.start_monitoring()
#     from module.module2 import initialize_default_house 
#     await initialize_default_house(db.House)
    
#     print("\n--- DANH SÁCH API ROUTES ĐÃ ĐĂNG KÝ ---")
#     for route in app.routes:
#         print(f"DEBUG_ROUTE: {route.path} (Methods: {route.methods})")
#     print("---------------------------------------\n")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
