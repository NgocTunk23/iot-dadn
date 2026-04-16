"""
module2.py  –  Ngưỡng cảm biến, kênh thông báo, kịch bản tự động, kiểm tra nguy hiểm.
Phiên bản đã nâng cấp: tất cả API nhận houseid động (không hardcode HS001).
"""
from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
from typing import Any
import re
import uuid
from module.notifiers import dispatch_all_channels

router = APIRouter(prefix="/api", tags=["Module 2 – Safety & Automation"])

VN_TZ = timezone(timedelta(hours=7))

# Ngưỡng mặc định (dự phòng khi House chưa có cấu hình)
DEFAULT_THRESHOLDS = {
    "temp":  {"min": 0,   "max": 40},
    "humi":  {"min": 20,  "max": 80},
    "light": {"min": 0,   "max": 90},
}

DEVICE_NAMES = {
    1: "Đèn báo trộm", 2: "Đèn 2", 3: "Đèn 3",
    4: "Đèn 4",        6: "Servo (Cửa)", 7: "Quạt",
}

HOUSE_THRESHOLD_FIELDS = {
    "temp":  {"min": "tempmin",  "max": "tempmax"},
    "humi":  {"min": "humimin",  "max": "humimax"},
    "light": {"min": "lightmin", "max": "lightmax"},
}


# ══════════════════════════════════════════════════════════════════
#  Hàm helper: đảm bảo House tồn tại
# ══════════════════════════════════════════════════════════════════
async def ensure_house_default(house_col, houseid: str, username: str = ""):
    house = await house_col.find_one({"_id.houseid": houseid})
    if not house:
        now = datetime.now(VN_TZ).replace(tzinfo=None)
        DEFAULT_NUMBERDEVICES = [
            {"numberdevice": 1, "type": "denchongtrom", "status": False},
            {"numberdevice": 2, "type": "den",           "status": False},
            {"numberdevice": 3, "type": "den",           "status": False},
            {"numberdevice": 4, "type": "den",           "status": False},
            {"numberdevice": 6, "type": "servo",         "status": 0},
            {"numberdevice": 7, "type": "quat",          "status": 0},
        ]
        default_house = {
            "_id":              {"houseid": houseid, "username": username},
            "tempmin":          DEFAULT_THRESHOLDS["temp"]["min"],
            "tempmax":          DEFAULT_THRESHOLDS["temp"]["max"],
            "humimin":          DEFAULT_THRESHOLDS["humi"]["min"],
            "humimax":          DEFAULT_THRESHOLDS["humi"]["max"],
            "lightmin":         DEFAULT_THRESHOLDS["light"]["min"],
            "lightmax":         DEFAULT_THRESHOLDS["light"]["max"],
            "emailtowarning":   "",
            "email_enabled":    False,
            "teletowarning":    {"token": "", "id": ""},
            "telegram_enabled": False,
            "numberdevices":    DEFAULT_NUMBERDEVICES,
            "createdat":        now,
        }
        await house_col.insert_one(default_house)
        print(f"[MODULE2] Đã tạo House mặc định: {houseid}")


# Backward-compat: gọi khi server startup với HS001
async def initialize_default_house(house_col):
    await ensure_house_default(house_col, "HS001")

async def sync_device_state(house_col, house_id: str, updates: list):
    house = await house_col.find_one({"_id.houseid": house_id})
    if not house:
        return

    current_devices = house.get("numberdevices", [])
    # Tạo map để tìm kiếm nhanh theo numberdevice
    device_map = {d['numberdevice']: d for d in current_devices}

    for item in updates:
        if isinstance(item, list):
            d_id, d_val = item[0], item[1]
        else:
            d_id, d_val = item.get("numberdevice"), item.get("status")
        
        if d_id in device_map:
            device_map[d_id]["status"] = d_val

    await house_col.update_one(
        {"_id.houseid": house_id},
        {"$set": {"numberdevices": list(device_map.values())}}
    )
    print(f"[MODULE2] Đã đồng bộ thiết bị cho {house_id} vào Database.")
