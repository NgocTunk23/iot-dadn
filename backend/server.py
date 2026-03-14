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
# danger_collection = db.danger_logs   # Bảng log nguy hiểm
# device_log_collection = db.device_logs # Bảng log thiết bị

# # --- BIẾN TOÀN CỤC ---
# latest_sensor_data = {}
# #! MỚI: Biến này lưu lệnh chờ Yolobit lấy về. Mặc định Đèn 2 tắt, Thiết bị 6 mức 0, các file backend thay đổi con số này.
# device_status = [[2, False], [6, 0]] 
# # Biến phụ để kiểm tra xem trạng thái có thay đổi không mới ghi Log thiết bị
# last_device_status = None

# # --- ENDPOINT CŨ CỦA BẠN (CÓ CHỈNH SỬA NHẸ ĐỂ LƯU LOG THIẾT BỊ) ---
# @app.post("/update")
# async def handle_data(payload: dict = Body(...)):
#     global latest_sensor_data, last_device_status
#     tz_vn = timezone(timedelta(hours=7))
#     now_vn = datetime.now(tz_vn)
    
#     # ID chung cho tất cả các bảng
#     common_id = now_vn 
    
#     payload["_id"] = common_id
#     payload["date"] = now_vn.strftime("%Y-%m-%d")
#     payload["time"] = now_vn.strftime("%H:%M:%S")
#     #! Lưu thêm trạng thái thiết bị lúc đó vào DB
#     payload["numberdevice"] = device_status 
    
#     try:
#         # 1. Ghi vào bảng sensor_history như bình thường
#         await collection.insert_one(payload.copy())
#         latest_sensor_data = payload
#         print(f"--- Đã nhận dữ liệu từ Yolobit: {payload['time']} ---")

#         #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!    TỰ VIẾT THÀNH HÀM Ở MODULE 2 và chỉ include dô đây gọi và chạy
#         # MODULE ĐIỀU KIỆN VƯỢT NGƯỠNG (Ghi log nguy hiểm)
#         if payload.get('temp', 0) > 35 or payload.get('light', 0) > 90:
#             danger_data = {
#                 "_id": common_id, # ID y chang bảng sensor
#                 "reason": "Nhiệt độ hoặc ánh sáng vượt ngưỡng an toàn",
#                 "value": {"temp": payload.get('temp'), "light": payload.get('light')}
#             }
#             await danger_collection.insert_one(danger_data)
#             print("--- !!! ĐÃ GHI LOG NGUY HIỂM !!! ---")
#         #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

#         # --- LOG THIẾT BỊ: Chỉ chạy khi có thay đổi trạng thái ---
#         if device_status != last_device_status:
#             for dev in device_status:
#                 # Format ID theo kiểu: ISODate + number (Ví dụ: 2026-03-09T...Z2)
#                 # Dùng strftime để lấy chuỗi thời gian chuẩn ISO
#                 timestamp_str = common_id.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
#                 dev_id_in_db = f"{timestamp_str}{dev[0]}"
                
#                 device_log = {
#                     "_id": dev_id_in_db,
#                     "timestamp": common_id,
#                     "device_number": dev[0],
#                     "status": dev[1]
#                 }
#                 # Upsert giúp cập nhật nếu trùng hoặc thêm mới nếu chưa có
#                 await device_log_collection.update_one(
#                     {"_id": dev_id_in_db},
#                     {"$set": device_log},
#                     upsert=True
#                 )
            
#             # Cập nhật trạng thái cuối cùng
#             last_device_status = [list(d) for d in device_status]
#             print(f"--- Đã lưu Log thiết bị mới: {device_status} ---")

#     except Exception as e:
#         print(f"Lỗi DB: {e}")
#     return {"status": "Success"}

# @app.get("/api/sensor-data")# ? NÀY LÀ HIỂN THỊ DASH BOARD CHỨ ÉO PHẢI FE CỦA MÌNH, FE NẰM TRONG APP.jsx
# async def get_latest_data():
#     if not latest_sensor_data:
#         return {"temp": "--", "humi": "--", "light": "--", "time": "Chờ..."}
    
