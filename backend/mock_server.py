"""
Mock Server - Phục vụ dữ liệu giả từ import_logs.py để xem trước giao diện Frontend.
Không cần Docker, MongoDB. Chỉ cần chạy: python mock_server.py
"""
from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import random, math
import time
from module.module1 import get_sensor_comparison_data, get_realtime_trend_data, get_sensor_alerts_data, record_sensor_reading

MOCK_START_TIME = time.time()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# === DỮ LIỆU GIẢ TỪ import_logs.py (light đổi sang lux = giá trị gốc * 10) ===
MOCK_LOGS = [
    {'humi': 64.6, 'light': 760, 'temp': 29.5, 'time': '11:30:24'},
    {'humi': 64.0, 'light': 760, 'temp': 29.5, 'time': '11:30:29'},
    {'humi': 63.9, 'light': 760, 'temp': 29.5, 'time': '11:30:35'},
    {'humi': 63.9, 'light': 740, 'temp': 29.5, 'time': '11:30:41'},
    {'humi': 64.1, 'light': 720, 'temp': 29.4, 'time': '11:30:47'},
    {'humi': 64.2, 'light': 730, 'temp': 29.4, 'time': '11:30:50'},
    {'humi': 64.2, 'light': 730, 'temp': 29.4, 'time': '11:30:56'},
    {'humi': 64.2, 'light': 740, 'temp': 29.4, 'time': '11:31:02'},
    {'humi': 64.2, 'light': 740, 'temp': 29.3, 'time': '11:31:07'},
    {'humi': 64.3, 'light': 650, 'temp': 29.3, 'time': '11:31:13'},
    {'humi': 64.4, 'light': 750, 'temp': 29.3, 'time': '11:31:19'},
    {'humi': 64.4, 'light': 730, 'temp': 29.3, 'time': '11:31:23'},
]

# Thêm nhiều điểm dữ liệu cho biểu đồ
EXTENDED_LOGS = list(MOCK_LOGS)
for i in range(30):
    base_temp = 28.5 + 1.5 * math.sin(i * 0.2)
    base_humi = 64 + 3 * math.cos(i * 0.15)
    base_light = 700 + 100 * math.sin(i * 0.25)
    m = 31 + (i * 2) // 60
    s = 24 + (i * 6) % 60
    EXTENDED_LOGS.append({
        'humi': round(base_humi + random.uniform(-0.5, 0.5), 1),
        'light': max(0, round(base_light + random.uniform(-20, 20))),
        'temp': round(base_temp + random.uniform(-0.3, 0.3), 1),
        'time': f'{11:02d}:{m:02d}:{s:02d}',
    })

# Trạng thái thiết bị
device_status = [
    [1, True], [2, False], [3, True],
    [4, False], [5, True], [6, 90], [7, 80],
]

# Kịch bản giả
mock_scenes = [
    {
        "_id": "scene001", "scene_name": "Chế độ Ban ngày",
        "trigger_type": "timer", "trigger_time": "06:00",
        "actions": [
            {"device_id": 1, "value": False}, {"device_id": 2, "value": False},
            {"device_id": 3, "value": False}, {"device_id": 4, "value": False},
            {"device_id": 5, "value": False}, {"device_id": 6, "value": 90},
            {"device_id": 7, "value": 80},
        ],
        "updated_at": "2026-03-18T10:00:00",
    },
    {
        "_id": "scene002", "scene_name": "Chế độ Ban đêm",
        "trigger_type": "timer", "trigger_time": "22:00",
        "actions": [
            {"device_id": 1, "value": True}, {"device_id": 2, "value": True},
            {"device_id": 3, "value": True}, {"device_id": 4, "value": False},
            {"device_id": 5, "value": False}, {"device_id": 6, "value": 0},
            {"device_id": 7, "value": 0},
        ],
        "updated_at": "2026-03-18T10:05:00",
    },
    {
        "_id": "scene003", "scene_name": "Chế độ Tiết kiệm",
        "trigger_type": "manual", "trigger_time": "",
        "actions": [
            {"device_id": 1, "value": True}, {"device_id": 2, "value": False},
            {"device_id": 3, "value": False}, {"device_id": 4, "value": False},
            {"device_id": 5, "value": False}, {"device_id": 6, "value": 0},
            {"device_id": 7, "value": 70},
        ],
        "updated_at": "2026-03-18T10:10:00",
    },
]

