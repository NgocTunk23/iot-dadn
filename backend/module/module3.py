from fastapi import APIRouter, Body, Query
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pydantic.v1.json import ENCODERS_BY_TYPE

# Patch cho ObjectId
ENCODERS_BY_TYPE[ObjectId] = str

# Router KHÔNG có prefix ở đây (sẽ được định nghĩa ở server.py)
router = APIRouter()

def get_default_device_name(dev_num, dev_type):
    if dev_type == "denchongtrom": return "Đèn báo trộm" 
    if dev_type == "den": return f"Đèn {dev_num}"
    if dev_type == "servo": return "Cửa (Servo)"
    if dev_type == "quat": return "Quạt"
    return f"Thiết bị {dev_num}"

device_status_map = {}
_scene_manager = None
_house_col = None

def init_module3(manager, house_col=None):
    global _scene_manager, _house_col
    _scene_manager = manager
    _house_col = house_col

async def log_device_state(houseid, numberdevice, dev_type, new_status, old_status=False, reason="Điều khiển"):
    if _house_col is None: return
    try:
        device_log_col = _house_col.database.Device_log
        now_utc = datetime.now(timezone.utc)
        timestamp_str = now_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        log_id = f"{timestamp_str}{numberdevice}_{houseid}"
        
        # Đổi "status" thành "old_status" và "new_status"
        log_entry = {
            "_id": log_id, "time": now_utc, "houseid": houseid, 
            "numberdevice": numberdevice, "type": dev_type, 
            "old_status": old_status, 
            "new_status": new_status, 
            "reason": reason
        }
        await device_log_col.update_one({"_id": log_id}, {"$set": log_entry}, upsert=True)
    except Exception as e: print(f"[MODULE3] Lỗi ghi log: {e}")

# --- API ENDPOINTS (Đường dẫn tương đối) ---

@router.post("/login")
async def login_api_override(payload: dict = Body(...)):
    if _house_col is None: return {"success": False, "message": "Backend chưa sẵn sàng (Thiếu Database)"}
    users_collection = _house_col.database.User
    username_input, password, house_id = payload.get("username"), payload.get("password"), payload.get("houseid")
    if not username_input or not password: return {"success": False, "message": "Thiếu thông tin"}
    try:
        user = await users_collection.find_one({"$or": [{"email": username_input}, {"_id": username_input}]})
        if not user or user.get("password") != password: return {"success": False, "message": "Sai tài khoản/mật khẩu"}
        actual_username = user.get("_id")
        # Sử dụng regex để kiểm tra house_id không phân biệt hoa thường
        house = await _house_col.find_one({
            "_id.houseid": {"$regex": f"^{house_id}$", "$options": "i"}, 
            "_id.username": actual_username
        })
        if not house: return {"success": False, "message": "House ID không thuộc tài khoản này"}
        
        # Đảm bảo trả về đúng houseid từ DB (để đồng nhất hoa thường)
        db_house_id = house["_id"]["houseid"]
        return {"success": True, "message": "Thành công", "user": {k:v for k,v in user.items() if k!="password"}, "houseid": db_house_id}
    except Exception as e: return {"success": False, "message": f"Lỗi: {str(e)}"}

@router.post("/control")
async def update_control_override(payload: dict = Body(...)):
    if _house_col is None: return {"status": "Error", "message": "Database chưa sẵn sàng"}, 500
    house_id = payload.get("houseid", "HS001")
    new_cmds = payload.get("commands")
    if not new_cmds: return {"status": "Error", "message": "Thiếu lệnh"}, 400
    try:
        house = await _house_col.find_one({"_id.houseid": house_id})
        dev_map = {d["numberdevice"]: d for d in house.get("numberdevices", [])} if house else {}

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Lấy trạng thái hiện tại (cũ) chuyển thành dict để dễ tra cứu TRƯỚC KHI ghi đè
        old_status_list = device_status_map.get(house_id, [])
        old_status_dict = {item[0]: item[1] for item in old_status_list}
        
        device_status_map[house_id] = new_cmds
        for cmd in new_cmds:
            d_id, d_val = cmd[0], cmd[1]
            d_type = dev_map.get(d_id, {}).get("type", "unknown")
            
            # Lấy ra trạng thái cũ tương ứng của thiết bị này
            old_val = old_status_dict.get(d_id, False) 
            
            # Truyền old_status vào hàm
            await log_device_state(house_id, d_id, d_type, new_status=d_val, old_status=old_val, reason="Người dùng điều khiển thủ công")
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            
        from module.module2 import sync_device_state
        await sync_device_state(_house_col, house_id, new_cmds)
        return {"status": "Updated"}
    except Exception as e: return {"status": "Error", "message": str(e)}, 500