# ══════════════════════════════════════════════════════════════════
#  ThresholdManager
# ══════════════════════════════════════════════════════════════════
class ThresholdManager:
    def __init__(self, house_col, logupdate_col=None):
        self.house_col      = house_col
        self.logupdate_col  = logupdate_col

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
        await ensure_house_default(self.house_col, houseid)
        house = await self.house_col.find_one({"_id.houseid": houseid})
        result = {}
        for sensor, fields in HOUSE_THRESHOLD_FIELDS.items():
            default = DEFAULT_THRESHOLDS[sensor]
            result[sensor] = {
                "min": house.get(fields["min"], default["min"]) if house else default["min"],
                "max": house.get(fields["max"], default["max"]) if house else default["max"],
            }
        return result

    async def set_threshold(self, houseid: str, sensor: str,
                            min_val: float, max_val: float) -> dict:
        await ensure_house_default(self.house_col, houseid)
        check = self.validate(sensor, min_val, max_val)
        if not check["ok"]:
            return {"status": "error", "message": check["message"]}

        fields = HOUSE_THRESHOLD_FIELDS.get(sensor)
        if not fields:
            return {"status": "error", "message": f"Cảm biến '{sensor}' không hợp lệ."}

        old_data   = await self.get_thresholds(houseid)
        old_sensor = old_data.get(sensor, DEFAULT_THRESHOLDS[sensor])
        now        = datetime.now(VN_TZ).replace(tzinfo=None)

        await self.house_col.update_one(
            {"_id.houseid": houseid},
            {"$set": {fields["min"]: float(min_val), fields["max"]: float(max_val), "createdat": now}},
            upsert=True,
        )

        if self.logupdate_col is not None:
            await self.logupdate_col.insert_one({
                "time":     now,
                "houseid":  houseid,
                "target":   f"Cấu hình ngưỡng ({sensor})",
                "oldvalue": [{"min": old_sensor["min"], "max": old_sensor["max"]}],
                "newvalue": [{"min": float(min_val),   "max": float(max_val)}],
            })

        return {"status": "success", "message": "Cập nhật ngưỡng thành công."}

    async def reset_to_default(self, houseid: str) -> dict:
        old_data   = await self.get_thresholds(houseid)
        now        = datetime.now(VN_TZ).replace(tzinfo=None)
        update_fields: dict = {"createdat": now}
        for sensor, fields in HOUSE_THRESHOLD_FIELDS.items():
            update_fields[fields["min"]] = DEFAULT_THRESHOLDS[sensor]["min"]
            update_fields[fields["max"]] = DEFAULT_THRESHOLDS[sensor]["max"]

        await self.house_col.update_one({"_id.houseid": houseid}, {"$set": update_fields}, upsert=True)

        if self.logupdate_col is not None:
            await self.logupdate_col.insert_one({
                "time":     now,
                "houseid":  houseid,
                "target":   "Cấu hình ngưỡng (Reset mặc định)",
                "oldvalue": [old_data],
                "newvalue": [DEFAULT_THRESHOLDS],
            })

        return {
            "status": "success", 
            "message": "Đã reset ngưỡng về mặc định.",
            "thresholds": DEFAULT_THRESHOLDS 
        }


# ══════════════════════════════════════════════════════════════════
#  NotificationChannelManager
# ══════════════════════════════════════════════════════════════════
class NotificationChannelManager:
    def __init__(self, house_col):
        self.house_col = house_col

    async def get_channels(self, houseid: str) -> dict:
        await ensure_house_default(self.house_col, houseid)
        house = await self.house_col.find_one({"_id.houseid": houseid}) or {}
        return {
            "telegram": {
                "enabled":   house.get("telegram_enabled", False),
                "bot_token": house.get("teletowarning", {}).get("token", ""),
                "chat_id":   house.get("teletowarning", {}).get("id", ""),
            },
            "email": {
                "enabled": house.get("email_enabled", False),
                "address": house.get("emailtowarning", ""),
            },
        }

    async def update_channel(self, houseid: str, channel: str,
                             enabled: bool, contact_info: dict | None) -> dict:
        await ensure_house_default(self.house_col, houseid)
        update = {}
        if channel == "telegram":
            update["telegram_enabled"] = enabled
            if contact_info:
                tele = {}
                if "bot_token" in contact_info:
                    tele["token"] = contact_info["bot_token"]
                if "chat_id" in contact_info:
                    tele["id"] = contact_info["chat_id"]
                if tele:
                    update["teletowarning"] = tele
        elif channel == "email":
            update["email_enabled"] = enabled
            if contact_info and "address" in contact_info:
                update["emailtowarning"] = contact_info["address"]
        else:
            return {"status": "error", "message": f"Kênh '{channel}' không hợp lệ."}

        await self.house_col.update_one({"_id.houseid": houseid}, {"$set": update}, upsert=True)
        return {"status": "success", "message": f"Đã cập nhật kênh {channel}."}


