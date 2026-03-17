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

# --- BIẾN TOÀN CỤC ---
latest_sensor_data = {}
#! MỚI: Biến này lưu lệnh chờ Yolobit lấy về. Mặc định Đèn 2 tắt, Thiết bị 6 mức 0, các file backend thay đổi con số này.
device_status = [[2, False], [6, 0]] 
# Biến phụ để kiểm tra xem trạng thái có thay đổi không mới ghi Log thiết bị
last_device_status = None

# Biến UC001.3
last_sensor_update_time = None
is_sensor_connected = False
connection_timeout_seconds = 30

# --- ENDPOINT CŨ CỦA BẠN (CÓ CHỈNH SỬA NHẸ ĐỂ LƯU LOG THIẾT BỊ) ---
@app.post("/update")
async def handle_data(payload: dict = Body(...)):
    global latest_sensor_data, last_device_status
    tz_vn = timezone(timedelta(hours=7))
    now_vn = datetime.now(tz_vn)
    
    # ID chung cho tất cả các bảng
    common_id = now_vn 
    
    payload["_id"] = common_id
    payload["date"] = now_vn.strftime("%Y-%m-%d")
    payload["time"] = now_vn.strftime("%H:%M:%S")
    #! Lưu thêm trạng thái thiết bị lúc đó vào DB
    payload["numberdevice"] = device_status 
    
    try:
        # 1. Ghi vào bảng sensor_history như bình thường
        await collection.insert_one(payload.copy())
        latest_sensor_data = payload
        
        # UC001.3: Cập nhật thời gian nhận dữ liệu cuối cùng
        last_sensor_update_time = now_vn
        if not is_sensor_connected:
            is_sensor_connected = True
            print("--- Cảm biến đã KẾT NỐI lại ---")
            
        print(f"--- Đã nhận dữ liệu từ Yolobit: {payload['time']} ---")

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!    TỰ VIẾT THÀNH HÀM Ở MODULE 2 và chỉ include dô đây gọi và chạy
        # MODULE ĐIỀU KIỆN VƯỢT NGƯỠNG (Ghi log nguy hiểm)
        if payload.get('temp', 0) > 35 or payload.get('light', 0) > 90:
            danger_data = {
                "_id": common_id, # ID y chang bảng sensor
                "reason": "Nhiệt độ hoặc ánh sáng vượt ngưỡng an toàn",
                "value": {"temp": payload.get('temp'), "light": payload.get('light')}
            }
            await danger_collection.insert_one(danger_data)
            print("--- !!! ĐÃ GHI LOG NGUY HIỂM !!! ---")
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # --- LOG THIẾT BỊ: Chỉ chạy khi có thay đổi trạng thái ---
        if device_status != last_device_status:
            for dev in device_status:
                # Format ID theo kiểu: ISODate + number (Ví dụ: 2026-03-09T...Z2)
                # Dùng strftime để lấy chuỗi thời gian chuẩn ISO
                timestamp_str = common_id.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                dev_id_in_db = f"{timestamp_str}{dev[0]}"
                
                device_log = {
                    "_id": dev_id_in_db,
                    "timestamp": common_id,
                    "device_number": dev[0],
                    "status": dev[1]
                }
                # Upsert giúp cập nhật nếu trùng hoặc thêm mới nếu chưa có
                await device_log_collection.update_one(
                    {"_id": dev_id_in_db},
                    {"$set": device_log},
                    upsert=True
                )
            
            # Cập nhật trạng thái cuối cùng
            last_device_status = [list(d) for d in device_status]
            print(f"--- Đã lưu Log thiết bị mới: {device_status} ---")

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

#! Yolobit sẽ gọi GET vào đây để lấy lệnh [[2, True], [6, 80]]
@app.get("/api/get-commands")
async def get_commands():
    return {"numberdevice": device_status}


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
    if not scene_name or not actions:
         return {"status": "Error", "message": "Missing scene_name or actions"}, 400
         
    res = await scene_manager.setup_scene(scene_name, actions)
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
                    "reason": f"Mất kết nối cảm biến (Quá {connection_timeout_seconds} giây)",
                    "value": {},
                    "log_type": "Báo cáo nguy hiểm"
                }
                try:
                    await danger_collection.insert_one(danger_data)
                    print("--- Đã lưu log mất kết nối vào database ---")
                except Exception as e:
                    print(f"Lỗi ghi log mất kết nối: {e}")

@app.on_event("startup")
async def startup_event():
    # Khởi chạy background task khi server bắt đầu
    asyncio.create_task(check_sensor_connection())

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)