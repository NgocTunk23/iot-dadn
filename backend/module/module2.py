
from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
from typing import Any
import re
from module.notifiers import dispatch_all_channels

router = APIRouter(prefix="/api", tags=["Module 2 – Safety & Automation"])

VN_TZ = timezone(timedelta(hours=7))

DEFAULT_THRESHOLDS = {
    "temp":  {"min": 0,   "max": 40},
    "humi":  {"min": 20,  "max": 80},
    "light": {"min": 0,   "max": 90},
}

DEVICE_NAMES = {
    1: "Đèn 1 (PIR)", 2: "Đèn 2", 3: "Đèn 3",
    4: "Đèn 4",       5: "Đèn 5", 6: "Servo (Cửa)", 7: "Quạt",
}



class ThresholdManager:
    def __init__(self, collection):
        self.col = collection

    @staticmethod
    def validate(sensor: str, min_val: float, max_val: float) -> dict:
        PHYSICAL_LIMITS = {
            "temp": (-50, 500), "humi": (0, 100), "light": (0, 100),
        }
        if sensor not in PHYSICAL_LIMITS:
            return {"ok": False, "message": f"Cảm biến '{sensor}' không tồn tại."}
        lo, hi = PHYSICAL_LIMITS[sensor]
        try:
            min_val, max_val = float(min_val), float(max_val)
        except (TypeError, ValueError):
            return {"ok": False, "message": "Giá trị ngưỡng phải là số."}
        if not (lo <= min_val <= hi) or not (lo <= max_val <= hi):
            return {"ok": False, "message": f"Giá trị vượt phạm vi vật lý ({lo}–{hi})."}
        if min_val > max_val:
            return {"ok": False, "message": "Lỗi logic: Min không được lớn hơn Max."}
        return {"ok": True}

    async def get_thresholds(self, houseid: str) -> dict:
        doc = await self.col.find_one({"_id": houseid})
        if doc:
            doc.pop("_id", None)
            doc.pop("updated_at", None)
            return doc
        return dict(DEFAULT_THRESHOLDS)

    async def set_threshold(self, houseid: str, sensor: str,
                             min_val: float, max_val: float) -> dict:
        check = self.validate(sensor, min_val, max_val)
        if not check["ok"]:
            return {"status": "error", "message": check["message"]}
        await self.col.update_one(
            {"_id": houseid},
            {"$set": {
                sensor: {"min": float(min_val), "max": float(max_val)},
                "updated_at": datetime.now(VN_TZ),
            }},
            upsert=True,
        )
        return {"status": "success", "message": "Cập nhật ngưỡng thành công."}

    async def reset_to_default(self, houseid: str) -> dict:
        await self.col.update_one(
            {"_id": houseid},
            {"$set": {**DEFAULT_THRESHOLDS, "updated_at": datetime.now(VN_TZ)}},
            upsert=True,
        )
        return {"status": "success", "thresholds": DEFAULT_THRESHOLDS}


