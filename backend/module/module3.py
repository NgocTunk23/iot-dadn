from fastapi import APIRouter, Body, Query
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pydantic.v1.json import ENCODERS_BY_TYPE
ENCODERS_BY_TYPE[ObjectId] = str

# Khởi tạo Router cho Module 3
router = APIRouter()

def get_default_device_name(dev_num, dev_type):
    # Với denchongtrom thì giữ tên cũ (như trước quy ước), den thì là Đèn + num
    if dev_type == "denchongtrom": return "Đèn báo trộm" 
    if dev_type == "den": return f"Đèn {dev_num}"
    if dev_type == "servo": return "Cửa (Servo)"
    if dev_type == "quat": return "Quạt"
    return f"Thiết bị {dev_num}"

def format_device_status(numberdevice, status, dev_type="unknown"):
    """Chuyển status thô thành text có ý nghĩa dựa trên type thiết bị."""
    name = get_default_device_name(numberdevice, dev_type)
    if dev_type in ("den", "denchongtrom"):
        status_text = "Bật" if status else "Tắt"
    elif dev_type == "servo":
        status_text = "Mở" if (isinstance(status, int) and status >= 45) else "Đóng"
    elif dev_type == "quat":
        status_text = "Chạy" if (isinstance(status, int) and status > 0) else "Tắt"
    else:
        status_text = str(status)
    return {"type": dev_type, "name": name, "numberdevice": numberdevice, "status": status, "status_text": status_text}

# Biến toàn cục từ điển thiết bị
device_status_map = {}

_scene_manager = None
_house_col = None

def init_module3(manager, house_col=None):
    global _scene_manager, _house_col
    _scene_manager = manager
    _house_col = house_col

# --- LOGIC GHI LOG THIẾT BỊ (DEVICE_LOG - CHUẨN ERD) ---

async def log_device_state(houseid, numberdevice, dev_type, status, reason="Điều khiển"):
    """Ghi nhật ký thay đổi trạng thái thiết bị theo chuẩn ERD."""
    if _house_col is None: return
    try:
        device_log_col = _house_col.database.Device_log
        now_utc = datetime.now(timezone.utc)
        
        # Tạo ID duy nhất theo chuẩn DB của nhóm (Time + ID + House)
        timestamp_str = now_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        log_id = f"{timestamp_str}{numberdevice}_{houseid}"
        
        log_entry = {
            "_id": log_id,
            "time": now_utc,
            "houseid": houseid,
            "numberdevice": numberdevice,
            "type": dev_type,
            "status": status,
            "reason": reason
        }
        await device_log_col.update_one({"_id": log_id}, {"$set": log_entry}, upsert=True)
        print(f"[MODULE3] Ghi Log: {houseid} - {dev_type} ({numberdevice}) -> {status} [{reason}]")
    except Exception as e:
        print(f"[MODULE3] Lỗi ghi log: {e}")

# --- LOGIC ĐĂNG NHẬP (Lấy bảng User từ database của bảng House) ---

@router.post("/login")
async def login_api_override(payload: dict = Body(...)):
    if _house_col is None: return {"success": False, "message": "Database chưa khởi tạo"}
    users_collection = _house_col.database.User
    
    username_input, password, house_id = payload.get("username"), payload.get("password"), payload.get("houseid")
    if not username_input or not password: return {"success": False, "message": "Thiếu thông tin đăng nhập"}

    try:
        user = await users_collection.find_one({"$or": [{"email": username_input}, {"_id": username_input}]})
        if not user or user.get("password") != password: 
            return {"success": False, "message": "Sai tài khoản hoặc mật khẩu"}
        
        actual_username = user.get("_id")
        house = await _house_col.find_one({"_id.houseid": house_id, "_id.username": actual_username})
        if not house: return {"success": False, "message": "House ID không thuộc tài khoản này"}

        user_data = {k: v for k, v in user.items() if k != "password"}
        return {"success": True, "message": "Đăng nhập thành công", "user": user_data, "houseid": house_id}
    except Exception as e: return {"success": False, "message": f"Lỗi hệ thống: {str(e)}"}

# --- LOGIC ĐIỀU KHIỂN & GHI LOG (Hỗ trợ ghi đè /api/control của server.py) ---

@router.post("/control")
async def update_control_override(payload: dict = Body(...)):
    """
    Điều khiển thiết bị và tự động ghi Device_log theo chuẩn ERD.
    Dữ liệu nhận: {"houseid": "HS001", "commands": [[2, True], [6, 85]]}
    """
    house_id = payload.get("houseid", "HS001")
    new_cmds = payload.get("commands")
    if not new_cmds: return {"status": "Error", "message": "Thiếu lệnh điều khiển"}, 400

    # Lấy trạng thái hiện tại để so sánh và tìm type
    try:
        house = await _house_col.find_one({"_id.houseid": house_id})
        dev_map = {d["numberdevice"]: d for d in house.get("numberdevices", [])} if house else {}
        
        # Cập nhật bản đồ trạng thái toàn bô
        device_status_map[house_id] = new_cmds
        
        # Ghi Log cho từng thay đổi
        for cmd in new_cmds:
            d_id, d_val = cmd[0], cmd[1]
            d_type = dev_map.get(d_id, {}).get("type", "unknown")
            await log_device_state(house_id, d_id, d_type, d_val, reason="Người dùng điều khiển thủ công")

        # Đồng bộ vào bảng House (vẫn giữ logic của Module 2)
        from module.module2 import sync_device_state
        await sync_device_state(_house_col, house_id, new_cmds)
        
        return {"status": "Updated", "message": "Đã điều khiển và ghi log"}
    except Exception as e:
        print(f"[MODULE3] Lỗi điều khiển: {e}")
        return {"status": "Error", "message": str(e)}, 500

