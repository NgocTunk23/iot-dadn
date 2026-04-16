from fastapi import APIRouter, Body, Query
from datetime import datetime, timezone, timedelta

# Khởi tạo Router cho Module 3
router = APIRouter(prefix="/api")

# --- ÁNH XẠ THIẾT BỊ (theo ERD: type = den, quat, servo, denchongtrom) ---
DEVICE_TYPE_MAP = {
    1: {"type": "denchongtrom", "name": "Đèn chống trộm"},
    2: {"type": "den", "name": "Đèn 2"},
    3: {"type": "den", "name": "Đèn 3"},
    4: {"type": "den", "name": "Đèn 4"},
    6: {"type": "servo", "name": "Cửa (Servo)"},
    7: {"type": "quat", "name": "Quạt"},
}

def format_device_status(numberdevice, status):
    """Chuyển status thô thành text có ý nghĩa dựa trên type thiết bị."""
    info = DEVICE_TYPE_MAP.get(numberdevice, {"type": "unknown", "name": f"Thiết bị {numberdevice}"})
    dev_type = info["type"]
    if dev_type in ("den", "denchongtrom"):
        status_text = "Bật" if status else "Tắt"
    elif dev_type == "servo":
        status_text = "Mở" if (isinstance(status, int) and status >= 45) else "Đóng"
    elif dev_type == "quat":
        status_text = "Chạy" if (isinstance(status, int) and status > 0) else "Tắt"
    else:
        status_text = str(status)
    return {**info, "numberdevice": numberdevice, "status": status, "status_text": status_text}

# Biến toàn cục cho thiết bị (được chia sẻ với server.py)
device_status = [[1, False], [2, False], [3, False], [4, False], [6, 0], [7, 0]]

_scene_manager = None
_house_col = None  # db.House — để đọc numberdevices theo houseid

def init_module3(manager, house_col=None):
    global _scene_manager, _house_col
    _scene_manager = manager
    _house_col = house_col

