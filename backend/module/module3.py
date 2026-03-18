from datetime import datetime, timezone, timedelta

class SceneManager:
    def __init__(self, scenes_collection):
        self.scenes_collection = scenes_collection
        self.tz_vn = timezone(timedelta(hours=7))

    async def setup_scene(self, scene_name, actions, trigger_type="manual", trigger_time=""):
        """
        Lưu cấu hình kịch bản vào MongoDB.
        actions format: [{"device_id": 2, "value": True}, {"device_id": 6, "value": 50}]
        """
        scene_data = {
            "scene_name": scene_name,
            "trigger_type": trigger_type,
            "trigger_time": trigger_time,
            "actions": actions,
            "updated_at": datetime.now(self.tz_vn)
        }
        
        try:
            await self.scenes_collection.update_one(
                {"scene_name": scene_name},
                {"$set": scene_data},
                upsert=True
            )
            return {"status": "success", "message": f"Saved scene '{scene_name}'"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_scene_actions(self, scene_name):
        """
        Lấy danh sách lệnh từ kịch bản để server.py áp dụng.
        """
        try:
            scene = await self.scenes_collection.find_one({"scene_name": scene_name})
            if scene:
                return scene.get("actions", [])
            return None
        except Exception as e:
            print(f"Error fetching scene: {e}")
            return None

def apply_scene_to_status(current_status, actions):
    """
    Hàm helper: Trộn lệnh của kịch bản vào mảng device_status hiện tại.
    current_status: [[2, False], [6, 0]]
    actions: [{"device_id": 2, "value": True}, {"device_id": 5, "value": 90}]
    Trả về mảng status mới.
    """
    # Chuyển array of arrays -> dictionary để dễ replace
    status_dict = {item[0]: item[1] for item in current_status}
    
    for act in actions:
        dev_id = act.get("device_id")
        val = act.get("value")
        if dev_id is not None and val is not None:
            status_dict[dev_id] = val
            
    # Chuyển ngược lại thành list of lists
    new_status = [[k, v] for k, v in status_dict.items()]
    return new_status
