from fastapi import APIRouter, Body, Query
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pydantic.v1.json import ENCODERS_BY_TYPE
ENCODERS_BY_TYPE[ObjectId] = str

# Khởi tạo Router cho Module 3 (Xử lý phẳng để tránh lỗi 404 trên Windows)
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

class SceneManager:
    def __init__(self, scenes_collection):
        self.scenes_collection = scenes_collection
        self.tz_vn = timezone(timedelta(hours=7))

    async def setup_scene(self, name, action, houseid="HS001", isactive=True):
        if _house_col:
            house_config = await _house_col.find_one({"_id.houseid": houseid})
            if house_config:
                house_devices = house_config.get("numberdevices", [])
                dev_map = {d.get("numberdevice"): d for d in house_devices}
                for item in action:
                    dev_num = item.get("numberdevice")
                    if "type" not in item:
                        item["type"] = dev_map.get(dev_num, {}).get("type", "unknown")

        scene_data = {
            "houseid": houseid,
            "name": name,
            "action": action,
            "isactive": isactive,
            "createdat": datetime.now(timezone.utc)
        }
        await self.scenes_collection.update_one(
            {"houseid": houseid, "name": name},
            {"$set": scene_data},
            upsert=True
        )
        return {"status": "success", "message": f"Saved scene '{name}'"}

    async def get_scene_actions(self, name):
        try:
            scene = await self.scenes_collection.find_one({"name": name})
            if not scene:
                scene = await self.scenes_collection.find_one({"scene_name": name})
            if scene:
                return scene.get("action", scene.get("actions", []))
            return None
        except Exception:
            return None

async def get_servo_ids_for_house(house_col, houseid):
    if not house_col: return [6]
    try:
        house = await house_col.find_one({"_id.houseid": houseid})
        if house and "numberdevices" in house:
            return [d["numberdevice"] for d in house["numberdevices"] if d.get("type", "") == "servo"]
    except Exception: pass
    return [6]

def apply_scene_to_status(current_status, actions, servo_ids=None):
    if servo_ids is None: servo_ids = [6]
    status_dict = {item[0]: item[1] for item in current_status}
    for act in actions:
        dev_id = act.get("device_id", act.get("numberdevice"))
        val = act.get("value", act.get("status"))
        if dev_id is not None and val is not None:
            if dev_id in servo_ids:
                try: val = 90 if int(val) >= 45 else 0
                except: val = 0
            status_dict[dev_id] = val
    return [[k, v] for k, v in status_dict.items()]

# --- ENDPOINTS ---

@router.post("/scenes")
async def create_scene(payload: dict = Body(...)):
    name, action = payload.get("name"), payload.get("action")
    houseid, isactive = payload.get("houseid", "HS001"), payload.get("isactive", True)
    if not name or not action: return {"status": "Error"}, 400
    return await _scene_manager.setup_scene(name, action, houseid, isactive)

@router.post("/activate-scene")
async def activate_scene_endpoint(payload: dict = Body(...)):
    name, houseid = payload.get("name"), payload.get("houseid", "HS001")
    if not name: return {"status": "Error"}, 400
    actions = await _scene_manager.get_scene_actions(name)
    if actions is None: return {"status": "Error"}, 404
    current = device_status_map.get(houseid, [])
    s_ids = await get_servo_ids_for_house(_house_col, houseid)
    device_status_map[houseid] = apply_scene_to_status(current, actions, s_ids)
    return {"status": "Success", "new_commands": device_status_map[houseid]}

@router.post("/deactivate-scene")
async def deactivate_scene_endpoint(payload: dict = Body(...)):
    name, houseid = payload.get("name"), payload.get("houseid", "HS001")
    if not name: return {"status": "Error"}, 400
    actions = await _scene_manager.get_scene_actions(name)
    if actions is None: return {"status": "Error"}, 404
    rev = []
    for item in actions:
        d_id = item.get("numberdevice", item.get("device_id")) if isinstance(item, dict) else (item[0] if isinstance(item, list) else None)
        st = item.get("status", item.get("value")) if isinstance(item, dict) else (item[1] if isinstance(item, list) else None)
        if d_id is not None and st is not None:
            if isinstance(st, bool) and st: rev.append({"device_id": d_id, "value": False})
            elif isinstance(st, int) and not isinstance(st, bool) and st > 0: rev.append({"device_id": d_id, "value": 0})
    current = device_status_map.get(houseid, [])
    s_ids = await get_servo_ids_for_house(_house_col, houseid)
    device_status_map[houseid] = apply_scene_to_status(current, rev, s_ids)
    return {"status": "Success", "new_commands": device_status_map[houseid]}

@router.get("/scenes")
async def get_all_scenes(houseid: str = Query("HS001")):
    cursor = _scene_manager.scenes_collection.find({"houseid": houseid})
    res = await cursor.to_list(100)
    return [{"modeid": str(i["_id"]), "houseid": i.get("houseid", "HS001"), "name": i.get("name", "Unknown"), "action": i.get("action", []), "isactive": i.get("isactive", True), "createdat": str(i.get("createdat", ""))} for i in res]

@router.delete("/scenes")
async def delete_scene(name: str = Query(..., alias="name")):
    res = await _scene_manager.scenes_collection.delete_one({"name": name})
    return {"status": "Deleted" if res.deleted_count > 0 else "Not Found"}

@router.get("/devices-info")
async def get_devices_info(houseid: str = Query("HS001")):
    """Trả về danh sách thiết bị kèm linh hoạt ID 6/7 và quy ước tên Đèn."""
    devices_from_db = None
    if _house_col is not None:
        try:
            house = await _house_col.find_one({"_id.houseid": {"$regex": f"^{houseid}$", "$options": "i"}})
            if house and "numberdevices" in house:
                devices_from_db = house["numberdevices"]
        except Exception: pass

    realtime_list = []
    for k, v in device_status_map.items():
        if k.lower() == houseid.lower():
            realtime_list = v
            break
    status_dict = {item[0]: item[1] for item in realtime_list}

    result = []
    if devices_from_db:
        for dev in devices_from_db:
            num, d_type = dev.get("numberdevice"), dev.get("type", "unknown")
            curr = status_dict.get(num, dev.get("status"))
            if d_type in ("den", "denchongtrom"): st_txt = "Bật" if curr else "Tắt"
            elif d_type == "servo": st_txt = "Mở" if (isinstance(curr, int) and curr >= 45) else "Đóng"
            elif d_type == "quat": st_txt = "Chạy" if (isinstance(curr, int) and curr > 0) else "Tắt"
            else: st_txt = str(curr)

            if d_type == "den": d_name = f"Đèn {num}"
            else: d_name = dev.get("name") or get_default_device_name(num, d_type)

            result.append({"numberdevice": num, "type": d_type, "name": d_name, "status": curr, "status_text": st_txt})
    else:
        # Fallback ID 1-7
        seen = set()
        for item in realtime_list:
            result.append(format_device_status(item[0], item[1]))
            seen.add(item[0])
        for mid in [1, 2, 3, 4, 6, 7]:
            if mid not in seen:
                result.append({"numberdevice": mid, "name": f"Thiết bị {mid}", "type": "unknown", "status": 0, "status_text": "Tắt"})

    return {"houseid": houseid, "devices": result}