class NotificationChannelManager:
    CHANNELS = ("email", "telegram", "app")

    def __init__(self, channel_col, house_col=None):
        self.col       = channel_col   # db.notification_channels
        self.house_col = house_col     # db.House

    @staticmethod
    def validate_contact(channel: str, info: dict) -> dict:
        """
        Chỉ validate khi field được cung cấp VÀ có giá trị (không rỗng).
        Cho phép lưu khi chỉ muốn toggle enabled mà chưa nhập thông tin.
        """
        if channel == "email":
            address = info.get("address", "")
            if address and not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", str(address)):
                return {"ok": False, "message": "Địa chỉ email không hợp lệ."}
        elif channel == "telegram":
            bot_token = info.get("bot_token", "")
            chat_id   = info.get("chat_id", "")
            if bot_token and len(str(bot_token).strip()) < 10:
                return {"ok": False, "message": "Bot token không hợp lệ (quá ngắn)."}
        return {"ok": True}

    async def get_channels(self, houseid: str) -> dict:
        """
        Trả về cấu hình kênh.
        Merge: House defaults (emailtowarning/teletowarning) → notification_channels override.
        """
        result = {
            "email":    {"enabled": False},
            "telegram": {"enabled": False},
            "app":      {"enabled": True},
        }
        if self.house_col is not None:
            house = await self.house_col.find_one({"houseid": houseid})
            if house:
                if house.get("emailtowarning"):
                    result["email"]["address"] = house["emailtowarning"]
                tele = house.get("teletowarning", {})
                if tele.get("token"):
                    result["telegram"]["bot_token"] = tele["token"]
                if tele.get("id"):
                    result["telegram"]["chat_id"] = tele["id"]

        doc = await self.col.find_one({"_id": houseid})
        if doc:
            doc.pop("_id", None)
            for ch, val in doc.items():
                if ch in result and isinstance(val, dict):
                    result[ch].update(val)
        return result

    async def update_channel(self, houseid: str, channel: str,
                              enabled: bool, contact_info: dict = None) -> dict:
        if channel not in self.CHANNELS:
            return {"status": "error", "message": f"Kênh '{channel}' không được hỗ trợ."}

        filtered_info = contact_info or {}
        check = self.validate_contact(channel, filtered_info)
        if not check["ok"]:
            return {"status": "error", "message": check["message"]}

        update_data: dict[str, Any] = {f"{channel}.enabled": enabled}
        for k, v in filtered_info.items():
            update_data[f"{channel}.{k}"] = v

        await self.col.update_one(
            {"_id": houseid}, {"$set": update_data}, upsert=True
        )
        return {"status": "success", "message": "Cập nhật thành công."}



class AutomationRuleManager:
    OPERATORS = {"gt": ">", "lt": "<", "gte": ">=", "lte": "<=", "eq": "=="}

    def __init__(self, collection):
        self.col = collection  # db.Scenario

    @staticmethod
    def _check_condition(condition: dict, sensor_data: dict) -> bool:
        """
        condition format lưu trong DB: {sensor, op, value}
        (lưu nguyên dạng từ frontend, không chuyển đổi sang lower/upper)
        """
        sensor  = condition.get("sensor")
        op      = condition.get("op")
        value   = condition.get("value")
        current = sensor_data.get(sensor)
        if current is None or op not in AutomationRuleManager.OPERATORS:
            return False
        ops = {
            "gt":  lambda a, b: a > b,
            "lt":  lambda a, b: a < b,
            "gte": lambda a, b: a >= b,
            "lte": lambda a, b: a <= b,
            "eq":  lambda a, b: a == b,
        }
        try:
            return ops[op](float(current), float(value))
        except (TypeError, ValueError):
            return False

    async def add_rule(self, houseid: str, name: str,
                        condition: dict, actions: list,
                        enabled: bool = True) -> dict:
        if not name:
            return {"status": "error", "message": "Thiếu tên kịch bản."}
        if not condition or not all(k in condition for k in ("sensor", "op", "value")):
            return {"status": "error", "message": "Điều kiện không hợp lệ."}
        if not actions:
            return {"status": "error", "message": "Thiếu hành động phản hồi."}
        if condition.get("op") not in self.OPERATORS:
            return {"status": "error", "message": "Toán tử không được hỗ trợ."}

        try:
            condition = {**condition, "value": float(condition["value"])}
        except (TypeError, ValueError):
            return {"status": "error", "message": "Giá trị điều kiện phải là số."}

        scenario_id = f"{houseid}_{name.replace(' ', '_')}"
        doc = {
            "_id":        scenario_id,
            "scenarioid": scenario_id,
            "houseid":    houseid,
            "name":       name,
            "condition":  condition,   # {sensor, op, value} — lưu nguyên
            "action":     actions,     # ERD field "action" (số ít)
            "isactive":   enabled,     # ERD field "isactive"
            "createdat":  datetime.now(VN_TZ),
        }
        await self.col.update_one({"_id": scenario_id}, {"$set": doc}, upsert=True)
        return {"status": "success",
                "message": "Tạo kịch bản thành công.",
                "scenarioid": scenario_id}

    async def delete_rule(self, houseid: str, name: str) -> dict:
        scenario_id = f"{houseid}_{name.replace(' ', '_')}"
        result = await self.col.delete_one({"_id": scenario_id})
        if result.deleted_count:
            return {"status": "success", "message": "Đã xóa kịch bản."}
        return {"status": "error", "message": "Kịch bản không tồn tại."}

    async def toggle_rule(self, houseid: str, name: str, enabled: bool) -> dict:
        scenario_id = f"{houseid}_{name.replace(' ', '_')}"
        result = await self.col.update_one(
            {"_id": scenario_id}, {"$set": {"isactive": enabled}}
        )
        if result.matched_count:
            return {"status": "success"}
        return {"status": "error", "message": "Kịch bản không tồn tại."}

    async def get_rules(self, houseid: str) -> list:
        cursor = self.col.find({"houseid": houseid})
        rules  = await cursor.to_list(length=200)
        output = []
        for r in rules:
            action_list = r.get("action", [])
            scenario_id = str(r.get("_id", ""))
            output.append({
                "_id":        scenario_id,
                "scenarioid": scenario_id,
                "houseid":    r.get("houseid"),
                "name":       r.get("name"),
                "condition":  r.get("condition", {}),
                "action":     action_list,
                "actions":    action_list,
                "isactive":   r.get("isactive", True),
                "enabled":    r.get("isactive", True),
                "createdat":  str(r.get("createdat", "")),
            })
        return output

    async def evaluate_and_apply(self, houseid: str, sensor_data: dict,
                                  current_device_status: list) -> tuple:
        cursor = self.col.find({"houseid": houseid, "isactive": True})
        rules  = await cursor.to_list(length=200)

        new_status = [list(item) for item in current_device_status]
        before     = {item[0]: item[1] for item in current_device_status}
        triggered_rules = []

        for rule in rules:
            cond = rule.get("condition", {})
            if not self._check_condition(cond, sensor_data):
                continue

            rule_changes = []
            for action in rule.get("action", []):
                dev_id = int(action.get("numberdevice"))
                stat   = action.get("status")
                for item in new_status:
                    if item[0] == dev_id:
                        old_val = before.get(dev_id)
                        item[1] = stat
                        rule_changes.append({
                            "device_id":   dev_id,
                            "device_name": DEVICE_NAMES.get(dev_id, f"Thiết bị {dev_id}"),
                            "from":    old_val,
                            "to":      stat,
                            "changed": old_val != stat,
                        })
                        break

            triggered_rules.append({
                "rule_name": rule.get("name"),
                "changes":   rule_changes,
            })
            print(f"[MODULE2] Kích hoạt kịch bản: '{rule.get('name')}'")

        return new_status, triggered_rules


