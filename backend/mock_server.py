"""
Mock Server - Phục vụ dữ liệu giả từ import_logs.py để xem trước giao diện Frontend.
Không cần Docker, MongoDB. Chỉ cần chạy: python mock_server.py

Bao gồm tất cả endpoints từ:
  - Module 1: sensor-data, sensor-comparison, realtime-trend, weekly-trend, sensor-alerts, history-by-date
  - Module 2: thresholds, notification-channels, automation-rules, danger-logs, check-danger, stop-alert
  - Module 3: scenes (CRUD), activate-scene, deactivate-scene, get-commands
  - Server:   /update, /api/control
"""
from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
import uvicorn
import random, math
import time
import asyncio
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

# ============================================================
# TRẠNG THÁI THIẾT BỊ (dùng chung cho tất cả module)
# 7 thiết bị: Đèn 1-5, Servo 6, Quạt 7
# ============================================================
device_status = [
    [1, True], [2, False], [3, True],
    [4, False], [5, True], [6, 90], [7, 80],
]

# Cờ nguy hiểm
is_danger_global = False

# ============================================================
# DỮ LIỆU GIẢ MODULE 2 (in-memory)
# ============================================================

# --- Ngưỡng an toàn ---
DEFAULT_THRESHOLDS = {
    "temp":  {"min": 0,   "max": 40},
    "humi":  {"min": 20,  "max": 80},
    "light": {"min": 0,   "max": 90},
}
mock_thresholds = {"HS001": dict(DEFAULT_THRESHOLDS)}

# --- Kênh thông báo ---
mock_channels = {
    "HS001": {
        "email":    {"enabled": False, "address": ""},
        "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
        "app":      {"enabled": True},
    }
}

# --- Kịch bản tự động (Automation Rules / Scenario) ---
mock_automation_rules = []

# --- Danger logs ---
mock_danger_logs = [
    {
        "_id": "2026-03-18T10:15:00",
        "time": "2026-03-18T10:15:00+07:00",
        "houseid": "HS001",
        "type": "Vượt ngưỡng an toàn",
        "value": {"temp": 42, "humi": 65, "light": 50},
        "violations": [{"sensor": "temp", "value": 42, "threshold": "max", "limit": 40}],
    },
    {
        "_id": "2026-03-17T22:30:00",
        "time": "2026-03-17T22:30:00+07:00",
        "houseid": "HS001",
        "type": "Mất kết nối cảm biến (Quá 30 giây)",
        "value": {},
    },
]

# ============================================================
# DỮ LIỆU GIẢ MODULE 3 (Kịch bản / Scenes)
# ============================================================
mock_scenes = [
    {
        "_id": "scene001",
        "modeid": "scene001",
        "houseid": "HS001",
        "name": "Chế độ Ban ngày",
        "action": [
            {"numberdevice": 1, "status": False}, {"numberdevice": 2, "status": False},
            {"numberdevice": 3, "status": False}, {"numberdevice": 4, "status": False},
            {"numberdevice": 5, "status": False}, {"numberdevice": 6, "status": 90},
            {"numberdevice": 7, "status": 80},
        ],
        "isactive": True,
        "createdat": "2026-03-18T10:00:00",
    },
    {
        "_id": "scene002",
        "modeid": "scene002",
        "houseid": "HS001",
        "name": "Chế độ Ban đêm",
        "action": [
            {"numberdevice": 1, "status": True}, {"numberdevice": 2, "status": True},
            {"numberdevice": 3, "status": True}, {"numberdevice": 4, "status": False},
            {"numberdevice": 5, "status": False}, {"numberdevice": 6, "status": 0},
            {"numberdevice": 7, "status": 0},
        ],
        "isactive": True,
        "createdat": "2026-03-18T10:05:00",
    },
    {
        "_id": "scene003",
        "modeid": "scene003",
        "houseid": "HS001",
        "name": "Chế độ Tiết kiệm",
        "action": [
            {"numberdevice": 1, "status": True}, {"numberdevice": 2, "status": False},
            {"numberdevice": 3, "status": False}, {"numberdevice": 4, "status": False},
            {"numberdevice": 5, "status": False}, {"numberdevice": 6, "status": 0},
            {"numberdevice": 7, "status": 70},
        ],
        "isactive": True,
        "createdat": "2026-03-18T10:10:00",
    },
]

current_index = 0