class SceneManager:
    def __init__(self, scenes_collection):
        self.scenes_collection = scenes_collection
    def _get_mode_col(self):
        return _house_col.database.Mode if _house_col is not None else self.scenes_collection
    async def setup_scene(self, name, action, houseid="HS001", isactive=True):
        mode_col = self._get_mode_col()
        await mode_col.update_one({"houseid": houseid, "name": name}, {"$set": {"houseid": houseid, "name": name, "action": action, "isactive": isactive, "createdat": datetime.now(timezone.utc)}}, upsert=True)
        return {"status": "success"}
    async def get_scene_actions(self, name):
        scene = await self._get_mode_col().find_one({"name": name})
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
    if not _scene_manager: return {"status": "Error"}, 500
    return await _scene_manager.setup_scene(payload.get("name"), payload.get("action"), payload.get("houseid", "HS001"))

@router.post("/activate-scene")
async def activate_scene_endpoint(payload: dict = Body(...)):
    if not _scene_manager: return {"status": "Error"}, 500
    name, houseid = payload.get("name"), payload.get("houseid", "HS001")
    actions = await _scene_manager.get_scene_actions(name)
    if actions is None: return {"status": "Error"}, 404

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    current = device_status_map.get(houseid, [])
    
    # Lưu lại trạng thái cũ thành dict để tra cứu dễ dàng
    old_status_dict = {item[0]: item[1] for item in current}
    
    s_ids = await get_servo_ids_for_house(_house_col, houseid)
    new_status = apply_scene_to_status(current, actions, s_ids)
    device_status_map[houseid] = new_status
    house = await _house_col.find_one({"_id.houseid": houseid})
    dev_map = {d["numberdevice"]: d["type"] for d in house.get("numberdevices", [])} if house else {}
    for act in actions:
        d_id = act.get("numberdevice")
        d_val = act.get("status")
        
        # Lấy trạng thái cũ của thiết bị này
        old_val = old_status_dict.get(d_id, False)
        
        # Truyền old_status vào
        await log_device_state(houseid, d_id, dev_map.get(d_id, "unknown"), new_status=d_val, old_status=old_val, reason=f"Chế độ: {name}")
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    return {"status": "Success", "new_commands": new_status}

@router.get("/scenes")
async def get_all_scenes(houseid: str = Query("HS001")):
    if not _scene_manager: return []
    res = await _scene_manager._get_mode_col().find({"houseid": houseid}).to_list(100)
    return [{"modeid": str(i["_id"]), "name": i.get("name"), "action": i.get("action"), "isactive": i.get("isactive", True)} for i in res]

@router.get("/devices-info")
async def get_devices_info(houseid: str = Query("HS001")):
    if _house_col is None: return {"houseid": houseid, "devices": []}
    house = await _house_col.find_one({"_id.houseid": {"$regex": f"^{houseid}$", "$options": "i"}})
    devices_from_db = house.get("numberdevices") if house else []
    status_dict = {item[0]: item[1] for item in device_status_map.get(houseid, [])}
    result = []
    for dev in devices_from_db:
        num, d_type = dev.get("numberdevice"), dev.get("type", "unknown")
        curr = status_dict.get(num, dev.get("status"))
        st_txt = "Bật" if d_type in ("den", "denchongtrom") and curr else ("Mở" if d_type == "servo" and curr >= 45 else ("Chạy" if d_type == "quat" and curr > 0 else "Tắt / Đóng"))
        d_name = f"Đèn {num}" if d_type == "den" else (dev.get("name") or get_default_device_name(num, d_type))
        result.append({"numberdevice": num, "type": d_type, "name": d_name, "status": curr, "status_text": st_txt})
    return {"houseid": houseid, "devices": result}