class SceneManager:
    def __init__(self, scenes_collection):
        self.scenes_collection = scenes_collection
        self.tz_vn = timezone(timedelta(hours=7))

    async def setup_scene(self, name, action, houseid="HS001", isactive=True):
        """
        Lưu cấu hình kịch bản vào MongoDB.
        action format: [{"numberdevice": 2, "status": True}, {"numberdevice": 6, "status": 50}]
        """
        scene_data = {
            "houseid": houseid,
            "name": name,
            "action": action,
            "isactive": isactive,
            "createdat": datetime.now(self.tz_vn)
        }
        
        try:
            await self.scenes_collection.update_one(
                {"name": name},
                {"$set": scene_data},
                upsert=True
            )
            return {"status": "success", "message": f"Saved scene '{name}'"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_scene_actions(self, name):
        """
        Lấy danh sách lệnh từ kịch bản để server.py áp dụng.
        """
        try:
            # Fallback cho database cũ nếu tìm name không thấy thì thử scene_name
            scene = await self.scenes_collection.find_one({"name": name})
            if not scene:
                scene = await self.scenes_collection.find_one({"scene_name": name})
                
            if scene:
                return scene.get("action", scene.get("actions", []))
            return None
        except Exception as e:
            print(f"Error fetching scene: {e}")
            return None

def apply_scene_to_status(current_status, actions):
    """
    Hàm helper: Trộn lệnh của kịch bản vào mảng device_status hiện tại.
    """
    status_dict = {item[0]: item[1] for item in current_status}
    
    for act in actions:
        # Hỗ trợ cả 2 format database cũ và mới
        dev_id = act.get("device_id", act.get("numberdevice"))
        val = act.get("value", act.get("status"))
        if dev_id is not None and val is not None:
            # Chuẩn hóa Servo (ID 6) về 0/90 để đảm bảo tính nhất quán
            if dev_id == 6:
                try:
                    val = 90 if int(val) >= 45 else 0
                except (ValueError, TypeError):
                    val = 0
            status_dict[dev_id] = val
            
    new_status = [[k, v] for k, v in status_dict.items()]
    return new_status

# --- CÁC ENDPOINT API CỦA MODULE 3 ---

@router.post("/scenes")
async def create_scene(payload: dict = Body(...)):
    name = payload.get("name")
    action = payload.get("action")
    houseid = payload.get("houseid", "HS001")
    isactive = payload.get("isactive", True)
    
    if not name or not action:
         return {"status": "Error", "message": "Missing name or action"}, 400
         
    res = await _scene_manager.setup_scene(name, action, houseid, isactive)
    if res["status"] == "success":
        return res
    return res, 500

@router.post("/activate-scene")
async def activate_scene_endpoint(payload: dict = Body(...)):
    global device_status
    name = payload.get("name")
    if not name:
        return {"status": "Error", "message": "Missing name"}, 400
        
    actions = await _scene_manager.get_scene_actions(name)
    if actions is None:
        return {"status": "Error", "message": "Scene not found"}, 404
        
    device_status = apply_scene_to_status(device_status, actions)
    print(f"--- Kích hoạt kịch bản '{name}'. Lệnh mới: {device_status} ---")
    return {"status": "Success", "new_commands": device_status}

@router.post("/deactivate-scene")
async def deactivate_scene_endpoint(payload: dict = Body(...)):
    global device_status
    try:
        name = payload.get("name")
        if not name:
            return {"status": "Error", "message": "Missing name"}, 400
            
        actions = await _scene_manager.get_scene_actions(name)
        if actions is None:
            return {"status": "Error", "message": "Scene not found"}, 404
            
        reversed_actions = []
        for item in actions:
            dev_id = None
            state = None
            if isinstance(item, list) and len(item) >= 2:
                dev_id = item[0]
                state = item[1]
            elif isinstance(item, dict):
                dev_id = item.get("numberdevice", item.get("device_id"))
                state = item.get("status", item.get("value"))

            if dev_id is None or state is None:
                continue

            if isinstance(state, bool) and state == True:
                reversed_actions.append({"device_id": dev_id, "value": False})
            elif isinstance(state, int) and not isinstance(state, bool) and state > 0:
                reversed_actions.append({"device_id": dev_id, "value": 0})

        device_status = apply_scene_to_status(device_status, reversed_actions)
        print(f"--- Tắt kịch bản '{name}'. Lệnh mới: {device_status} ---")
        return {"status": "Success", "new_commands": device_status}

    except Exception as e:
        print(f"[LỖI DEACTIVATE-SCENE CRASH]: {e}")
        return {"status": "Error", "message": f"Server Error: {str(e)}"}, 500

@router.get("/scenes")
async def get_all_scenes():
    try:
        cursor = _scene_manager.scenes_collection.find({})
        results = await cursor.to_list(length=100)
        formatted_results = []
        for item in results:
            formatted_results.append({
                "modeid": str(item.get("_id")),
                "houseid": item.get("houseid", "HS001"),
                "name": item.get("name", item.get("scene_name", "Unknown")),
                "action": item.get("action", item.get("actions", [])),
                "isactive": item.get("isactive", True),
                "createdat": str(item.get("createdat", item.get("updated_at", "")))
            })
        return formatted_results
    except Exception as e:
        return {"error": str(e)}

@router.delete("/scenes")
async def delete_scene(name: str = Query(..., alias="name")):
    try:
        result = await _scene_manager.scenes_collection.delete_one({"name": name})
        if result.deleted_count == 0:
            result = await _scene_manager.scenes_collection.delete_one({"scene_name": name})
        if result.deleted_count > 0:
            return {"status": "Deleted", "name": name}
        return {"status": "Not Found"}
    except Exception as e:
        return {"error": str(e)}

# --- ENDPOINT THÔNG TIN THIẾT BỊ (Module 3) ---

@router.get("/devices-info")
async def get_devices_info(houseid: str = Query("HS001")):
    """
    Trả về danh sách thiết bị kèm type, name, status, status_text.
    Ưu tiên đọc từ House collection (dynamic), fallback về DEVICE_TYPE_MAP.
    """
    devices_from_db = None

    # Cố đọc từ MongoDB House collection (cấu trúc _id compound)
    if _house_col is not None:
        try:
            house = await _house_col.find_one({"_id.houseid": houseid})
            if house and "numberdevices" in house:
                devices_from_db = house["numberdevices"]
        except Exception as e:
            print(f"[MODULE3] Lỗi đọc House DB: {e}")

    result = []
    if devices_from_db:
        # Dynamic từ DB
        status_dict = {item[0]: item[1] for item in device_status}
        for dev in devices_from_db:
            num = dev.get("numberdevice")
            dev_type = dev.get("type", "unknown")
            # Lấy status hiện tại từ device_status (realtime), fallback về DB
            current_status = status_dict.get(num, dev.get("status"))
            # Format status text theo type
            if dev_type in ("den", "denchongtrom"):
                status_text = "Bật" if current_status else "Tắt"
            elif dev_type == "servo":
                status_text = "Mở" if (isinstance(current_status, int) and current_status >= 45) else "Đóng"
            elif dev_type == "quat":
                status_text = "Chạy" if (isinstance(current_status, int) and current_status > 0) else "Tắt"
            else:
                status_text = str(current_status)
            result.append({
                "numberdevice": num,
                "type": dev_type,
                "name": DEVICE_TYPE_MAP.get(num, {}).get("name", f"Thiết bị {num}"),
                "status": current_status,
                "status_text": status_text,
            })
    else:
        # Fallback: dùng DEVICE_TYPE_MAP + device_status hiện tại
        for item in device_status:
            result.append(format_device_status(item[0], item[1]))

    return {"houseid": houseid, "devices": result}