# ===== BIẾN ĐỂ BẠN TỰ ĐỔI KHI TEST TRÊN WEB =====
# Sửa SIMULATE_RUN_MINUTES để giả lập việc server đã chạy bao lâu (tính bằng phút)
# Ví dụ: 3 (mới chạy 3 phút -> TH3), 6 (đã chạy 6 phút -> TH2), 1500 (đã chạy qua ngày -> TH1)
# Đặt là None để tính thời gian thực trôi qua kể từ lúc nãy bạn gõ lệnh chạy python mock_server.py
SIMULATE_RUN_MINUTES = 50


def get_elapsed_minutes():
    if SIMULATE_RUN_MINUTES is not None:
        return SIMULATE_RUN_MINUTES
    return (time.time() - MOCK_START_TIME) / 60.0


# ============================================================
#                    MODULE 1 ENDPOINTS
# ============================================================

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


@app.get("/api/sensor-alerts")
async def get_sensor_alerts():
    """Trả về cảnh báo & nhận định dựa trên xu hướng dữ liệu."""
    return get_sensor_alerts_data()


# ============================================================
#                    MODULE 2 ENDPOINTS
# ============================================================

# --- Ngưỡng an toàn ---
@app.get("/api/thresholds")
async def get_thresholds(houseid: str = "HS001"):
    """Lấy ngưỡng an toàn hiện tại."""
    return mock_thresholds.get(houseid, dict(DEFAULT_THRESHOLDS))


@app.post("/api/thresholds")
async def set_threshold(payload: dict = Body(...)):
    """Cập nhật ngưỡng an toàn cho 1 cảm biến."""
    houseid = payload.get("houseid", "HS001")
    sensor = payload.get("sensor")
    min_val = payload.get("min")
    max_val = payload.get("max")

    if sensor is None or min_val is None or max_val is None:
        return JSONResponse(status_code=400, content={
            "status": "error", "message": "Thiếu sensor, min hoặc max."
        })

    PHYSICAL_LIMITS = {"temp": (-50, 500), "humi": (0, 100), "light": (0, 100)}
    if sensor not in PHYSICAL_LIMITS:
        return JSONResponse(status_code=400, content={
            "status": "error", "message": f"Cảm biến '{sensor}' không tồn tại."
        })

    try:
        min_val, max_val = float(min_val), float(max_val)
    except (TypeError, ValueError):
        return JSONResponse(status_code=400, content={
            "status": "error", "message": "Giá trị ngưỡng phải là số."
        })

    if min_val > max_val:
        return JSONResponse(status_code=400, content={
            "status": "error", "message": "Lỗi logic: Min không được lớn hơn Max."
        })

    if houseid not in mock_thresholds:
        mock_thresholds[houseid] = dict(DEFAULT_THRESHOLDS)
    mock_thresholds[houseid][sensor] = {"min": min_val, "max": max_val}

    print(f"[MOCK] Cập nhật ngưỡng {sensor}: min={min_val}, max={max_val}")
    return {"status": "success", "message": "Cập nhật ngưỡng thành công."}


@app.post("/api/thresholds/reset")
async def reset_thresholds(payload: dict = Body(...)):
    """Reset ngưỡng về mặc định."""
    houseid = payload.get("houseid", "HS001")
    mock_thresholds[houseid] = dict(DEFAULT_THRESHOLDS)
    print(f"[MOCK] Reset ngưỡng về mặc định cho {houseid}")
    return {"status": "success", "thresholds": DEFAULT_THRESHOLDS}


# --- Kênh thông báo ---
@app.get("/api/notification-channels")
async def get_notification_channels(houseid: str = "HS001"):
    """Lấy cấu hình kênh thông báo."""
    return mock_channels.get(houseid, {
        "email":    {"enabled": False},
        "telegram": {"enabled": False},
        "app":      {"enabled": True},
    })


@app.post("/api/notification-channels")
async def update_notification_channel(payload: dict = Body(...)):
    """Cập nhật kênh thông báo."""
    houseid = payload.get("houseid", "HS001")
    channel = payload.get("channel")
    enabled = payload.get("enabled", True)

    VALID_CHANNELS = ("email", "telegram", "app")
    if channel not in VALID_CHANNELS:
        return JSONResponse(status_code=400, content={
            "status": "error", "message": f"Kênh '{channel}' không được hỗ trợ."
        })

    if houseid not in mock_channels:
        mock_channels[houseid] = {
            "email": {"enabled": False}, "telegram": {"enabled": False}, "app": {"enabled": True}
        }

    if channel not in mock_channels[houseid]:
        mock_channels[houseid][channel] = {}

    mock_channels[houseid][channel]["enabled"] = enabled

    # Lưu thông tin liên lạc
    if channel == "telegram":
        if "bot_token" in payload:
            mock_channels[houseid][channel]["bot_token"] = payload["bot_token"]
        if "chat_id" in payload:
            mock_channels[houseid][channel]["chat_id"] = payload["chat_id"]
    elif channel == "email":
        if "address" in payload:
            mock_channels[houseid][channel]["address"] = payload["address"]

    print(f"[MOCK] Cập nhật kênh {channel}: enabled={enabled}")
    return {"status": "success", "message": "Cập nhật thành công."}


