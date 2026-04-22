from fastapi import APIRouter, Query, Request
from datetime import datetime, timezone, timedelta  # <--- THÊM timezone, timedelta
router = APIRouter(prefix="/api/logging", tags=["Module 4"])

sensor_collection = None
danger_collection = None
device_collection = None
logupdate_collection = None  # ← db.Logupdate (thay cho system_update_collection)
_threshold_mgr = None

DEFAULT_THRESHOLDS = {
    "temp": {"min": 0, "max": 40},
    "humi": {"min": 20, "max": 80},
    "light": {"min": 0, "max": 90},
}


# =============================
# INIT MODULE
# =============================
def init_module4(
    sensor_col, danger_col, device_col, logupdate_col=None, threshold_mgr=None
):
    global sensor_collection, danger_collection, device_collection
    global logupdate_collection, _threshold_mgr

    sensor_collection = sensor_col
    danger_collection = danger_col
    device_collection = device_col
    logupdate_collection = logupdate_col  # db.Logupdate
    _threshold_mgr = threshold_mgr


# =============================
# FORMAT TIME
# =============================
def format_time(t):
    if isinstance(t, datetime):
        return t.strftime("%Y-%m-%d %H:%M:%S")
    return str(t) if t else "--"


# =============================
# SENSOR STATUS — dùng ngưỡng động từ module2
# =============================
def get_sensor_status(temp, humi, light, thresholds: dict) -> str:
    # Lấy ngưỡng MIN/MAX, ưu tiên định dạng phẳng (tempmax, humimax...) từ house-info
    # Nếu không có thì fallback về dạng lồng nhau hoặc giá trị mặc định.
    t_min = thresholds.get("tempmin", thresholds.get("temp", DEFAULT_THRESHOLDS["temp"]).get("min", 0))
    t_max = thresholds.get("tempmax", thresholds.get("temp", DEFAULT_THRESHOLDS["temp"]).get("max", 40))
    
    h_min = thresholds.get("humimin", thresholds.get("humi", DEFAULT_THRESHOLDS["humi"]).get("min", 20))
    h_max = thresholds.get("humimax", thresholds.get("humi", DEFAULT_THRESHOLDS["humi"]).get("max", 80))
    
    l_min = thresholds.get("lightmin", thresholds.get("light", DEFAULT_THRESHOLDS["light"]).get("min", 0))
    l_max = thresholds.get("lightmax", thresholds.get("light", DEFAULT_THRESHOLDS["light"]).get("max", 90))

    # Nếu VƯỢT QUÁ ngưỡng (nhỏ hơn min hoặc lớn hơn max) -> Nguy hiểm
    if (temp < t_min or temp > t_max) or \
       (humi < h_min or humi > h_max) or \
       (light < l_min or light > l_max):
        return "Nguy hiểm"
        
    return "Bình thường"