# ══════════════════════════════════════════════════════════════════
#  DangerChecker
# ══════════════════════════════════════════════════════════════════
class DangerChecker:
    @staticmethod
    def check(sensor_data: dict, thresholds: dict) -> dict:
        violations = []
        for sensor in ("temp", "humi", "light"):
            val = sensor_data.get(sensor, 0)
            th  = thresholds.get(sensor, DEFAULT_THRESHOLDS[sensor])
            if val > th["max"]:
                violations.append({"sensor": sensor, "value": val, "threshold": "max", "limit": th["max"]})
            elif val < th["min"]:
                violations.append({"sensor": sensor, "value": val, "threshold": "min", "limit": th["min"]})
        return {"is_danger": len(violations) > 0, "violations": violations}


# ══════════════════════════════════════════════════════════════════
#  AutomationRuleManager
# ══════════════════════════════════════════════════════════════════
class AutomationRuleManager:
    def __init__(self, rules_col, threshold_mgr: ThresholdManager):
        self.rules_col     = rules_col
        self.threshold_mgr = threshold_mgr
        self._active_rules: dict[str, str | None] = {}
        self._pre_rule_states: dict[str, list] = {}
        self._active_actions: dict[str, list] = {}

    _SENSOR_PRIORITY = ["temp", "humi", "light"]

    def get_active_rule_name(self, houseid: str) -> str | None:
        return self._active_rules.get(houseid)
    @staticmethod
    def _get_sensor_set(conditions: list) -> frozenset:
        return frozenset(c.get("sensor") for c in conditions if c.get("sensor"))

    @classmethod
    def _combo_rank(cls, sensor_set: frozenset) -> tuple:
        n = len(sensor_set)
        score = sum(
            2 ** (2 - cls._SENSOR_PRIORITY.index(s))
            for s in sensor_set
            if s in cls._SENSOR_PRIORITY
        )
        return (-n, -score)
    async def get_rules(self, houseid: str) -> list:
        cursor  = self.rules_col.find({"houseid": houseid})
        results = await cursor.to_list(length=200)
        out = []
        for r in results:
            r["_id"] = str(r["_id"])
            out.append(r)
        return out

    async def add_rule(self, houseid: str, name: str, conditions: list,
                       actions: list, enabled: bool = True,
                       force: bool = False,
                       original_name: str | None = None,
                       original_id:   str | None = None) -> dict:
        if not name or not conditions or not actions:
            return {"status": "error", "message": "Thiếu name, conditions hoặc actions."}

        if force:
            original_name = name

        if not force:
            name_query = {"houseid": houseid, "name": name}
            if original_name:
                name_query["name"] = {"$eq": name, "$ne": original_name}
                
            existing_name_rule = await self.rules_col.find_one(name_query)
            if existing_name_rule:
                return {
                    "status": "error",
                    "code": "DUPLICATE_NAME", 
                    "existing_name": existing_name_rule["name"],
                    "message": f"Tên kịch bản '{name}' đã tồn tại."
                }

        new_sensors = set(c.get("sensor") for c in conditions if c.get("sensor"))
        
        all_rules = await self.get_rules(houseid)
        for rule in all_rules:
            if original_name and rule.get("name") == original_name:
                continue
            if original_id and str(rule.get("_id")) == original_id:
                continue
            
            existing_sensors = set(c.get("sensor") for c in rule.get("conditions", []) if c.get("sensor"))
            
            if new_sensors == existing_sensors:
                return {
                    "status": "error",
                    "code": "DUPLICATE_CONDITIONS",
                    "conflict_name": rule["name"],
                    "message": "Bộ điều kiện bị trùng lặp với kịch bản khác."
                }

        now = datetime.now(VN_TZ).replace(tzinfo=None)
        doc = {
            "houseid":    houseid,
            "name":       name,
            "conditions": conditions,
            "action":     actions,
            "enabled":    enabled,
            "updatedat":  now,
        }

        if original_name or original_id:
            filter_q = {"houseid": houseid}
            if original_id and not force:
                from bson import ObjectId
                try:
                    filter_q["_id"] = ObjectId(original_id)
                except Exception:
                    filter_q["name"] = original_name
            else:
                filter_q["name"] = original_name
                
            await self.rules_col.update_one(filter_q, {"$set": doc}, upsert=True)
            
            if self._active_rules.get(houseid) == original_name:
                self._active_rules[houseid] = name
        else:
            doc["createdat"] = now
            await self.rules_col.insert_one(doc)

        return {"status": "success", "message": f"Đã lưu kịch bản '{name}'."}

    async def delete_rule(self, houseid: str, name: str) -> dict:
        result = await self.rules_col.delete_one({"houseid": houseid, "name": name})
        if result.deleted_count > 0:
            if self._active_rules.get(houseid) == name:
                self._active_rules[houseid] = None
            return {"status": "success", "message": f"Đã xoá kịch bản '{name}'."}
        return {"status": "error", "message": "Không tìm thấy kịch bản."}

    async def toggle_rule(self, houseid: str, name: str, enabled: bool) -> dict:
        result = await self.rules_col.update_one(
            {"houseid": houseid, "name": name},
            {"$set": {"enabled": enabled}},
        )
        if result.matched_count == 0:
            return {"status": "error", "message": "Không tìm thấy kịch bản."}
        return {"status": "success"}

    async def evaluate_and_apply(self, houseid: str, sensor_data: dict,
                                 current_status: list) -> tuple[list, list]:
        """
        Logic ưu tiên kịch bản:
          - Combo 3 sensor (temp+humi+light) > combo 2 (temp+humi > temp+light > humi+light) > đơn (temp > humi > light)
          - Khi chuyển kịch bản: undo actions kịch bản cũ (về pre_rule_state) rồi áp kịch bản mới
          - pre_rule_state chỉ được snapshot 1 lần duy nhất khi chuyển từ "không kịch bản" → "có kịch bản"
          - Khi tất cả kịch bản tắt: restore về pre_rule_state
        """
        thresholds = await self.threshold_mgr.get_thresholds(houseid)
        rules      = await self.get_rules(houseid)
        triggered  = []

        was_active_rule = self._active_rules.get(houseid)

        # ── 1. Tìm kịch bản thắng (winner) ──────────────────────────────
        matched_rules = []
        for rule in rules:
            if not rule.get("enabled", True):
                continue
            conditions = rule.get("conditions", [])
            if self._eval_conditions(conditions, sensor_data, thresholds):
                rank = self._combo_rank(self._get_sensor_set(conditions))
                matched_rules.append((rule, rank))

        matched_rules.sort(key=lambda x: x[1])
        winner_rule = matched_rules[0][0] if matched_rules else None
        winner_name = winner_rule.get("name") if winner_rule else None

        # ── 2. Có kịch bản thắng ─────────────────────────────────────────
        if winner_rule:
            winner_actions = winner_rule.get("action", [])

            if winner_name != was_active_rule:
                # ── 2a. Kịch bản thay đổi (hoặc lần đầu kích hoạt) ──────

                # Snapshot pre_rule_state CHỈ 1 LẦN khi chưa có kịch bản nào
                if not was_active_rule:
                    self._pre_rule_states[houseid] = [list(item) for item in current_status]
                    print(f"[MODULE2] Snapshot pre_rule_state cho {houseid}: {self._pre_rule_states[houseid]}")

                # Bắt đầu từ pre_rule_state rồi áp kịch bản mới
                # → đảm bảo undo hoàn toàn kịch bản cũ, chỉ giữ trạng thái trung lập
                base_status = [list(item) for item in self._pre_rule_states[houseid]]

                if was_active_rule:
                    print(f"[MODULE2] Kịch bản '{was_active_rule}' bị đè bởi '{winner_name}'. "
                          f"Undo kịch bản cũ, áp kịch bản mới từ pre_rule_state.")

                new_status = base_status
                changes = self._apply_actions(new_status, winner_actions)

                triggered.append({"rule_name": winner_name, "changes": changes})
                self._active_rules[houseid]  = winner_name
                self._active_actions[houseid] = winner_actions

            else:
                # ── 2b. Kịch bản giữ nguyên — chỉ re-apply để đảm bảo đúng trạng thái
                new_status = [list(item) for item in self._pre_rule_states.get(houseid, current_status)]
                self._apply_actions(new_status, winner_actions)

        # ── 3. Không có kịch bản nào thoả — restore về pre_rule_state ───
        else:
            if was_active_rule:
                if houseid in self._pre_rule_states:
                    print(f"[MODULE2] Kịch bản '{was_active_rule}' hết hiệu lực. "
                          f"Phục hồi trạng thái trước khi có kịch bản.")
                    new_status = [list(item) for item in self._pre_rule_states[houseid]]
                    triggered.append({
                        "rule_name": "Hệ thống an toàn trở lại",
                        "changes": [{
                            "device_name": "Tất cả thiết bị",
                            "changed":     True,
                            "from":        f"Kịch bản {was_active_rule}",
                            "to":          "Khôi phục trạng thái ban đầu",
                        }]
                    })
                    del self._pre_rule_states[houseid]
                else:
                    # Không có snapshot → giữ nguyên current (edge case)
                    new_status = [list(item) for item in current_status]
            else:
                # Không có kịch bản nào trước đó và cũng không có bây giờ → giữ nguyên
                new_status = [list(item) for item in current_status]

            self._active_rules.pop(houseid, None)
            self._active_actions.pop(houseid, None)

        return new_status, triggered


    @staticmethod
    def _eval_conditions(conditions: list, sensor_data: dict, thresholds: dict) -> bool:
        if not conditions:
            return False
        for cond in conditions:
            sensor = cond.get("sensor")
            if not sensor:
                continue
            val = sensor_data.get(sensor, 0)
            th  = thresholds.get(sensor, DEFAULT_THRESHOLDS.get(sensor, {}))
            lo  = cond.get("lowerbound", th.get("min", 0))
            hi  = cond.get("upperbound", th.get("max", 100))
            if lo <= val <= hi:
                return False   # Trong ngưỡng an toàn → điều kiện KHÔNG thoả
        return True

    @staticmethod
    def _apply_actions(status_list: list, actions: list) -> list:
        status_dict = {item[0]: item[1] for item in status_list}
        changes     = []
        DEVICE_NAMES_LOCAL = {1: "Đèn báo trộm", 2: "Đèn 2", 3: "Đèn 3",
                               4: "Đèn 4", 6: "Servo (Cửa)", 7: "Quạt"}
        for act in actions:
            dev_id   = act.get("numberdevice") or act.get("device_id")
            val      = act.get("status") if "status" in act else act.get("value")
            if dev_id is None or val is None:
                continue
            old_val  = status_dict.get(dev_id)
            changed  = old_val != val
            changes.append({
                "device_name": DEVICE_NAMES_LOCAL.get(dev_id, f"Thiết bị {dev_id}"),
                "from":        old_val,
                "to":          val,
                "changed":     changed,
            })
            status_dict[dev_id] = val

        # Cập nhật lại status_list in-place
        for i, item in enumerate(status_list):
            if item[0] in status_dict:
                status_list[i][1] = status_dict[item[0]]
        return changes