# --- Kịch bản tự động (Automation Rules) ---
@app.get("/api/automation-rules")
async def get_automation_rules(houseid: str = "HS001"):
    """Lấy danh sách kịch bản tự động."""
    return [r for r in mock_automation_rules if r.get("houseid") == houseid]


@app.post("/api/automation-rules")
async def create_automation_rule(payload: dict = Body(...)):
    """Tạo hoặc cập nhật kịch bản tự động."""
    houseid = payload.get("houseid", "HS001")
    name = payload.get("name")
    condition = payload.get("condition")
    actions = payload.get("actions") or payload.get("action")
    enabled = payload.get("enabled", payload.get("isactive", True))

    if not name:
        return JSONResponse(status_code=400, content={
            "status": "error", "message": "Thiếu tên kịch bản."
        })
    if not condition or not all(k in condition for k in ("sensor", "op", "value")):
        return JSONResponse(status_code=400, content={
            "status": "error", "message": "Điều kiện không hợp lệ."
        })
    if not actions:
        return JSONResponse(status_code=400, content={
            "status": "error", "message": "Thiếu hành động phản hồi."
        })

    try:
        condition = {**condition, "value": float(condition["value"])}
    except (TypeError, ValueError):
        return JSONResponse(status_code=400, content={
            "status": "error", "message": "Giá trị điều kiện phải là số."
        })

    scenario_id = f"{houseid}_{name.replace(' ', '_')}"

    # Kiểm tra đã tồn tại chưa -> cập nhật
    existing = next((r for r in mock_automation_rules if r["_id"] == scenario_id), None)
    if existing:
        existing.update({
            "name": name,
            "condition": condition,
            "action": actions,
            "actions": actions,
            "isactive": enabled,
            "enabled": enabled,
        })
    else:
        new_rule = {
            "_id": scenario_id,
            "scenarioid": scenario_id,
            "houseid": houseid,
            "name": name,
            "condition": condition,
            "action": actions,
            "actions": actions,
            "isactive": enabled,
            "enabled": enabled,
            "createdat": datetime.now().isoformat(),
        }
        mock_automation_rules.append(new_rule)

    print(f"[MOCK] Lưu kịch bản tự động: '{name}'")
    return {"status": "success", "message": "Tạo kịch bản thành công.", "scenarioid": scenario_id}


@app.delete("/api/automation-rules")
async def delete_automation_rule(houseid: str = "HS001", name: str = ""):
    """Xóa kịch bản tự động."""
    global mock_automation_rules
    scenario_id = f"{houseid}_{name.replace(' ', '_')}"
    before = len(mock_automation_rules)
    mock_automation_rules = [r for r in mock_automation_rules if r["_id"] != scenario_id]
    if len(mock_automation_rules) < before:
        print(f"[MOCK] Đã xóa kịch bản: '{name}'")
        return {"status": "success", "message": "Đã xóa kịch bản."}
    return {"status": "error", "message": "Kịch bản không tồn tại."}


@app.patch("/api/automation-rules/toggle")
async def toggle_automation_rule(payload: dict = Body(...)):
    """Bật/tắt kịch bản tự động."""
    houseid = payload.get("houseid", "HS001")
    name = payload.get("name")
    enabled = payload.get("enabled", payload.get("isactive", True))
    scenario_id = f"{houseid}_{name.replace(' ', '_')}"

    for rule in mock_automation_rules:
        if rule["_id"] == scenario_id:
            rule["isactive"] = enabled
            rule["enabled"] = enabled
            print(f"[MOCK] Toggle kịch bản '{name}': enabled={enabled}")
            return {"status": "success"}

    return {"status": "error", "message": "Kịch bản không tồn tại."}


# --- Kiểm tra nguy hiểm ---
@app.get("/api/check-danger")
async def check_danger_now(houseid: str = "HS001"):
    """Kiểm tra tình trạng nguy hiểm hiện tại."""
    item = MOCK_LOGS[current_index % len(MOCK_LOGS)] if current_index > 0 else MOCK_LOGS[0]
    thresholds = mock_thresholds.get(houseid, DEFAULT_THRESHOLDS)
    sensor_data = {"temp": item["temp"], "humi": item["humi"], "light": item["light"]}

    violations = []
    for sensor, limits in thresholds.items():
        val = sensor_data.get(sensor, 0)
        if val > limits.get("max", 100):
            violations.append({"sensor": sensor, "value": val, "threshold": "max", "limit": limits["max"]})
        elif val < limits.get("min", 0):
            violations.append({"sensor": sensor, "value": val, "threshold": "min", "limit": limits["min"]})

    return {
        "is_danger": len(violations) > 0,
        "violations": violations,
        "thresholds_used": thresholds,
        "sensor_data": sensor_data,
    }