# =============================
# DEVICE MAP
# =============================
DEVICE_MAP = {
    1: "Đèn báo trộm",
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
    limit: int = Query(0),
):
    if danger_collection is None:
        return []

    # Lấy cấu hình ngưỡng hiện tại (Làm mốc dự phòng)
    thresholds = DEFAULT_THRESHOLDS
    mgr = getattr(request.app.state, "threshold_mgr", _threshold_mgr)
    if mgr:
        try:
            thresholds = await mgr.get_thresholds(houseid)
        except Exception:
            pass

    # Đọc đúng cấu trúc dữ liệu phẳng từ API
    t_max = thresholds.get("tempmax", thresholds.get("temp", DEFAULT_THRESHOLDS["temp"]).get("max", 40))
    t_min = thresholds.get("tempmin", thresholds.get("temp", DEFAULT_THRESHOLDS["temp"]).get("min", 0))

    h_max = thresholds.get("humimax", thresholds.get("humi", DEFAULT_THRESHOLDS["humi"]).get("max", 80))
    h_min = thresholds.get("humimin", thresholds.get("humi", DEFAULT_THRESHOLDS["humi"]).get("min", 20))

    l_max = thresholds.get("lightmax", thresholds.get("light", DEFAULT_THRESHOLDS["light"]).get("max", 90))
    l_min = thresholds.get("lightmin", thresholds.get("light", DEFAULT_THRESHOLDS["light"]).get("min", 0))

    # Cập nhật Label hiển thị dạng khoảng [Min - Max]
    SENSOR_THRESHOLD_LABEL = {
        "temp": f"[{t_min} - {t_max}]°C",
        "humi": f"[{h_min} - {h_max}]%",
        "light": f"[{l_min} - {l_max}]%",
    }
    SENSOR_UNIT = {"temp": "°C", "humi": "%", "light": "%"}

    cursor = danger_collection.find({"houseid": houseid}).sort("time", -1).limit(limit)

    result = []
    async for doc in cursor:
        violations = doc.get("violations", [])

        if violations:
            for v in violations:
                sensor = v.get("sensor", "Không rõ")
                actual_val = v.get("value", "--")
                unit = SENSOR_UNIT.get(sensor, "")

                # KIỂM TRA DỮ LIỆU ĐỂ QUYẾT ĐỊNH MỨC ĐỘ VÀ CÁCH HIỂN THỊ
                if actual_val == "--":
                    display_actual = "--"
                    display_level = "Cảnh báo"
                else:
                    display_actual = f"{actual_val}{unit}"
                    display_level = "Nguy hiểm"

                # --- ĐOẠN MỚI CẦN THAY THẾ ---
                # Lấy cả loại (max/min) và con số giới hạn
                historical_type = v.get("threshold") 
                historical_limit = v.get("limit")
                
                if historical_limit is not None:
                    # Format hiển thị "Max: 22.5°C" hoặc "Min: 10%"
                    if historical_type == "max":
                        threshold_label = f"Max: {historical_limit}{unit}"
                    elif historical_type == "min":
                        threshold_label = f"Min: {historical_limit}{unit}"
                    else:
                        threshold_label = f"Ngưỡng: {historical_limit}{unit}"
                else:
                    # Fallback dự phòng cho các log quá cũ
                    fallback_val = v.get("threshold")
                    if not isinstance(fallback_val, (int, float)):
                        fallback_val = doc.get("threshold")
                        
                    if isinstance(fallback_val, (int, float)):
                        threshold_label = f"Ngưỡng: {fallback_val}{unit}"
                    else:
                        threshold_label = SENSOR_THRESHOLD_LABEL.get(sensor, "--")
                # --- KẾT THÚC ĐOẠN SỬA ---

                result.append(
                    {
                        "time": format_time(doc.get("time")),
                        "sensor": sensor,
                        "threshold": threshold_label,
                        "actual": display_actual, # Sử dụng biến đã format
                        "level": display_level,   # Sử dụng biến level đã xét điều kiện
                    }
                )
        else:
            # Fallback cho các bản ghi DB cũ
            historical_threshold = doc.get("threshold")
            if historical_threshold is not None:
                threshold_label = str(historical_threshold)
            else:
                threshold_label = SENSOR_THRESHOLD_LABEL.get(doc.get("sensor", "temp"), "--")

            actual_val = doc.get("actual", "--")
            # Kiểm tra tương tự cho dữ liệu cũ
            display_level = "Cảnh báo" if actual_val == "--" else "Nguy hiểm"

            result.append(
                {
                    "time": format_time(doc.get("time")),
                    "sensor": doc.get("sensor", "Không rõ"),
                    "threshold": threshold_label,
                    "actual": actual_val,
                    "level": display_level, # Sử dụng biến level đã xét điều kiện
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
    limit: int = Query(0),
):
    if sensor_collection is None:
        return []

    thresholds = DEFAULT_THRESHOLDS
    mgr = getattr(request.app.state, "threshold_mgr", _threshold_mgr)
    if mgr:
        try:
            thresholds = await mgr.get_thresholds(houseid)
        except Exception:
            pass

    cursor = sensor_collection.find({"houseid": houseid}).sort("time", -1).limit(limit)
    result = []
    async for doc in cursor:
        temp = doc.get("temp", 0)
        humi = doc.get("humi", 0)
        light = doc.get("light", 0)
        
        # SỬA LỖI: Ưu tiên lấy trạng thái (status) đã được gán tại thời điểm lưu DB
        status = doc.get("status")
        if not status:
            # Chỉ khi DB không có sẵn trạng thái thì mới đành phải tính toán lại bằng cấu hình hiện tại
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
async def get_device_history(
    houseid: str = Query("HS001"),
    limit: int = Query(0),
):
    if device_collection is None:
        return []

    cursor = device_collection.find({"houseid": houseid}).sort("time", -1).limit(limit)

    result = []
    async for doc in cursor:
        device_num = doc.get("numberdevice")

        # --- THÊM 2 DÒNG NÀY VÀO ĐÂY ---
        # Nếu là thiết bị số 5 thì bỏ qua, không đọc và không thêm vào mảng kết quả
        if device_num == 5:
            continue
        # -------------------------------

        old_status = doc.get("old_status", False)
        new_status = doc.get("new_status", False)
        reason = doc.get("reason", "")

        # --- Nâng cấp hàm xử lý trạng thái ---
        def format_status(val, dev_num):
            # 1. Xử lý RIÊNG cho Servo (Thiết bị số 6)
            if dev_num == 6:
                if val == 0 or val is False:
                    return "Đóng"
                return "Mở"

            # 2. Xử lý RIÊNG cho Quạt (Thiết bị số 7)
            if dev_num == 7:
                if val == 0 or val is False:
                    return "Tắt"
                elif val == 70:
                    return "Mức 1"
                elif val == 80:
                    return "Mức 2"
                elif val == 90:
                    return "Mức 3"
                elif val == 100:
                    return "Mức 4"
                # Dự phòng nếu sau này có gửi số lạ không nằm trong 4 mức trên
                return f"Mức {val}"

            # 3. Nếu là Đèn/Công tắc thông thường (True/False)
            if isinstance(val, bool):
                return "Bật" if val else "Tắt"

            # Các trường hợp thiết bị khác (nếu có)
            return str(val)

        result.append(
            {
                "time": format_time(doc.get("time")),
                "device": DEVICE_MAP.get(device_num, f"Thiết bị {device_num}"),
                "old_value": format_status(old_status, device_num),
                "new_value": format_status(new_status, device_num),
                "actor": (
                    "Hệ thống"
                    if any(
                        kw in reason.lower()
                        for kw in ["hệ thống", "tự động", "ngừng phát hiện"]
                    )
                    else "Người dùng"
                ),
            }
        )

    return result


# =============================
# 4. SYSTEM UPDATE HISTORY — đọc từ db.Logupdate
# Format mới từ module2:
# {
#   "time": datetime,
#   "houseid": str,
#   "target": "Cấu hình ngưỡng (temp)",
#   "oldvalue": [{"min": 0, "max": 40}],
#   "newvalue": [{"min": 0, "max": 35}]
# }
# =============================
@router.get("/system-updates")
async def get_system_updates(
    houseid: str = "HS001",
    limit: int = Query(0),
):
    if logupdate_collection is None:
        return []

    cursor = (
        logupdate_collection.find({"houseid": houseid}).sort("time", -1).limit(limit)
    )

    result = []
    async for doc in cursor:
        target = doc.get("target", "--")
        oldvalue = doc.get("oldvalue", [])
        newvalue = doc.get("newvalue", [])

        # Format oldvalue/newvalue thành string dễ đọc
        def fmt_value(val):
            if isinstance(val, list) and len(val) > 0:
                v = val[0]
                if isinstance(v, dict):
                    # {"min": x, "max": y} → "min: x, max: y"
                    parts = [f"{k}: {v2}" for k, v2 in v.items()]
                    return " | ".join(parts)
                return str(v)
            return str(val) if val else "--"

        result.append(
            {
                "time": format_time(doc.get("time")),
                "field": target,
                "old_value": fmt_value(oldvalue),
                "new_value": fmt_value(newvalue),
            }
        )

    return result