# ══════════════════════════════════════════════════════════════════
#  AlertDispatcher
# ══════════════════════════════════════════════════════════════════
class AlertDispatcher:
    def __init__(self, danger_col, channel_mgr: NotificationChannelManager):
        self.danger_col  = danger_col
        self.channel_mgr = channel_mgr
        self._last_alert: dict[str, float] = {}   # houseid → timestamp
        self._alert_cooldown = 300                 # 5 phút giữa 2 lần báo

    async def dispatch(self, houseid: str, violations: list,
                       sensor_data: dict, device_status: list,
                       triggered_rules: list | None = None):
        import time
        now_ts = time.time()
        last   = self._last_alert.get(houseid, 0)
        if now_ts - last < self._alert_cooldown:
            return  # Cooldown chưa hết

        self._last_alert[houseid] = now_ts
        now_dt = datetime.now(VN_TZ).replace(tzinfo=None)

        # Ghi Danger_log
        await self.danger_col.update_one(
            {"houseid": houseid, "time": now_dt},
            {"$set": {
                "houseid":    houseid,
                "time":       now_dt,
                "violations": violations,
                "value":      {k: sensor_data.get(k) for k in ("temp", "humi", "light")},
            }},
            upsert=True,
        )

        # Gửi thông báo
        channels_doc = await self.channel_mgr.get_channels(houseid)
        channels_raw = {
            "telegram": {
                "enabled":   channels_doc["telegram"]["enabled"],
                "bot_token": channels_doc["telegram"]["bot_token"],
                "chat_id":   channels_doc["telegram"]["chat_id"],
            },
            "email": {
                "enabled": channels_doc["email"]["enabled"],
                "address": channels_doc["email"]["address"],
            },
        }
        await dispatch_all_channels(houseid, violations, sensor_data,
                                    channels_raw, triggered_rules=triggered_rules)

    async def auto_stop_alert(self, houseid: str, device_status: list, is_danger: bool):
        pass  # Placeholder — logic tắt báo động nếu cần