class DangerChecker:
    @staticmethod
    def check(sensor_data: dict, thresholds: dict) -> dict:
        violations = []
        for sensor, limits in thresholds.items():
            raw = sensor_data.get(sensor)
            if raw is None:
                continue
            try:
                val = float(raw)
            except (TypeError, ValueError):
                continue
            lo = limits.get("min", DEFAULT_THRESHOLDS.get(sensor, {}).get("min", 0))
            hi = limits.get("max", DEFAULT_THRESHOLDS.get(sensor, {}).get("max", 100))
            if val > hi:
                violations.append({"sensor": sensor, "value": val,
                                    "threshold": "max", "limit": hi})
            elif val < lo:
                violations.append({"sensor": sensor, "value": val,
                                    "threshold": "min", "limit": lo})
        return {"is_danger": len(violations) > 0, "violations": violations}



class AlertDispatcher:
    def __init__(self, danger_col, channel_col):
        self.danger_col  = danger_col   # db.Danger_log
        self.channel_col = channel_col  # db.notification_channels

    async def dispatch(self, houseid: str, violations: list,
                       sensor_data: dict, device_status_ref: list,
                       triggered_rules: list = None) -> dict:
        now = datetime.now(VN_TZ)

        danger_log = {
            "_id":     now,
            "time":    now,
            "houseid": houseid,
            "type":    "Vượt ngưỡng an toàn",
            "value": {
                "temp":  sensor_data.get("temp"),
                "humi":  sensor_data.get("humi"),
                "light": sensor_data.get("light"),
            },
            "violations":      violations,
            "triggered_rules": triggered_rules or [],
        }
        try:
            await self.danger_col.insert_one(danger_log)
        except Exception as e:
            print(f"[MODULE2] Lỗi ghi Danger_log: {e}")

        channels_doc = await self.channel_col.find_one({"_id": houseid}) or {}
        print(f"[MODULE2] Channels config: {channels_doc}")

        try:
            results = await dispatch_all_channels(
                houseid, violations, sensor_data, channels_doc,
                triggered_rules=triggered_rules or [],
            )
            sent_channels = [r.get("channel") for r in results if r.get("ok")]
            failed        = [r for r in results if not r.get("ok")]
            if sent_channels:
                print(f"[MODULE2] ✅ Gửi thông báo qua: {sent_channels}")
            if failed:
                print(f"[MODULE2] ❌ Gửi thất bại: {failed}")
        except Exception as e:
            print(f"[MODULE2] Lỗi dispatch: {e}")
            sent_channels = []

        return {"dispatched": True, "sent_channels": sent_channels}

    async def auto_stop_alert(self, houseid: str,
                               device_status_ref: list, is_danger: bool):
        if not is_danger:
            print(f"[MODULE2] An toàn – Yolobit tắt nhạc sau 15s.")