current_index = 0

# ===== DỮ LIỆU XU HƯỚNG TUẦN (giả) =====
# Đã được chuyển sang module1.py

# ===== CẢNH BÁO & NHẬN ĐỊNH =====
# Đã được chuyển sang module1.py


@app.get("/api/sensor-data")
async def get_sensor_data():
    global current_index
    item = MOCK_LOGS[current_index % len(MOCK_LOGS)]
    current_index += 1
    # Ghi nhận vào bộ nhớ tạm cho comparison & realtime trend
    record_sensor_reading(item["temp"], item["humi"], item["light"])
    return {
        "temp": item["temp"],
        "humi": item["humi"],
        "light": item["light"],
        "time": item["time"],
        "date": "2026-03-06",
        "connected": True,
        "numberdevice": device_status,
        "houseid": "HS001",
    }


@app.get("/api/history-by-date")
async def get_history_by_date(date: str = Query("2026-03-06")):
    results = []
    for item in EXTENDED_LOGS:
        results.append({
            "_id": f"{date}T{item['time']}",
            "temp": item["temp"],
            "humi": item["humi"],
            "light": item["light"],
            "time": item["time"],
            "date": date,
        })
    return results


# ===== BIẾN ĐỂ BẠN TỰ ĐỔI KHI TEST TRÊN WEB =====
# Sửa SIMULATE_RUN_MINUTES để giả lập việc server đã chạy bao lâu (tính bằng phút)
# Ví dụ: 3 (mới chạy 3 phút -> TH3), 6 (đã chạy 6 phút -> TH2), 1500 (đã chạy qua ngày -> TH1)
# Đặt là None để tính thời gian thực trôi qua kể từ lúc nãy bạn gõ lệnh chạy python mock_server.py
SIMULATE_RUN_MINUTES = 50


def get_elapsed_minutes():
    if SIMULATE_RUN_MINUTES is not None:
        return SIMULATE_RUN_MINUTES
    return (time.time() - MOCK_START_TIME) / 60.0

@app.get("/api/sensor-comparison")
async def get_sensor_comparison():
    """Trả về dữ liệu tổng quan cấu hình mô phỏng theo thời gian."""
    elapsed = get_elapsed_minutes()
    
    if elapsed < 5:
        # TH3: Hệ thống mới bật, hoàn toàn chưa đủ dữ liệu
        return {
            "temp": {"delta": 0, "label": "Chưa đủ dữ liệu"},
            "humi": {"delta": 0, "label": "Chưa đủ dữ liệu"},
            "light": {"delta": 0, "label": "Chưa đủ dữ liệu"},
        }
    elif elapsed < 1440:
        # TH2: Không đủ trung bình ngày, quay lại lấy 5 phút trước
        return {
            "temp": {"delta": 2.5, "label": "So với 5 phút trước"},
            "humi": {"delta": -1.5, "label": "So với 5 phút trước"},
            "light": {"delta": 15, "label": "So với 5 phút trước"},
        }
    else:
        # TH1: Có đủ dữ liệu, so sánh trung bình ngày
        return {
            "temp": {"delta": 1.2, "label": "So với trung bình ngày"},
            "humi": {"delta": -2.1, "label": "So với trung bình ngày"},
            "light": {"delta": 30, "label": "So với trung bình ngày"},
        }

@app.get("/api/realtime-trend")
async def get_realtime_trend():
    """Trả về dữ liệu biểu đồ khớp với thời gian chạy thực tế theo mô tả."""
    elapsed = get_elapsed_minutes()
    intervals = [30, 25, 20, 15, 10, 5, 0]
    labels = ["30", "25", "20", "15", "10", "5", "Hiện tại"]
    
    res_temp, res_humi, res_light = [], [], []
    
    for idx, mins in enumerate(intervals):
        if mins > elapsed:
            # Nếu thời điểm trên đồ thị dài hơn thời gian đã chạy máy -> Value = 0
            res_temp.append({"label": labels[idx], "value": 0})
            res_humi.append({"label": labels[idx], "value": 0})
            res_light.append({"label": labels[idx], "value": 0})
        else:
            # Có dữ liệu giả
            base_temp = 28.5 + 1.2 * math.sin(idx * 0.12)
            base_humi = 65.0 + 3.0 * math.cos(idx * 0.1)
            base_light = 750 + 80 * math.sin(idx * 0.15)
            
            res_temp.append({"label": labels[idx], "value": round(base_temp + random.uniform(-0.5, 0.5), 1)})
            res_humi.append({"label": labels[idx], "value": round(base_humi + random.uniform(-1, 1), 1)})
            res_light.append({"label": labels[idx], "value": max(0, int(base_light + random.uniform(-10, 10)))})
            
    return {
        "temp": res_temp,
        "humi": res_humi,
        "light": res_light
    }