# --- Danger logs ---
@app.get("/api/danger-logs")
async def get_danger_logs(houseid: str = "HS001", limit: int = 50):
    """Lấy lịch sử cảnh báo nguy hiểm."""
    logs = [d for d in mock_danger_logs if d.get("houseid") == houseid]
    return logs[:limit]


# --- Tắt báo động ---
@app.post("/api/stop-alert")
async def manual_stop_alert(payload: dict = Body(...)):
    """Tắt báo động thủ công."""
    global is_danger_global
    is_danger_global = False
    houseid = payload.get("houseid", "HS001")
    print(f"[MOCK] TẮT báo động thủ công (house: {houseid})")
    return {"status": "success", "message": "Đã tắt báo động."}


# ============================================================
#                    MODULE 3 ENDPOINTS
# ============================================================

@app.get("/api/scenes")
async def get_scenes():
    """Lấy danh sách kịch bản (format mới khớp module3.py)."""
    return [
        {
            "modeid": s.get("modeid", s.get("_id", "")),
            "houseid": s.get("houseid", "HS001"),
            "name": s.get("name", ""),
            "action": s.get("action", []),
            "isactive": s.get("isactive", True),
            "createdat": s.get("createdat", ""),
        }
        for s in mock_scenes
    ]


@app.post("/api/scenes")
async def create_scene(payload: dict = Body(...)):
    """Tạo kịch bản mới (khớp module3.py)."""
    name = payload.get("name")
    action = payload.get("action")
    houseid = payload.get("houseid", "HS001")
    isactive = payload.get("isactive", True)

    if not name or not action:
        return JSONResponse(status_code=400, content={
            "status": "Error", "message": "Missing name or action"
        })

    # Kiểm tra trùng tên -> cập nhật
    existing = next((s for s in mock_scenes if s["name"] == name), None)
    if existing:
        existing["action"] = action
        existing["isactive"] = isactive
        existing["houseid"] = houseid
    else:
        new_scene = {
            "_id": f"scene{len(mock_scenes) + 1:03d}",
            "modeid": f"scene{len(mock_scenes) + 1:03d}",
            "houseid": houseid,
            "name": name,
            "action": action,
            "isactive": isactive,
            "createdat": datetime.now().isoformat(),
        }
        mock_scenes.append(new_scene)

    print(f"[MOCK] Lưu kịch bản: '{name}'")
    return {"status": "success", "message": f"Saved scene '{name}'"}


@app.delete("/api/scenes")
async def delete_scene(name: str = Query(...)):
    """Xóa kịch bản theo tên."""
    global mock_scenes
    before = len(mock_scenes)
    mock_scenes = [s for s in mock_scenes if s["name"] != name]
    if len(mock_scenes) < before:
        print(f"[MOCK] Đã xóa kịch bản: '{name}'")
        return {"status": "Deleted", "name": name}
    return {"status": "Not Found"}


def apply_scene_to_status(current_status, actions):
    """Hàm helper: Trộn lệnh của kịch bản vào mảng device_status hiện tại."""
    status_dict = {item[0]: item[1] for item in current_status}
    for act in actions:
        dev_id = act.get("device_id", act.get("numberdevice"))
        val = act.get("value", act.get("status"))
        if dev_id is not None and val is not None:
            status_dict[dev_id] = val
    return [[k, v] for k, v in status_dict.items()]


@app.post("/api/activate-scene")
async def activate_scene(payload: dict = Body(...)):
    """Kích hoạt kịch bản (khớp module3.py — nhận 'name')."""
    global device_status
    name = payload.get("name")
    if not name:
        return JSONResponse(status_code=400, content={
            "status": "Error", "message": "Missing name"
        })

    scene = next((s for s in mock_scenes if s["name"] == name), None)
    if not scene:
        return JSONResponse(status_code=404, content={
            "status": "Error", "message": "Scene not found"
        })

    device_status = apply_scene_to_status(device_status, scene.get("action", []))
    print(f"[MOCK] Kích hoạt kịch bản '{name}'. Lệnh mới: {device_status}")
    return {"status": "Success", "new_commands": device_status}