async def process_danger_and_rules(app, payload: dict, house_id: str) -> tuple:
    sensor_data = {
        "temp":  payload.get("temp",  0),
        "humi":  payload.get("humi",  0),
        "light": payload.get("light", 0),
    }

    threshold_mgr    = app.state.threshold_mgr
    rule_mgr         = app.state.rule_mgr
    alert_dispatcher = app.state.alert_dispatcher

    thresholds = await threshold_mgr.get_thresholds(house_id)
    result = DangerChecker.check(sensor_data, thresholds)
    is_danger = result["is_danger"]
    app.state.is_danger_global = is_danger

    new_status, triggered_rules = await rule_mgr.evaluate_and_apply(
        house_id, sensor_data, app.state.device_status
    )
    app.state.device_status = new_status

    if is_danger:
        has_changes = any(
            c.get("changed")
            for rule in triggered_rules
            for c in rule.get("changes", [])
        )
        if triggered_rules and not has_changes:
            triggered_rules = [{
                "rule_name": triggered_rules[0]["rule_name"],
                "changes": [{
                    "device_name": "Tất cả thiết bị",
                    "changed":     False,
                    "note":        "Không có thay đổi so với trạng thái hiện tại",
                }],
            }]

        await alert_dispatcher.dispatch(
            house_id, result["violations"], sensor_data,
            app.state.device_status,
            triggered_rules=triggered_rules,
        )
    else:
        await alert_dispatcher.auto_stop_alert(
            house_id, app.state.device_status, False
        )

    return is_danger, new_status

def init_module2(app, threshold_mgr, channel_mgr, rule_mgr,
                 alert_dispatcher, danger_col, notif_channel_col):
    app.state.threshold_mgr     = threshold_mgr
    app.state.channel_mgr       = channel_mgr
    app.state.rule_mgr          = rule_mgr
    app.state.alert_dispatcher  = alert_dispatcher
    app.state.danger_collection = danger_col
    app.state.notif_channel_col = notif_channel_col
    print("[MODULE2] init_module2 hoàn tất.")


@router.get("/notification-channels")
async def get_notification_channels(request: Request, houseid: str = "HS001"):
    mgr = request.app.state.channel_mgr
    return await mgr.get_channels(houseid)


@router.post("/notification-channels")
async def update_notification_channel(request: Request, payload: dict = Body(...)):
    mgr          = request.app.state.channel_mgr
    houseid      = payload.get("houseid", "HS001")
    channel      = payload.get("channel")
    enabled      = payload.get("enabled", True)
    contact_info = {}
    for key in ("address", "bot_token", "chat_id"):
        if key in payload:
            contact_info[key] = payload[key]
    res = await mgr.update_channel(houseid, channel, enabled, contact_info or None)
    if res["status"] == "error":
        return JSONResponse(status_code=400, content=res)
    return res


@router.get("/thresholds")
async def get_thresholds(request: Request, houseid: str = "HS001"):
    mgr = request.app.state.threshold_mgr
    return await mgr.get_thresholds(houseid)


