from fastapi import FastAPI, Body, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
import os
import uvicorn
from module.module3 import SceneManager, init_module3, router as module3_router, device_status as shared_device_status
import module.module3 as module3
from module.module1 import DashboardAnalytics, init_module1, router as module1_router

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
danger_collection = db.Danger_log   # Bảng log nguy hiểm
device_log_collection = db.Device_log # Bảng log thiết bị
scenes_collection = db.Mode        # Bảng kịch bản
scene_manager = SceneManager(scenes_collection)
init_module3(scene_manager)

# --- BIẾN TOÀN CỤC ---
latest_sensor_data = {}
# Biến phụ để so sánh sự thay đổi log
last_device_status = {item[0]: item[1] for item in shared_device_status}
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
    now_vn = datetime.now(tz_vn).replace(tzinfo=None)#!
    
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
        
        thresh_temp_max = 35
        thresh_light_max = 90
        
        if temp > thresh_temp_max or light > thresh_light_max:
            is_danger_global = True
            danger_data = {
                "_id": common_time,
                "time": common_time,
                "houseid": house_id,
                "type": "Vượt ngưỡng an toàn",
                "value": {"temp": temp, "humi": humi, "light": light}
            }
            await danger_collection.insert_one(danger_data)
            print("--- !!! ĐÃ GHI LOG NGUY HIỂM !!! ---")
        else:
            is_danger_global = False

        # 3. GHI LOG THIẾT BỊ (Bảng Device_log)
        # Yolobit gửi mảng `numberdevices` dạng dictionary: [{"numberdevice": 1, "status": True}, ...]
        devices_status_array = payload.get("numberdevices", [])
        
        for dev in devices_status_array:
            dev_num = dev.get("numberdevice")
            stat = dev.get("status")
            
            # Chỉ ghi log nếu trạng thái thay đổi so với lần cuối
            # key của dict last_device_status là dev_num
            if last_device_status.get(dev_num) != stat:
                
                # Kiểm tra xem đây có phải là chống trộm tự động bật thiết bị 1 không?
                # (Thiết bị 1 bật nhưng Backend không hề ra lệnh bật trước đó)
                cmd_dict = {item[0]: item[1] for item in module3.device_status}
                if dev_num == 1 and stat == True and cmd_dict.get(1) == False:
                    reason_str = "do hệ thống tự động bật (chống trộm)"
                else:
                    reason_str = "do người dùng bật thủ công"

                # Format ID: ISODate + number ví dụ 2026-03-09T05:55:25.836Z1
                timestamp_str = common_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                dev_id_in_db = f"{timestamp_str}{dev_num}"
                
                device_log = {
                    "_id": dev_id_in_db,
                    "time": common_time,
                    "houseid": house_id,
                    "numberdevice": dev_num,
                    "status": stat,
                    "reason": reason_str
                }
                
                await device_log_collection.update_one(
                    {"_id": dev_id_in_db},
                    {"$set": device_log},
                    upsert=True
                )
                
                # Đồng bộ lại Backend nếu là chống trộm tự động bật đèn 1
                if reason_str == "do hệ thống tự động bật (chống trộm)":
                    for i, item in enumerate(module3.device_status):
                        if item[0] == 1:
                            module3.device_status[i][1] = True
                            break

                last_device_status[dev_num] = stat
                print(f"--- Đã ghi Log thiết bị ID {dev_num} ({reason_str}) ---")

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
    data_to_send["numberdevice"] = module3.device_status
    # Gửi trạng thái kết nối
    data_to_send["connected"] = is_sensor_connected
    return data_to_send

# --- ENDPOINT MỚI (ĐỂ ĐIỀU KHIỂN) ---

#! Yolobit sẽ gọi GET vào đây để lấy lệnh
@app.get("/api/get-commands")
async def get_commands():
    # Trả về format mới: dict -> array of objects
    commands_array = [{"numberdevice": item[0], "status": item[1]} for item in module3.device_status]
    return {
        "numberdevices": commands_array,
        "is_danger": is_danger_global # Push cờ nguy hiểm xuống Yolobit
    }


#! Frontend hoặc File khác gọi POST vào đây để thay đổi trạng thái
@app.post("/api/control")
async def update_control(payload: dict = Body(...)):
    # Nhận dữ liệu: {"commands": [[2, True], [6, 85]]}
    new_cmd = payload.get("commands")
    if new_cmd:
        module3.device_status = new_cmd
        print(f"--- Lệnh điều khiển mới: {module3.device_status} ---")
        return {"status": "Updated"}
    return {"status": "Error"}, 400

# --- INCLUDE ROUTER MODULE 3 ---
app.include_router(module3_router)

# --- PHÂN TÍCH & BIỂU ĐỒ (MODULE 1) ---
dashboard_analytics = DashboardAnalytics(collection, danger_collection)
init_module1(dashboard_analytics)
app.include_router(module1_router)


# --- CÁC API KHÁC GIỮ NGUYÊN ---

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

                except Exception as e:
                    print(f"Lỗi ghi log mất kết nối: {e}")

@app.on_event("startup")
async def startup_event():
    # Khởi chạy các background tasks khi server bắt đầu
    asyncio.create_task(check_sensor_connection())

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)