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
    1: "Đèn báo trộm", 2: "Đèn 2", 3: "Đèn 3",
    4: "Đèn 4",        6: "Servo (Cửa)", 7: "Quạt",
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
        
    @staticmethod
    def _validate_conditions(conditions: list) -> dict:
        VALID_SENSORS = {"temp", "humi", "light"}
        VALID_OPS     = {"gt", "gte", "lt", "lte", "eq"}
 
        if not conditions or not isinstance(conditions, list):
            return {"ok": False, "message": "Phải có ít nhất một điều kiện."}
        if len(conditions) > 3:
            return {"ok": False, "message": "Tối đa 3 điều kiện mỗi kịch bản."}
 
        # Validate từng điều kiện
        for i, cond in enumerate(conditions):
            if not all(k in cond for k in ("sensor", "op", "value")):
                return {"ok": False, "message": f"Điều kiện {i+1} thiếu trường sensor/op/value."}
            if cond["sensor"] not in VALID_SENSORS:
                return {"ok": False, "message": f"Cảm biến '{cond['sensor']}' không hợp lệ."}
            if cond["op"] not in VALID_OPS:
                return {"ok": False, "message": f"Toán tử '{cond['op']}' không được hỗ trợ."}
            try:
                float(cond["value"])
            except (TypeError, ValueError):
                return {"ok": False, "message": f"Giá trị điều kiện {i+1} phải là số."}
 
        # Không được trùng sensor
        sensors_used = [c["sensor"] for c in conditions]
        if len(sensors_used) != len(set(sensors_used)):
            return {"ok": False, "message": "Mỗi cảm biến chỉ được xuất hiện một lần trong điều kiện."}
        by_sensor: dict[str, list] = {}
        for cond in conditions:
            by_sensor.setdefault(cond["sensor"], []).append(cond)
 
        for sensor, conds in by_sensor.items():
            if len(conds) < 2:
                continue
            gt_vals = [float(c["value"]) for c in conds if c["op"] in ("gt", "gte")]
            lt_vals = [float(c["value"]) for c in conds if c["op"] in ("lt", "lte")]
            if gt_vals and lt_vals:
                gt_max = max(gt_vals)
                lt_min = min(lt_vals)
                if gt_max >= lt_min:
                    return {
                        "ok": False,
                        "message": (
                            f"Xung đột điều kiện trên {sensor}: "
                            f"không thể vừa > {gt_max} vừa < {lt_min}."
                        ),
                    }
            # eq xung đột với gt/lt
            eq_vals = [float(c["value"]) for c in conds if c["op"] == "eq"]
            if eq_vals:
                for ev in eq_vals:
                    for gv in gt_vals:
                        if ev <= gv:
                            return {"ok": False, "message": f"Xung đột: {sensor} = {ev} mâu thuẫn với > {gv}."}
                    for lv in lt_vals:
                        if ev >= lv:
                            return {"ok": False, "message": f"Xung đột: {sensor} = {ev} mâu thuẫn với < {lv}."}
 
        return {"ok": True}

    async def add_rule(self, houseid: str, name: str,
                        condition: dict, actions: list,
                        enabled: bool = True,
                        conditions: list = None) -> dict:
        if not name:
            return {"status": "error", "message": "Thiếu tên kịch bản."}
        if not actions:
            return {"status": "error", "message": "Thiếu hành động phản hồi."}
 
        if conditions and isinstance(conditions, list) and len(conditions) > 0:
            conds_list = conditions
        elif condition and isinstance(condition, dict):
            conds_list = [condition]
        else:
            return {"status": "error", "message": "Thiếu điều kiện kích hoạt."}
 
        # Validate + conflict check
        check = self._validate_conditions(conds_list)
        if not check["ok"]:
            return {"status": "error", "message": check["message"]}
 
        # Chuẩn hóa value sang float
        conds_list = [{**c, "value": float(c["value"])} for c in conds_list]
 
        scenario_id = f"{houseid}_{name.replace(' ', '_')}"
        doc = {
            "_id":        scenario_id,
            "scenarioid": scenario_id,
            "houseid":    houseid,
            "name":       name,
            "conditions": conds_list,           # mảng điều kiện AND mới
            "condition":  conds_list[0],        # tương thích ngược: điều kiện đầu tiên
            "action":     actions,
            "isactive":   enabled,
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
            conds = r.get("conditions")
            if not conds:
                single = r.get("condition", {})
                conds  = [single] if single else []
            output.append({
                "_id":        scenario_id,
                "scenarioid": scenario_id,
                "houseid":    r.get("houseid"),
                "name":       r.get("name"),
                "conditions": conds,        
                "condition":  conds[0] if conds else {},
                "action":     action_list,
                "actions":    action_list,
                "isactive":   r.get("isactive", True),
                "enabled":    r.get("isactive", True),
                "createdat":  str(r.get("createdat", "")),
            })
        return output
    _rule_state: dict = {}   # houseid → RuleState

    @staticmethod
    def _get_sensor_set(conditions: list) -> frozenset:
        return frozenset(c.get("sensor") for c in conditions if c.get("sensor"))
    _SENSOR_PRIORITY = ["temp", "humi", "light"]
    _COMBO_RANK: dict = {}   # được tính lười (lazy) lần đầu gọi

    @classmethod
    def _combo_rank(cls, sensor_set: frozenset) -> tuple:
        n = len(sensor_set)
        score = sum(
            2 ** (2 - cls._SENSOR_PRIORITY.index(s))
            for s in sensor_set
            if s in cls._SENSOR_PRIORITY
        )
        return (-n, -score)

    async def evaluate_and_apply(self, houseid: str, sensor_data: dict,
                                  current_device_status: list) -> tuple:

        if houseid not in self._rule_state:
            self._rule_state[houseid] = {
                "active_rule_name":        None,
                "pre_rule_snapshot":       None,
                "active_rule_name_expose": None,
            }

        state = self._rule_state[houseid]

        # ── 1. Lấy tất cả kịch bản đang bật ────────────────────────────
        cursor = self.col.find({"houseid": houseid, "isactive": True})
        rules  = await cursor.to_list(length=200)

        # ── 2. Lọc & xếp hạng kịch bản thỏa điều kiện ───────────────────
        matched = []
        for rule in rules:
            conds = rule.get("conditions") or []
            if not conds:
                single = rule.get("condition", {})
                conds  = [single] if single else []
            if conds and all(self._check_condition(c, sensor_data) for c in conds):
                matched.append((rule, self._combo_rank(self._get_sensor_set(conds))))

        matched.sort(key=lambda x: x[1])
        winner_rule = matched[0][0] if matched else None
        winner_name = winner_rule.get("name") if winner_rule else None

        currently_active = state["active_rule_name"]
        new_status       = [list(item) for item in current_device_status]
        before           = {item[0]: item[1] for item in current_device_status}
        triggered_rules  = []

        # ── 3. Không còn kịch bản nào thỏa → reset ngay ─────────────────
        if winner_name is None:
            if currently_active is not None:
                snap = state["pre_rule_snapshot"]
                if snap:
                    new_status = [list(item) for item in snap]
                print(f"[MODULE2] Kịch bản '{currently_active}' hết điều kiện – khôi phục ngay.")
            state["active_rule_name"]        = None
            state["active_rule_name_expose"] = None
            state["pre_rule_snapshot"]       = None
            return new_status, []

        # ── 4. Có winner – xử lý theo từng trường hợp ────────────────────
        if winner_name != currently_active:
            # Kịch bản mới (hoặc lần đầu) → kích hoạt ngay
            if currently_active is not None:
                # Khôi phục snapshot kịch bản cũ trước khi apply mới
                snap = state["pre_rule_snapshot"]
                if snap:
                    new_status = [list(item) for item in snap]
                    before     = {item[0]: item[1] for item in new_status}
                print(f"[MODULE2] Kịch bản '{currently_active}' bị thay bởi '{winner_name}'.")

            # Chụp snapshot TRƯỚC khi apply
            state["pre_rule_snapshot"]       = [list(item) for item in new_status]
            state["active_rule_name"]        = winner_name
            state["active_rule_name_expose"] = winner_name

            # Apply actions
            rule_changes = []
            for action in winner_rule.get("action", []):
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

            triggered_rules = [{"rule_name": winner_name, "changes": rule_changes}]
            print(f"[MODULE2] ✅ Kích hoạt ngay kịch bản: '{winner_name}'")

        else:
            # Kịch bản đang chạy vẫn thỏa → duy trì + drift protection
            state["active_rule_name_expose"] = winner_name
            for action in winner_rule.get("action", []):
                dev_id = int(action.get("numberdevice"))
                stat   = action.get("status")
                for item in new_status:
                    if item[0] == dev_id:
                        if item[1] != stat:
                            item[1] = stat
                        break

        return new_status, triggered_rules

    def get_active_rule_name(self, houseid: str) -> str | None:
        """Trả về tên kịch bản đang chạy (dùng cho get-commands endpoint)."""
        return self._rule_state.get(houseid, {}).get("active_rule_name_expose")


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
    rules = await mgr.get_rules(houseid)
    active_name = mgr.get_active_rule_name(houseid)
    for r in rules:
        r["is_active_now"] = (r.get("name") == active_name) if active_name else False
    return rules


@router.post("/automation-rules")
async def create_automation_rule(request: Request, payload: dict = Body(...)):
    mgr       = request.app.state.rule_mgr
    houseid   = payload.get("houseid", "HS001")
    name      = payload.get("name")
    condition = payload.get("condition")
    conditions = payload.get("conditions")
    actions   = payload.get("actions") or payload.get("action")
    enabled   = payload.get("enabled", payload.get("isactive", True))
    res = await mgr.add_rule(houseid, name, condition, actions, enabled, conditions=conditions)
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