@router.post("/thresholds")
async def set_threshold(request: Request, payload: dict = Body(...)):
    mgr     = request.app.state.threshold_mgr
    houseid = payload.get("houseid", "HS001")
    sensor  = payload.get("sensor")
    min_val = payload.get("min")
    max_val = payload.get("max")
    if sensor is None or min_val is None or max_val is None:
        return JSONResponse(status_code=400,
                            content={"status": "error",
                                     "message": "Thiếu sensor, min hoặc max."})
    res = await mgr.set_threshold(houseid, sensor, min_val, max_val)
    if res["status"] == "error":
        return JSONResponse(status_code=400, content=res)
    return res


@router.post("/thresholds/reset")
async def reset_thresholds(request: Request, payload: dict = Body(...)):
    mgr     = request.app.state.threshold_mgr
    houseid = payload.get("houseid", "HS001")
    return await mgr.reset_to_default(houseid)


@router.get("/automation-rules")
async def get_automation_rules(request: Request, houseid: str = "HS001"):
    mgr = request.app.state.rule_mgr
    return await mgr.get_rules(houseid)


@router.post("/automation-rules")
async def create_automation_rule(request: Request, payload: dict = Body(...)):
    mgr       = request.app.state.rule_mgr
    houseid   = payload.get("houseid", "HS001")
    name      = payload.get("name")
    condition = payload.get("condition")
    actions   = payload.get("actions") or payload.get("action")
    enabled   = payload.get("enabled", payload.get("isactive", True))
    res = await mgr.add_rule(houseid, name, condition, actions, enabled)
    if res["status"] == "error":
        return JSONResponse(status_code=400, content=res)
    return res


@router.delete("/automation-rules")
async def delete_automation_rule(request: Request,
                                  houseid: str = "HS001",
                                  name: str = ""):
    mgr = request.app.state.rule_mgr
    return await mgr.delete_rule(houseid, name)


@router.patch("/automation-rules/toggle")
async def toggle_automation_rule(request: Request, payload: dict = Body(...)):
    """
    Frontend gửi: { houseid, name, enabled: !rule.enabled }
    Backend update: isactive = enabled
    """
    mgr     = request.app.state.rule_mgr
    houseid = payload.get("houseid", "HS001")
    name    = payload.get("name")
    enabled = payload.get("enabled", payload.get("isactive", True))
    return await mgr.toggle_rule(houseid, name, enabled)


@router.get("/check-danger")
async def check_danger_now(request: Request, houseid: str = "HS001"):
    latest = getattr(request.app.state, "latest_sensor_data", None)
    if not latest:
        return {"is_danger": False, "message": "Chưa có dữ liệu cảm biến."}
    mgr         = request.app.state.threshold_mgr
    thresholds  = await mgr.get_thresholds(houseid)
    sensor_data = {
        "temp":  latest.get("temp",  0),
        "humi":  latest.get("humi",  0),
        "light": latest.get("light", 0),
    }
    result = DangerChecker.check(sensor_data, thresholds)
    result["thresholds_used"] = thresholds
    result["sensor_data"]     = sensor_data
    return result


@router.get("/danger-logs")
async def get_danger_logs(request: Request,
                           houseid: str = "HS001",
                           limit: int = 50):
    col     = request.app.state.danger_collection
    cursor  = col.find({"houseid": houseid}).sort("_id", -1).limit(limit)
    results = await cursor.to_list(length=limit)
    for item in results:
        item["_id"] = str(item["_id"])
        t = item.get("time")
        if t is None:
            item["time"] = "--"
        elif hasattr(t, "tzinfo") and t.tzinfo is not None:
            item["time"] = t.astimezone(VN_TZ).strftime("%Y-%m-%dT%H:%M:%S+07:00")
        else:
            item["time"] = (t + timedelta(hours=7)).strftime("%Y-%m-%dT%H:%M:%S+07:00")
    return results


@router.post("/stop-alert")
async def manual_stop_alert(request: Request, payload: dict = Body(...)):
    houseid = payload.get("houseid", "HS001")
    state   = request.app.state
    state.is_danger_global = False
    print(f"[MODULE2][UC002.5] TẮT báo động thủ công (house: {houseid})")
    return {"status": "success", "message": "Đã tắt báo động."}