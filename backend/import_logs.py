import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# 1. Danh sách dữ liệu mẫu ngày 06/03/2026
logs = [
    {'humi': 64.6, 'light': 76, 'temp': 29.5, 'time': '11:30:24'},
    {'humi': 64.0, 'light': 76, 'temp': 29.5, 'time': '11:30:29'},
    {'humi': 63.9, 'light': 76, 'temp': 29.5, 'time': '11:30:35'},
    {'humi': 63.9, 'light': 74, 'temp': 29.5, 'time': '11:30:41'},
    {'humi': 64.1, 'light': 72, 'temp': 29.4, 'time': '11:30:47'},
    {'humi': 64.2, 'light': 73, 'temp': 29.4, 'time': '11:30:50'},
    {'humi': 64.2, 'light': 73, 'temp': 29.4, 'time': '11:30:56'},
    {'humi': 64.2, 'light': 74, 'temp': 29.4, 'time': '11:31:02'},
    {'humi': 64.2, 'light': 74, 'temp': 29.3, 'time': '11:31:07'},
    {'humi': 64.3, 'light': 65, 'temp': 29.3, 'time': '11:31:13'},
    {'humi': 64.4, 'light': 75, 'temp': 29.3, 'time': '11:31:19'},
    {'humi': 64.4, 'light': 73, 'temp': 29.3, 'time': '11:31:23'}
]

async def import_data():
    # --- BƯỚC 1: KẾT NỐI MONGODB ---
    # Chạy từ WSL nên dùng localhost:27017
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.iot_database
    collection = db.sensor_history
    
    # --- BƯỚC 2: RESET DỮ LIỆU CŨ ---
    # Xóa sạch bản ghi cũ của ngày 06/03 để nạp lại cấu trúc mới
    await collection.delete_many({"date": "2026-03-06"})
    
    fixed_date = "2026-03-06"
    print(f"--- Bắt đầu nạp dữ liệu cho ngày {fixed_date} (Khóa chính là ID thời gian) ---")

    # --- BƯỚC 3: VÒNG LẶP NẠP DỮ LIỆU ---
    for item in logs:
        # Tạo đối tượng datetime từ ngày cố định và giờ trong log
        dt_obj = datetime.strptime(f"{fixed_date} {item['time']}", "%Y-%m-%d %H:%M:%S")
        
        # Cấu trúc Document tối giản: _id đóng vai trò timestamp luôn
        entry = {
            "_id": dt_obj,       # Khóa chính (Primary Key)
            "temp": item['temp'],
            "humi": item['humi'],
            "light": item['light'],
            "date": fixed_date,   # Dùng để lọc dữ liệu theo ngày nhanh hơn
            "time": item['time']  # Giữ lại chuỗi giờ để hiển thị giao diện
        }
        
        try:
            await collection.insert_one(entry)
            print(f"Thành công: {item['time']}")
        except Exception as e:
            # Nếu trùng _id (cùng 1 giây), MongoDB sẽ tự động chặn
            print(f"Bỏ qua (Trùng ID): {item['time']}")

    print("\n--- HOÀN TẤT: Dữ liệu đã nằm trong MongoDB (khóa chính _id là datetime) ---")

if __name__ == "__main__":
    asyncio.run(import_data())