#     data_to_send = latest_sensor_data.copy()
#     if "_id" in data_to_send:
#         data_to_send["_id"] = str(data_to_send["_id"])
#     #! Gửi thêm trạng thái thiết bị hiện tại cho Dashboard React
#     data_to_send["numberdevice"] = device_status
#     return data_to_send

# # --- ENDPOINT MỚI (ĐỂ ĐIỀU KHIỂN) ---

# #! Yolobit sẽ gọi GET vào đây để lấy lệnh [[2, True], [6, 80]]
# @app.get("/api/get-commands")
# async def get_commands():
#     return {"numberdevice": device_status}


# #! Frontend hoặc File khác gọi POST vào đây để thay đổi trạng thái
# @app.post("/api/control")
# async def update_control(payload: dict = Body(...)):
#     global device_status
#     # Nhận dữ liệu: {"commands": [[2, True], [6, 85]]}
#     new_cmd = payload.get("commands")
#     if new_cmd:
#         device_status = new_cmd
#         print(f"--- Lệnh điều khiển mới: {device_status} ---")
#         return {"status": "Updated"}
#     return {"status": "Error"}, 400


# # --- CÁC API KHÁC GIỮ NGUYÊN ---
# @app.get("/api/history-by-date")
# async def get_history_by_date(date: str = Query("2026-03-09")):
#     try:
#         cursor = collection.find({"date": date}).sort("_id", 1)
#         results = await cursor.to_list(length=100)
#         for item in results:
#             item["_id"] = str(item["_id"])
#         return results
#     except Exception as e:
#         return {"error": str(e)}

# if __name__ == '__main__':
#     uvicorn.run(app, host='0.0.0.0', port=5000)




from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
import os
import uvicorn
import copy

app = FastAPI()