# --- QUẢN LÝ KỊCH BẢN / CHẾ ĐỘ (MAPPING SANG BẢNG 'MODE') ---

class SceneManager:
    def __init__(self, scenes_collection):
        # Chuyển đổi linh hoạt sang bảng 'Mode' nếu khả dụng
        self.scenes_collection = scenes_collection
        self.tz_vn = timezone(timedelta(hours=7))

    def _get_mode_col(self):
        # Ưu tiên dùng bảng 'Mode' theo ERD
        if _house_col is not None: return _house_col.database.Mode
        return self.scenes_collection

    async def setup_scene(self, name, action, houseid="HS001", isactive=True):
        mode_col = self._get_mode_col()
        scene_data = {
            "houseid": houseid, "name": name, "action": action,
            "isactive": isactive, "createdat": datetime.now(timezone.utc)
        }
        await mode_col.update_one({"houseid": houseid, "name": name}, {"$set": scene_data}, upsert=True)
        return {"status": "success", "message": f"Đã lưu chế độ '{name}'"}

    async def get_scene_actions(self, name):
        mode_col = self._get_mode_col()
        scene = await mode_col.find_one({"name": name})
        return scene.get("action", []) if scene else None

async def get_servo_ids_for_house(house_col, houseid):
    if not house_col: return [6]
    house = await house_col.find_one({"_id.houseid": houseid})
    return [d["numberdevice"] for d in house.get("numberdevices", []) if d.get("type", "") == "servo"] if house else [6]

def apply_scene_to_status(current_status, actions, servo_ids=None):
    if servo_ids is None: servo_ids = [6]
    status_dict = {item[0]: item[1] for item in current_status}
    for act in actions:
        dev_id = act.get("numberdevice") or act.get("device_id")
        val = act.get("status") if "status" in act else act.get("value")
        if dev_id is not None and val is not None:
            if dev_id in servo_ids:
                try: val = 90 if int(val) >= 45 else 0
                except: val = 0
            status_dict[dev_id] = val
    return [[k, v] for k, v in status_dict.items()]

@router.post("/scenes")
async def create_scene(payload: dict = Body(...)):
    name, action, houseid = payload.get("name"), payload.get("action"), payload.get("houseid", "HS001")
    if not name or not action: return {"status": "Error"}, 400
    return await _scene_manager.setup_scene(name, action, houseid)

@router.post("/activate-scene")
async def activate_scene_endpoint(payload: dict = Body(...)):
    name, houseid = payload.get("name"), payload.get("houseid", "HS001")
    actions = await _scene_manager.get_scene_actions(name)
    if actions is None: return {"status": "Error"}, 404
    
    current = device_status_map.get(houseid, [])
    s_ids = await get_servo_ids_for_house(_house_col, houseid)
    new_status = apply_scene_to_status(current, actions, s_ids)
    device_status_map[houseid] = new_status
    
    # Ghi log cho từng thiết bị thay đổi trong kịch bản
    for act in actions:
        d_id = act.get("numberdevice")
        d_val = act.get("status")
        # Tìm type từ DB
        house = await _house_col.find_one({"_id.houseid": houseid})
        d_type = next((d["type"] for d in house["numberdevices"] if d["numberdevice"] == d_id), "unknown") if house else "unknown"
        await log_device_state(houseid, d_id, d_type, d_val, reason=f"Kích hoạt chế độ: {name}")

    return {"status": "Success", "new_commands": new_status}

@router.get("/scenes")
async def get_all_scenes(houseid: str = Query("HS001")):
    mode_col = _scene_manager._get_mode_col()
    res = await mode_col.find({"houseid": houseid}).to_list(100)
    return [{"modeid": str(i["_id"]), "name": i.get("name"), "action": i.get("action"), "isactive": i.get("isactive", True)} for i in res]

@router.get("/devices-info")
async def get_devices_info(houseid: str = Query("HS001")):
    devices_from_db = None
    if _house_col:
        house = await _house_col.find_one({"_id.houseid": {"$regex": f"^{houseid}$", "$options": "i"}})
        if house: devices_from_db = house.get("numberdevices")

    status_dict = {item[0]: item[1] for item in device_status_map.get(houseid, [])}
    result = []
    if devices_from_db:
        for dev in devices_from_db:
            num, d_type = dev.get("numberdevice"), dev.get("type", "unknown")
            curr = status_dict.get(num, dev.get("status"))
            st_txt = "Bật" if d_type in ("den", "denchongtrom") and curr else ("Mở" if d_type == "servo" and curr >= 45 else ("Chạy" if d_type == "quat" and curr > 0 else "Tắt / Đóng"))
            d_name = f"Đèn {num}" if d_type == "den" else (dev.get("name") or get_default_device_name(num, d_type))
            result.append({"numberdevice": num, "type": d_type, "name": d_name, "status": curr, "status_text": st_txt})
    return {"houseid": houseid, "devices": result}