@app.get("/api/weekly-trend")
async def get_weekly_trend(period: str = Query("week")):
    """Legacy endpoint — redirect to realtime."""
    return get_realtime_trend_data()


@app.get("/api/realtime-trend")
async def get_realtime_trend():
    """Trả về dữ liệu xu hướng real-time (30 phút qua)."""
    return get_realtime_trend_data()


@app.get("/api/sensor-alerts")
async def get_sensor_alerts():
    """Trả về cảnh báo & nhận định dựa trên xu hướng dữ liệu."""
    return get_sensor_alerts_data()


@app.get("/api/scenes")
async def get_scenes():
    return mock_scenes


@app.post("/api/scenes")
async def create_scene(payload: dict = Body(...)):
    new_scene = {
        "_id": f"scene{len(mock_scenes) + 1:03d}",
        "scene_name": payload.get("scene_name", "Chế độ mới"),
        "trigger_type": payload.get("trigger_type", "manual"),
        "trigger_time": payload.get("trigger_time", ""),
        "actions": payload.get("actions", []),
        "updated_at": datetime.now().isoformat(),
    }
    mock_scenes.append(new_scene)
    return {"status": "success", "scene_name": new_scene["scene_name"]}


@app.delete("/api/scenes")
async def delete_scene(scene_name: str = Query(...)):
    global mock_scenes
    mock_scenes = [s for s in mock_scenes if s["scene_name"] != scene_name]
    return {"status": "Deleted", "scene_name": scene_name}


@app.post("/api/activate-scene")
async def activate_scene(payload: dict = Body(...)):
    global device_status
    scene_name = payload.get("scene_name")
    for scene in mock_scenes:
        if scene["scene_name"] == scene_name:
            for act in scene["actions"]:
                idx = act["device_id"] - 1
                if 0 <= idx < len(device_status):
                    device_status[idx][1] = act["value"]
            return {"status": "Success", "new_commands": device_status}
    return {"status": "Error", "message": "Scene not found"}


@app.post("/api/control")
async def control_device(payload: dict = Body(...)):
    global device_status
    new_cmd = payload.get("commands")
    if new_cmd:
        device_status = new_cmd
        return {"status": "Updated"}
    return {"status": "Error"}


@app.post("/update")
async def handle_data(payload: dict = Body(...)):
    return {"status": "Success"}

import asyncio

last_triggered_minute = ""

async def check_scene_timers():
    """Background task lặp mỗi 10 giây để kiểm tra và kích hoạt các scene hẹn giờ."""
    global device_status, last_triggered_minute
    while True:
        await asyncio.sleep(10)
        now_str = datetime.now().strftime("%H:%M")
        
        # Tránh trigger nhiều lần trong cùng 1 phút
        if now_str == last_triggered_minute:
            continue

        triggered_any = False
        for scene in mock_scenes:
            if scene.get("trigger_type") == "timer" and scene.get("trigger_time") == now_str:
                print(f"\n[AUTO-TRIGGER] Đã đến {now_str}. Tự động kích hoạt: {scene['scene_name']}")
                for act in scene.get("actions", []):
                    idx = act["device_id"] - 1
                    if 0 <= idx < len(device_status):
                        device_status[idx][1] = act["value"]
                triggered_any = True
                
        if triggered_any:
            last_triggered_minute = now_str


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_scene_timers())


if __name__ == "__main__":
    print("=" * 50)
    print("  MOCK SERVER - Dữ liệu giả cho Frontend")
    print("  http://localhost:5000")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=5000)