# --- 1. CẤU HÌNH CORS CHO FRONTEND REACT ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. KẾT NỐI MONGODB ---
MONGO_URL = os.getenv("MONGO_URL", "mongodb://db:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.iot_database

# Ánh xạ chuẩn theo sơ đồ UML IoT
collection = db.sensor_history
danger_collection = db.danger_log  
device_log_collection = db.device_log 
house_collection = db.house 

# --- 3. BIẾN TOÀN CỤC ---
latest_sensor_data = {}

# Mảng này lưu "Lệnh điều khiển" từ Frontend gửi xuống để Yolobit tải về
# Khởi tạo mặc định 6 thiết bị (giống với trạng thái ban đầu của Yolobit)
device_status = [
    {"numberdevice": 1, "status": False}, # LED ngoài cửa
    {"numberdevice": 2, "status": False}, # LED trong nhà
    {"numberdevice": 3, "status": False}, # LED trong nhà
    {"numberdevice": 4, "status": False}, # LED trong nhà
    {"numberdevice": 5, "status": 0},     # Góc quay Servo
    {"numberdevice": 6, "status": 0}      # Tốc độ quạt
]

# Mảng này lưu "Trạng thái thực tế" từ Yolobit báo cáo lên để ghi Log
last_device_status = None


# ==========================================
# API: NHẬN DỮ LIỆU TỪ YOLOBIT
# ==========================================
@app.post("/update")
async def handle_data(payload: dict = Body(...)):
    global latest_sensor_data, last_device_status
    tz_vn = timezone(timedelta(hours=7))
    now_vn = datetime.now(tz_vn)
    
    houseid = str(payload.get("houseid", "HS_UNKNOWN"))
    
    current_temp = float(payload.get("temp", 0.0))
    current_humi = float(payload.get("humi", 0.0))
    current_light = float(payload.get("light", 0.0))

    # ! QUAN TRỌNG: Lấy mảng trạng thái THỰC TẾ do phần cứng báo cáo
    actual_devices_from_yolobit = payload.get("numberdevices", [])

    # --- 1. LƯU BẢNG SENSOR_HISTORY ---
    document = {
        "_id": {
            "time": now_vn,
            "houseid": houseid
        },
        "temp": current_temp,       
        "humi": current_humi,       
        "light": current_light,     
        "numberdevices": actual_devices_from_yolobit  # Ghi chính xác trạng thái thực của mạch
    }
    
    try:
        await collection.insert_one(document)
        latest_sensor_data = document
        print(f"--- Đã nhận Data từ {houseid} lúc {now_vn.strftime('%H:%M:%S')} ---")

        # --- 2. LƯU BẢNG DANGER_LOG ---
        temp_max_limit = 35.0
        light_max_limit = 90.0
        
        house_info = await house_collection.find_one({"_id": houseid})
        if house_info:
            temp_max_limit = float(house_info.get("tempmax", 35.0))
            light_max_limit = float(house_info.get("lightmax", 90.0))

        if current_temp > temp_max_limit or current_light > light_max_limit:
            danger_data = {
                "_id": {  
                    "time": now_vn,
                    "houseid": houseid
                },
                "type": "Cảnh báo vượt ngưỡng cài đặt", 
                "value": [{  
                    "temp": current_temp,
                    "humi": current_humi,
                    "light": current_light
                }]
            }
            await danger_collection.insert_one(danger_data)
            print(f"--- !!! BÁO ĐỘNG TẠI {houseid} !!! ---")

        # --- 3. LƯU BẢNG DEVICE_LOG ---
        # So sánh trạng thái THỰC TẾ gửi lên với lần trước đó để ghi Log
        if actual_devices_from_yolobit and actual_devices_from_yolobit != last_device_status:
            for dev in actual_devices_from_yolobit:
                dev_num = dev.get("numberdevice")
                dev_stat = dev.get("status")
                
                device_log = {
                    "_id": {  
                        "time": now_vn,
                        "houseid": houseid,
                        "numberdevice": dev_num
                    },
                    "status": dev_stat,
                    "reason": "Phần cứng cập nhật trạng thái" 
                }
                await device_log_collection.update_one(
                    {"_id": device_log["_id"]},
                    {"$set": device_log},
                    upsert=True
                )
            
            last_device_status = copy.deepcopy(actual_devices_from_yolobit)
            print(f"--- Đã lưu Log thiết bị thực tế cho {houseid} ---")

    except Exception as e:
        print(f"Lỗi DB: {e}")
        
    return {"status": "Success"}


# ==========================================
# CÁC API CHO FRONTEND (REACT)
# ==========================================
@app.get("/api/sensor-data")
async def get_latest_data():
    if not latest_sensor_data:
        return {"temp": "--", "humi": "--", "light": "--", "houseid": "Chờ..."}
    
    data_to_send = copy.deepcopy(latest_sensor_data)
    
    # Bóc tách PK kép để React đọc không bị lỗi
    if "_id" in data_to_send and isinstance(data_to_send["_id"], dict):
        data_to_send["time"] = data_to_send["_id"]["time"].strftime("%Y-%m-%d %H:%M:%S")
        data_to_send["houseid"] = data_to_send["_id"]["houseid"]
        
    data_to_send["_id"] = str(data_to_send["_id"])
    return data_to_send

@app.get("/api/history")
async def get_history(houseid: str = Query("HS001"), limit: int = Query(100)):
    try:
        cursor = collection.find({"_id.houseid": houseid}).sort("_id.time", -1)
        results = await cursor.to_list(length=limit)
        
        for item in results:
            if isinstance(item.get("_id"), dict):
                item["time"] = item["_id"]["time"].strftime("%Y-%m-%d %H:%M:%S")
                item["houseid"] = item["_id"]["houseid"]
            item["_id"] = str(item["_id"])
            
        return results
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/get-commands")
async def get_commands():
    # API cung cấp lệnh điều khiển cho Yolobit
    return {"numberdevices": device_status}

@app.post("/api/control")
async def update_control(payload: dict = Body(...)):
    global device_status
    new_cmd = payload.get("commands")
    if new_cmd:
        device_status = new_cmd
        print(f"--- Frontend gửi lệnh: {device_status} ---")
        return {"status": "Updated", "current": device_status}
    return {"status": "Error", "message": "Thiếu dữ liệu commands"}, 400

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)