# ══════════════════════════════════════════════════════════════════
#  process_danger_and_rules  –  gọi từ server.py
# ══════════════════════════════════════════════════════════════════
async def process_danger_and_rules(app, payload: dict, house_id: str):
    threshold_mgr    = app.state.threshold_mgr
    rule_mgr         = app.state.rule_mgr
    alert_dispatcher = app.state.alert_dispatcher

    sensor_data = {
        "temp":  payload.get("temp",  0),
        "humi":  payload.get("humi",  0),
        "light": payload.get("light", 0),
    }
    thresholds = await threshold_mgr.get_thresholds(house_id)
    result     = DangerChecker.check(sensor_data, thresholds)
    is_danger  = result["is_danger"]
    app.state.is_danger_global = is_danger

    new_status, triggered_rules = await rule_mgr.evaluate_and_apply(
        house_id, sensor_data, app.state.device_status
    )
    state_changed = new_status != app.state.device_status
    app.state.device_status = new_status
    if triggered_rules or state_changed:
        await sync_device_state(threshold_mgr.house_col, house_id, new_status)
        label = triggered_rules[0]['rule_name'] if triggered_rules else "thay đổi trạng thái"
        print(f"[MODULE2] Đã lưu trạng thái '{label}' vào DB.")
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


# ══════════════════════════════════════════════════════════════════
#  init_module2
# ══════════════════════════════════════════════════════════════════
def init_module2(app, threshold_mgr, channel_mgr, rule_mgr,
                 alert_dispatcher, danger_col):
    app.state.threshold_mgr     = threshold_mgr
    app.state.channel_mgr       = channel_mgr
    app.state.rule_mgr          = rule_mgr
    app.state.alert_dispatcher  = alert_dispatcher
    app.state.danger_collection = danger_col
    print("[MODULE2] init_module2 hoàn tất.")


