from fastapi import APIRouter, Query, Request
from datetime import datetime

router = APIRouter(prefix="/api/logging", tags=["Module 4"])

sensor_collection = None
danger_collection = None
device_collection = None
system_collection = None
_threshold_mgr = None  # ← Tham chiếu tới ThresholdManager của module2

DEFAULT_THRESHOLDS = {
    "temp": {"min": 0, "max": 40},
    "humi": {"min": 20, "max": 80},
    "light": {"min": 0, "max": 90},
}


# =============================
# INIT MODULE
# =============================
def init_module4(
    sensor_col, danger_col, device_col, system_col=None, threshold_mgr=None
):
    global sensor_collection, danger_collection, device_collection
    global system_collection, _threshold_mgr

    sensor_collection = sensor_col
    danger_collection = danger_col
    device_collection = device_col
    system_collection = system_col
    _threshold_mgr = threshold_mgr  # ← Nhận ThresholdManager từ module2


# =============================
# FORMAT TIME
# =============================
def format_time(t):
    if isinstance(t, datetime):
        return t.strftime("%Y-%m-%d %H:%M:%S")
    return t


# =============================
# SENSOR STATUS LOGIC — dùng ngưỡng động từ module2
# =============================
def get_sensor_status(temp, humi, light, thresholds: dict) -> str:
    """
    Dùng ngưỡng max từ ThresholdManager thay vì hardcode.
    Nếu bất kỳ cảm biến nào vượt max → trạng thái tương ứng.
    """
    t_max = thresholds.get("temp", DEFAULT_THRESHOLDS["temp"]).get("max", 40)
    h_max = thresholds.get("humi", DEFAULT_THRESHOLDS["humi"]).get("max", 80)
    l_max = thresholds.get("light", DEFAULT_THRESHOLDS["light"]).get("max", 90)

    # Mức nguy hiểm: vượt ngưỡng max 10%
    if temp > t_max * 1.1 or humi > h_max * 1.1 or light > l_max * 1.1:
        return "Nguy hiểm"

    # Mức cảnh báo: vượt ngưỡng max
    if temp > t_max or humi > h_max or light > l_max:
        return "Cảnh báo"

    return "Bình thường"


# =============================
# DEVICE MAP
# =============================
DEVICE_MAP = {
    1: "Đèn 1 (PIR)",
    2: "Đèn 2",
    3: "Đèn 3",
    4: "Đèn 4",
    5: "Đèn 5",
    6: "Servo (Cửa)",
    7: "Quạt",
}


# =============================
# 1. DANGER HISTORY
# =============================
@router.get("/danger-history")
async def get_danger_history(
    request: Request,
    houseid: str = "HS001",
    limit: int = Query(20),
):
    if danger_collection is None:
        return []

    # Lấy ngưỡng thực từ module2
    thresholds = DEFAULT_THRESHOLDS
    mgr = getattr(request.app.state, "threshold_mgr", _threshold_mgr)
    if mgr:
        try:
            thresholds = await mgr.get_thresholds(houseid)
        except Exception:
            pass

    t_max = thresholds.get("temp", DEFAULT_THRESHOLDS["temp"]).get("max", 40)
    h_max = thresholds.get("humi", DEFAULT_THRESHOLDS["humi"]).get("max", 80)
    l_max = thresholds.get("light", DEFAULT_THRESHOLDS["light"]).get("max", 90)

    SENSOR_THRESHOLD_LABEL = {
        "temp": f"≤ {t_max}°C",
        "humi": f"≤ {h_max}%",
        "light": f"≤ {l_max}%",
    }
    SENSOR_UNIT = {"temp": "°C", "humi": "%", "light": "%"}

    cursor = danger_collection.find({"houseid": houseid}).sort("time", -1).limit(limit)

    result = []
    async for doc in cursor:
        violations = doc.get("violations", [])

        if violations:
            # Mỗi violation tạo 1 dòng riêng
            for v in violations:
                sensor = v.get("sensor", "Không rõ")
                actual_val = v.get("value", "--")
                unit = SENSOR_UNIT.get(sensor, "")
                threshold_label = SENSOR_THRESHOLD_LABEL.get(sensor, "--")

                result.append(
                    {
                        "time": format_time(doc.get("time")),
                        "sensor": sensor,
                        "threshold": threshold_label,
                        "actual": f"{actual_val}{unit}",
                        "level": (
                            "Nguy hiểm"
                            if v.get("value", 0)
                            > thresholds.get(
                                sensor, DEFAULT_THRESHOLDS.get(sensor, {})
                            ).get("max", 100)
                            * 1.1
                            else "Cảnh báo"
                        ),
                    }
                )
        else:
            # Fallback: doc cũ không có violations
            result.append(
                {
                    "time": format_time(doc.get("time")),
                    "sensor": doc.get("sensor", "Không rõ"),
                    "threshold": doc.get("threshold", "--"),
                    "actual": doc.get("actual", "--"),
                    "level": doc.get("level", "Cảnh báo"),
                }
            )

    return result


# =============================
# 2. SENSOR HISTORY
# =============================
@router.get("/sensor-history")
async def get_sensor_history(
    request: Request,
    houseid: str = "HS001",
    limit: int = Query(20),
):
    if sensor_collection is None:
        return []

    # Lấy ngưỡng thực từ module2
    thresholds = DEFAULT_THRESHOLDS
    mgr = getattr(request.app.state, "threshold_mgr", _threshold_mgr)
    if mgr:
        try:
            thresholds = await mgr.get_thresholds(houseid)
        except Exception:
            pass

    cursor = sensor_collection.find().sort("time", -1).limit(limit)

    result = []
    async for doc in cursor:
        temp = doc.get("temp", 0)
        humi = doc.get("humi", 0)
        light = doc.get("light", 0)

        # ← Dùng ngưỡng động thay vì hardcode
        status = get_sensor_status(temp, humi, light, thresholds)

        result.append(
            {
                "time": format_time(doc.get("time")),
                "temp": temp,
                "humi": humi,
                "light": light,
                "status": status,
            }
        )

    return result


# =============================
# 3. DEVICE HISTORY
# =============================
@router.get("/device-history")
async def get_device_history(limit: int = Query(20)):
    if device_collection is None:
        return []

    cursor = device_collection.find().sort("time", -1).limit(limit)

    result = []
    async for doc in cursor:
        device_num = doc.get("numberdevice")
        old_status = doc.get("old_status", False)
        new_status = doc.get("new_status", False)
        reason = doc.get("reason", "")

        result.append(
            {
                "time": format_time(doc.get("time")),
                "device": DEVICE_MAP.get(device_num, f"Thiết bị {device_num}"),
                "old_value": "Bật" if old_status else "Tắt",
                "new_value": "Bật" if new_status else "Tắt",
                "actor": "Hệ thống" if "hệ thống" in reason.lower() else "Người dùng",
            }
        )

    return result


# =============================
# 4. SYSTEM UPDATE HISTORY
# =============================
@router.get("/system-updates")
async def get_system_updates(limit: int = Query(20)):
    if system_collection is None:
        return []

    cursor = system_collection.find().sort("time", -1).limit(limit)

    result = []
    async for doc in cursor:
        result.append(
            {
                "time": format_time(doc.get("time")),
                "field": doc.get("field"),
                "old_value": doc.get("old_value"),
                "new_value": doc.get("new_value"),
            }
        )

    return result
