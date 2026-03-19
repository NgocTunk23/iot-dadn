"""
Mock Server - Phục vụ dữ liệu giả từ import_logs.py để xem trước giao diện Frontend.
Không cần Docker, MongoDB. Chỉ cần chạy: python mock_server.py
"""
from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import random, math

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
WEEKLY_TREND = {
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

# ===== CẢNH BÁO & NHẬN ĐỊNH =====
SENSOR_ALERTS = [
    {
        "type": "warning",
        "title": "Nhiệt độ có xu hướng tăng",
        "message": "Nhiệt độ trung bình đã tăng 1.2°C so với tuần trước, cần theo dõi để điều chỉnh hệ thống làm mát phù hợp."
    },
    {
        "type": "info",
        "title": "Độ ẩm trong ngưỡng ổn định",
        "message": "Độ ẩm dao động từ 65-70%, nằm trong khoảng lý tưởng cho môi trường sống."
    },
    {
        "type": "success",
        "title": "Ánh sáng đạt chuẩn",
        "message": "Mức ánh sáng trung bình 840 lux, phù hợp cho hoạt động hàng ngày."
    },
]


@app.get("/api/sensor-data")
async def get_sensor_data():
    global current_index
    item = MOCK_LOGS[current_index % len(MOCK_LOGS)]
    current_index += 1
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


@app.get("/api/sensor-comparison")
async def get_sensor_comparison():
    """Trả về dữ liệu so sánh so với chu kỳ trước (mock)."""
    return {
        "temp": {"delta": 1.2, "label": "so với tuần trước"},
        "humi": {"delta": -2.1, "label": "so với tuần trước"},
        "light": {"delta": 30, "label": "so với tuần trước"},
    }


@app.get("/api/weekly-trend")
async def get_weekly_trend(period: str = Query("week")):
    """Trả về dữ liệu xu hướng theo chu kỳ."""
    if period == "month":
        # 4 tuần trong tháng
        return {
            "temp": [{"day": f"Tuần {i}", "value": round(28.0 + random.uniform(-1, 1), 1)} for i in range(1, 5)],
            "humi": [{"day": f"Tuần {i}", "value": round(65.0 + random.uniform(-3, 3), 1)} for i in range(1, 5)],
            "light": [{"day": f"Tuần {i}", "value": int(800 + random.uniform(-50, 50))} for i in range(1, 5)],
        }
    elif period == "year":
        # 12 tháng trong năm
        return {
            "temp": [{"day": f"Tháng {i}", "value": round(27.0 + math.sin(i)*2, 1)} for i in range(1, 13)],
            "humi": [{"day": f"Tháng {i}", "value": round(60.0 + math.cos(i)*5, 1)} for i in range(1, 13)],
            "light": [{"day": f"Tháng {i}", "value": int(750 + math.sin(i)*100)} for i in range(1, 13)],
        }
    else:
        # Default: week (7 ngày)
        return {
            "temp": [
                {"day": "T2", "value": 28.0}, {"day": "T3", "value": 28.5},
                {"day": "T4", "value": 29.0}, {"day": "T5", "value": 28.8},
                {"day": "T6", "value": 28.2}, {"day": "T7", "value": 27.5},
                {"day": "CN", "value": 27.8},
            ],
            "humi": [
                {"day": "T2", "value": 65.0}, {"day": "T3", "value": 68.0},
                {"day": "T4", "value": 67.0}, {"day": "T5", "value": 69.0},
                {"day": "T6", "value": 71.0}, {"day": "T7", "value": 66.0},
                {"day": "CN", "value": 65.5},
            ],
            "light": [
                {"day": "T2", "value": 810}, {"day": "T3", "value": 860},
                {"day": "T4", "value": 850}, {"day": "T5", "value": 880},
                {"day": "T6", "value": 870}, {"day": "T7", "value": 840},
                {"day": "CN", "value": 820},
            ],
        }


@app.get("/api/sensor-alerts")
async def get_sensor_alerts():
    """Trả về cảnh báo & nhận định dựa trên xu hướng dữ liệu."""
    return SENSOR_ALERTS


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


if __name__ == "__main__":
    print("=" * 50)
    print("  MOCK SERVER - Dữ liệu giả cho Frontend")
    print("  http://localhost:5000")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=5000)
