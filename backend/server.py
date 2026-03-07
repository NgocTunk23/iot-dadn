from fastapi import FastAPI, Body, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, time as dt_time
import os
import uvicorn

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

latest_sensor_data = {}

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    if not latest_sensor_data:
        return "<h1>Đang chờ dữ liệu từ Yolobit...</h1>"
    
    html_content = f"""
    <html>
        <head>
            <title>IoT Dashboard - Toon</title>
            <meta http-equiv="refresh" content="2">
            <style>
                body {{ font-family: sans-serif; text-align: center; padding: 50px; background: #f4f4f4; }}
                .card {{ background: white; padding: 20px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 300px; }}
                .val {{ font-size: 2em; color: #007bff; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Dữ liệu Cảm Biến</h1>
                <p>Nhiệt độ: <span class="val">{latest_sensor_data.get('temp', '--')} °C</span></p>
                <p>Độ ẩm: <span class="val">{latest_sensor_data.get('humi', '--')} %</span></p>
                <p>Ánh sáng: <span class="val">{latest_sensor_data.get('light', '--')} %</span></p>
                <hr>
                <p>Cập nhật cuối: {latest_sensor_data.get('time', '--')}</p>
            </div>
        </body>
    </html>
    """
    return html_content

@app.post("/update")
async def handle_data(payload: dict = Body(...)):
    global latest_sensor_data
    now = datetime.now()
    
    # Cấu trúc đồng nhất với script import
    payload["_id"] = now  # Khóa chính là thời gian hiện tại
    payload["date"] = now.strftime("%Y-%m-%d")
    payload["time"] = now.strftime("%H:%M:%S")
    
    try:
        await collection.insert_one(payload.copy())
        latest_sensor_data = payload
        print(f"--- Đã lưu DB: {payload['time']} ---")
    except Exception as e:
        print(f"Lỗi DB: {e}")
    return {"status": "Success"}

# API lấy dữ liệu theo ngày - ĐÃ SỬA LỖI TRẢ VỀ RỖNG []
@app.get("/api/history-by-date")
async def get_history_by_date(date: str = Query("2026-03-06")):
    try:
        # Tìm theo trường 'date' (dạng string) và sắp xếp theo '_id' (thời gian)
        cursor = collection.find({"date": date}).sort("_id", 1)
        results = await cursor.to_list(length=100)

        for item in results:
            # RẤT QUAN TRỌNG: Chuyển _id (datetime) sang string để JSON không bị lỗi rỗng
            item["_id"] = str(item["_id"])
        return results
    except Exception as e:
        return {"error": str(e)}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)