# ══════════════════════════════════════════════════════════════════
#  API Endpoints  –  tất cả đều nhận houseid động qua query/body
# ══════════════════════════════════════════════════════════════════

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
    contact_info = {k: payload[k] for k in ("address", "bot_token", "chat_id") if k in payload}
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
        return JSONResponse(status_code=400, content={"status": "error", "message": "Thiếu sensor, min hoặc max."})
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
    mgr         = request.app.state.rule_mgr
    rules       = await mgr.get_rules(houseid)
    active_name = mgr.get_active_rule_name(houseid)
    for r in rules:
        r["is_active_now"] = (r.get("name") == active_name) if active_name else False
    return rules


@router.post("/automation-rules")
async def create_automation_rule(request: Request, payload: dict = Body(...)):
    mgr           = request.app.state.rule_mgr
    houseid       = payload.get("houseid", "HS001")
    name          = payload.get("name")
    conditions    = payload.get("conditions", [])
    actions       = payload.get("actions") or payload.get("action")
    enabled       = payload.get("enabled", payload.get("isactive", True))
    force         = payload.get("force", False)
    original_name = payload.get("original_name")
    original_id   = payload.get("original_id")
    res = await mgr.add_rule(houseid, name, conditions, actions, enabled,
                              force=force, original_name=original_name, original_id=original_id)
    if res["status"] == "error":
        return JSONResponse(status_code=400, content=res)
    return res


@router.delete("/automation-rules")
async def delete_automation_rule(request: Request, houseid: str = "HS001", name: str = ""):
    mgr = request.app.state.rule_mgr
    return await mgr.delete_rule(houseid, name)


@router.patch("/automation-rules/toggle")
async def toggle_automation_rule(request: Request, payload: dict = Body(...)):
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
    sensor_data = {k: latest.get(k, 0) for k in ("temp", "humi", "light")}
    result      = DangerChecker.check(sensor_data, thresholds)
    result["thresholds_used"] = thresholds
    result["sensor_data"]     = sensor_data
    return result


@router.get("/danger-logs")
async def get_danger_logs(request: Request, houseid: str = "HS001", limit: int = 50):
    col    = request.app.state.danger_collection
    cursor = col.find({"houseid": houseid}).sort("_id", -1).limit(limit)
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
    request.app.state.is_danger_global = False
    print(f"[MODULE2] TẮT báo động thủ công (house: {houseid})")
    return {"status": "success", "message": "Đã tắt báo động."}