@app.post("/api/deactivate-scene")
async def deactivate_scene(payload: dict = Body(...)):
    """Tắt kịch bản — đảo ngược các hành động (khớp module3.py)."""
    global device_status
    name = payload.get("name")
    if not name:
        return JSONResponse(status_code=400, content={
            "status": "Error", "message": "Missing name"
        })

    scene = next((s for s in mock_scenes if s["name"] == name), None)
    if not scene:
        return JSONResponse(status_code=404, content={
            "status": "Error", "message": "Scene not found"
        })

    actions = scene.get("action", [])
    reversed_actions = []
    for item in actions:
        dev_id = item.get("numberdevice", item.get("device_id"))
        state = item.get("status", item.get("value"))
        if dev_id is None or state is None:
            continue
        if isinstance(state, bool) and state is True:
            reversed_actions.append({"device_id": dev_id, "value": False})
        elif isinstance(state, int) and not isinstance(state, bool) and state > 0:
            reversed_actions.append({"device_id": dev_id, "value": 0})

    device_status = apply_scene_to_status(device_status, reversed_actions)
    print(f"[MOCK] Tắt kịch bản '{name}'. Lệnh mới: {device_status}")
    return {"status": "Success", "new_commands": device_status}


# ============================================================
#              ENDPOINTS CHIA SẺ (SERVER.PY)
# ============================================================

@app.get("/api/get-commands")
async def get_commands():
    """Yolobit gọi GET để lấy lệnh điều khiển."""
    commands_array = [{"numberdevice": item[0], "status": item[1]} for item in device_status]
    return {
        "numberdevices": commands_array,
        "is_danger": is_danger_global,
    }


@app.post("/api/control")
async def control_device(payload: dict = Body(...)):
    """Frontend gọi POST để thay đổi trạng thái thiết bị."""
    global device_status
    new_cmd = payload.get("commands")
    if new_cmd:
        device_status = new_cmd
        print(f"[MOCK] Lệnh điều khiển mới: {device_status}")
        return {"status": "Updated"}
    return JSONResponse(status_code=400, content={"status": "Error"})


@app.post("/update")
async def handle_data(payload: dict = Body(...)):
    """Nhận dữ liệu từ Yolobit (giả lập)."""
    return {"status": "Success"}


# ============================================================
#              BACKGROUND TASKS (Timer scenes)
# ============================================================

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
            trigger_time = scene.get("trigger_time", "")
            trigger_type = scene.get("trigger_type", "")
            if trigger_type == "timer" and trigger_time == now_str:
                print(f"\n[AUTO-TRIGGER] Đã đến {now_str}. Tự động kích hoạt: {scene['name']}")
                device_status = apply_scene_to_status(device_status, scene.get("action", []))
                triggered_any = True
                
        if triggered_any:
            last_triggered_minute = now_str


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_scene_timers())


if __name__ == "__main__":
    print("=" * 60)
    print("  MOCK SERVER - Dữ liệu giả cho Frontend (ĐẦY ĐỦ)")
    print("  Bao gồm: Module 1 + Module 2 + Module 3 + Server")
    print("  http://localhost:5000")
    print("=" * 60)
    print()
    print("  Endpoints có sẵn:")
    print("  ─── Module 1 (Dashboard) ───")
    print("  GET  /api/sensor-data")
    print("  GET  /api/sensor-comparison")
    print("  GET  /api/realtime-trend")
    print("  GET  /api/weekly-trend")
    print("  GET  /api/sensor-alerts")
    print("  GET  /api/history-by-date?date=2026-03-06")
    print()
    print("  ─── Module 2 (An toàn & Tự động) ───")
    print("  GET  /api/thresholds?houseid=HS001")
    print("  POST /api/thresholds")
    print("  POST /api/thresholds/reset")
    print("  GET  /api/notification-channels?houseid=HS001")
    print("  POST /api/notification-channels")
    print("  GET  /api/automation-rules?houseid=HS001")
    print("  POST /api/automation-rules")
    print("  DEL  /api/automation-rules?houseid=HS001&name=...")
    print("  PATCH /api/automation-rules/toggle")
    print("  GET  /api/check-danger?houseid=HS001")
    print("  GET  /api/danger-logs?houseid=HS001")
    print("  POST /api/stop-alert")
    print()
    print("  ─── Module 3 (Kịch bản) ───")
    print("  GET  /api/scenes")
    print("  POST /api/scenes")
    print("  DEL  /api/scenes?name=...")
    print("  POST /api/activate-scene")
    print("  POST /api/deactivate-scene")
    print()
    print("  ─── Server ───")
    print("  GET  /api/get-commands")
    print("  POST /api/control")
    print("  POST /update")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=5000)
