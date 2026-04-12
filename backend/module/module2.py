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

# Ánh xạ tên field ngưỡng trong bảng House theo ERD
HOUSE_THRESHOLD_FIELDS = {
    "temp":  {"min": "tempmin",  "max": "tempmax"},
    "humi":  {"min": "humimin",  "max": "humimax"},
    "light": {"min": "lightmin", "max": "lightmax"},
}


# ══════════════════════════════════════════════════════════════════
#  ThresholdManager  –  đọc/ghi ngưỡng vào bảng House
# ══════════════════════════════════════════════════════════════════
class ThresholdManager:
    """
    Lưu ngưỡng vào bảng House theo ERD:
      tempmin, tempmax, humimin, humimax, lightmin, lightmax
    Không dùng collection thresholds riêng nữa.
    """

    def __init__(self, house_col, logupdate_col=None):
        self.house_col = house_col   # db.House
        self.logupdate_col = logupdate_col

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
        """Trả về dict {"temp": {"min": x, "max": y}, ...} đọc từ bảng House."""
        house = await self.house_col.find_one({"houseid": houseid})
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
        check = self.validate(sensor, min_val, max_val)
        if not check["ok"]:
            return {"status": "error", "message": check["message"]}

        fields = HOUSE_THRESHOLD_FIELDS.get(sensor)
        if not fields:
            return {"status": "error", "message": f"Cảm biến '{sensor}' không hợp lệ."}

        old_data_full = await self.get_thresholds(houseid)
        old_sensor_data = old_data_full.get(sensor, DEFAULT_THRESHOLDS[sensor])
        now = datetime.now(VN_TZ).replace(tzinfo=None)

        # 2. CẬP NHẬT VÀO BẢNG HOUSE
        await self.house_col.update_one(
            {"houseid": houseid},
            {"$set": {
                fields["min"]: float(min_val),
                fields["max"]: float(max_val),
                "updatedat": now,
            }},
            upsert=True,
        )

        # 3. GHI LOG VÀO BẢNG LOGUPDATE
        if self.logupdate_col is not None:
            log_entry = {
                "time": now,
                "houseid": houseid,
                "target": f"Cấu hình ngưỡng ({sensor})",
                "oldvalue": [{"min": old_sensor_data["min"], "max": old_sensor_data["max"]}],
                "newvalue": [{"min": float(min_val), "max": float(max_val)}]
            }
            await self.logupdate_col.insert_one(log_entry)

        return {"status": "success", "message": "Cập nhật ngưỡng thành công."}

    async def reset_to_default(self, houseid: str) -> dict:
        old_data_full = await self.get_thresholds(houseid)
        now = datetime.now(VN_TZ).replace(tzinfo=None)

        # 2. TIẾN HÀNH RESET
        update_fields: dict = {"updatedat": now}
        for sensor, fields in HOUSE_THRESHOLD_FIELDS.items():
            update_fields[fields["min"]] = DEFAULT_THRESHOLDS[sensor]["min"]
            update_fields[fields["max"]] = DEFAULT_THRESHOLDS[sensor]["max"]

        await self.house_col.update_one(
            {"houseid": houseid},
            {"$set": update_fields},
            upsert=True,
        )

        # 3. GHI LOG RESET
        if self.logupdate_col is not None:
            log_entry = {
                "time": now,
                "houseid": houseid,
                "target": "Cấu hình ngưỡng (Reset mặc định)",
                "oldvalue": [old_data_full],
                "newvalue": [DEFAULT_THRESHOLDS]
            }
            await self.logupdate_col.insert_one(log_entry)

        return {"status": "success", "thresholds": DEFAULT_THRESHOLDS}


# ══════════════════════════════════════════════════════════════════
#  NotificationChannelManager  –  đọc/ghi vào bảng House
# ══════════════════════════════════════════════════════════════════
class NotificationChannelManager:
    """
    Lưu kênh thông báo vào bảng House theo ERD:
      emailtowarning: string
      teletowarning: { token: string, id: string }
    Cờ enabled lưu riêng: email_enabled, telegram_enabled trong House.
    Không dùng collection notification_channels riêng nữa.
    """
    CHANNELS = ("email", "telegram", "app")

    def __init__(self, house_col):
        self.house_col = house_col   # db.House

    @staticmethod
    def validate_contact(channel: str, info: dict) -> dict:
        if channel == "email":
            address = info.get("address", "")
            if address and not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", str(address)):
                return {"ok": False, "message": "Địa chỉ email không hợp lệ."}
        elif channel == "telegram":
            bot_token = info.get("bot_token", "")
            if bot_token and len(str(bot_token).strip()) < 10:
                return {"ok": False, "message": "Bot token không hợp lệ (quá ngắn)."}
        return {"ok": True}

    async def get_channels(self, houseid: str) -> dict:
        """
        Đọc từ bảng House, trả về format chuẩn cho frontend:
        {
          email:    { enabled: bool, address: str },
          telegram: { enabled: bool, bot_token: str, chat_id: str },
          app:      { enabled: bool }
        }
        """
        result = {
            "email":    {"enabled": False},
            "telegram": {"enabled": False},
            "app":      {"enabled": True},
        }
        house = await self.house_col.find_one({"houseid": houseid})
        if not house:
            return result

        # Email
        email_addr = house.get("emailtowarning", "")
        if email_addr:
            result["email"]["address"] = email_addr
        result["email"]["enabled"] = bool(house.get("email_enabled", False))

        # Telegram
        tele = house.get("teletowarning") or {}
        if isinstance(tele, dict):
            token = tele.get("token", "")
            chat  = tele.get("id", "")
            if token:
                result["telegram"]["bot_token"] = token
            if chat:
                result["telegram"]["chat_id"] = chat
        result["telegram"]["enabled"] = bool(house.get("telegram_enabled", False))

        return result

    async def update_channel(self, houseid: str, channel: str,
                              enabled: bool, contact_info: dict = None) -> dict:
        if channel not in self.CHANNELS:
            return {"status": "error", "message": f"Kênh '{channel}' không được hỗ trợ."}

        filtered_info = contact_info or {}
        check = self.validate_contact(channel, filtered_info)
        if not check["ok"]:
            return {"status": "error", "message": check["message"]}

        update_data: dict[str, Any] = {"updatedat": datetime.now(VN_TZ).replace(tzinfo=None)}

        if channel == "email":
            if "address" in filtered_info:
                update_data["emailtowarning"] = filtered_info["address"]
            update_data["email_enabled"] = enabled

        elif channel == "telegram":
            # Merge vào sub-document hiện có
            house = await self.house_col.find_one({"houseid": houseid}) or {}
            existing_tele = house.get("teletowarning") or {}
            if "bot_token" in filtered_info:
                existing_tele["token"] = filtered_info["bot_token"]
            if "chat_id" in filtered_info:
                existing_tele["id"] = filtered_info["chat_id"]
            update_data["teletowarning"]   = existing_tele
            update_data["telegram_enabled"] = enabled

        elif channel == "app":
            update_data["app_enabled"] = enabled

        await self.house_col.update_one(
            {"houseid": houseid},
            {"$set": update_data},
            upsert=True,
        )
        return {"status": "success", "message": "Cập nhật thành công."}

    # Alias dùng trong AlertDispatcher
    async def get_channels_for_dispatch(self, houseid: str) -> dict:
        return await self.get_channels(houseid)


# ══════════════════════════════════════════════════════════════════
#  AutomationRuleManager  –  condition dùng threshold_type (min/max)
# ══════════════════════════════════════════════════════════════════
class AutomationRuleManager:
    """
    Điều kiện kịch bản KHÔNG nhập số thủ công.
    Mỗi điều kiện chỉ cần:  { sensor, threshold_type }
      threshold_type = "max"  →  kích hoạt khi sensor_value > ngưỡng max của House
      threshold_type = "min"  →  kích hoạt khi sensor_value < ngưỡng min của House

    Format lưu DB (bảng Scenario):
      conditions: [{ sensor: "temp", threshold_type: "max" }, ...]
    """

    def __init__(self, collection, threshold_mgr: ThresholdManager):
        self.col           = collection       # db.Scenario
        self.threshold_mgr = threshold_mgr    # lấy ngưỡng từ House khi evaluate

    @staticmethod
    def _validate_conditions(conditions: list) -> dict:
        VALID_SENSORS = {"temp", "humi", "light"}

        if not conditions or not isinstance(conditions, list):
            return {"ok": False, "message": "Phải có ít nhất một điều kiện."}
        if len(conditions) > 3:
            return {"ok": False, "message": "Tối đa 3 điều kiện mỗi kịch bản."}

        for i, cond in enumerate(conditions):
            if "sensor" not in cond:
                return {"ok": False, "message": f"Điều kiện {i+1} thiếu trường 'sensor'."}
            if cond["sensor"] not in VALID_SENSORS:
                return {"ok": False, "message": f"Cảm biến '{cond['sensor']}' không hợp lệ."}

        # Không trùng sensor (Mỗi cảm biến chỉ được chọn 1 lần)
        keys = [c["sensor"] for c in conditions]
        if len(keys) != len(set(keys)):
            return {"ok": False, "message": "Mỗi cảm biến chỉ được xuất hiện một lần trong điều kiện."}

        return {"ok": True}
    
    @staticmethod
    def _normalize_conditions(conditions: list) -> frozenset:
        return frozenset(
            frozenset(c.items())
            for c in conditions
            if c.get("sensor")
    )

    async def _check_condition(self, cond: dict, sensor_data: dict, houseid: str) -> bool:
        sensor  = cond.get("sensor")
        current = sensor_data.get(sensor)
        if current is None:
            return False

        thresholds  = await self.threshold_mgr.get_thresholds(houseid)
        sensor_th   = thresholds.get(sensor)
        if not sensor_th:
            return False
            
        lo = sensor_th.get("min")
        hi = sensor_th.get("max")
        if lo is None or hi is None:
            return False

        try:
            val = float(current)
        except (TypeError, ValueError):
            return False

        # Vượt ngoài vùng an toàn (bé hơn min HOẶC lớn hơn max) thì trả về True
        return val < lo or val > hi

    async def add_rule(self, houseid: str, name: str,
                        conditions: list, actions: list,
                        enabled: bool = True, force: bool = False,
                        original_name: str = None, original_id: str = None) -> dict: # <--- Thêm original_id
        if not name:
            return {"status": "error", "message": "Thiếu tên kịch bản."}
        if not actions:
            return {"status": "error", "message": "Thiếu hành động phản hồi."}
        if not conditions:
            return {"status": "error", "message": "Thiếu điều kiện kích hoạt."}

        check = self._validate_conditions(conditions)
        if not check["ok"]:
            return {"status": "error", "message": check["message"]}
        
        # ID chuẩn bị tạo mới hoặc ghi đè
        scenario_id = f"{houseid}_{name.strip().replace(' ', '_')}"
        
        # ── 1. KIỂM TRA TRÙNG TÊN ────────────────────────────────────
        if not force:
            # Chỉ báo trùng nếu tên này thuộc về một ID KHÁC với ID đang sửa
            if not original_id or scenario_id != original_id:
                existing = await self.col.find_one({"_id": scenario_id})
                if existing:
                    return {
                        "status": "error",
                        "code": "DUPLICATE_NAME",
                        "message": f"Tên kịch bản '{name}' đã tồn tại.",
                        "existing_name": existing.get("name"),
                    }

        # ── 2. KIỂM TRA TRÙNG ĐIỀU KIỆN ──────────────────────────────
        new_cond_sig = self._normalize_conditions(conditions)
        existing_cursor = self.col.find({"houseid": houseid})
        existing_rules  = await existing_cursor.to_list(length=200)

        for ex in existing_rules:
            if original_id and str(ex.get("_id")) == str(original_id):
                continue 
            if force and str(ex.get("_id")) == scenario_id:
                continue

            ex_name = ex.get("name", "").strip().lower()
            if original_name and ex_name == original_name.strip().lower():
                continue
            if ex_name == name.strip().lower():
                continue

            existing_sig = self._normalize_conditions(ex.get("conditions", []))
            if existing_sig == new_cond_sig:
                    return {
                        "status": "error",
                        "code": "DUPLICATE_CONDITIONS",
                        "message": f"Trùng điều kiện với kịch bản đã có: '{ex.get('name')}'.",
                        "conflict_name": ex.get("name"),
                    }
                
        if original_id and str(original_id) != scenario_id:
            await self.col.delete_one({"_id": original_id})

        # ── 4. LƯU VÀO DATABASE ──────────────────────────────────────
        doc = {
            "_id":        scenario_id,
            "scenarioid": scenario_id,
            "houseid":    houseid,
            "name":       name.strip(),
            "conditions": conditions,
            "action":     actions,
            "isactive":   enabled,
            "createdat":  datetime.now(VN_TZ).replace(tzinfo=None),
        }
        await self.col.update_one({"_id": scenario_id}, {"$set": doc}, upsert=True)
        
        return {"status": "success",
                "message": "Tạo/Cập nhật kịch bản thành công.",
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
            conds = r.get("conditions", [])
            output.append({
                "_id":        scenario_id,
                "scenarioid": scenario_id,
                "houseid":    r.get("houseid"),
                "name":       r.get("name"),
                "conditions": conds,
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

        # 1. Lấy tất cả kịch bản đang bật
        cursor = self.col.find({"houseid": houseid, "isactive": True})
        rules  = await cursor.to_list(length=200)

        # 2. Lọc & xếp hạng – check condition với ngưỡng từ House
        matched = []
        for rule in rules:
            conds = rule.get("conditions", [])
            if not conds:
                continue
            all_met = True
            for c in conds:
                if not await self._check_condition(c, sensor_data, houseid):
                    all_met = False
                    break
            if all_met:
                matched.append((rule, self._combo_rank(self._get_sensor_set(conds))))

        matched.sort(key=lambda x: x[1])
        winner_rule = matched[0][0] if matched else None
        winner_name = winner_rule.get("name") if winner_rule else None

        currently_active = state["active_rule_name"]
        new_status       = [list(item) for item in current_device_status]
        before           = {item[0]: item[1] for item in current_device_status}
        triggered_rules  = []

        # 3. Không còn kịch bản nào thỏa → reset
        if winner_name is None:
            if currently_active is not None:
                snap = state["pre_rule_snapshot"]
                if snap:
                    new_status = [list(item) for item in snap]
                print(f"[MODULE2] Kịch bản '{currently_active}' hết điều kiện – khôi phục.")
            state["active_rule_name"]        = None
            state["active_rule_name_expose"] = None
            state["pre_rule_snapshot"]       = None
            return new_status, []

        # 4. Có winner
        if winner_name != currently_active:
            if currently_active is not None:
                snap = state["pre_rule_snapshot"]
                if snap:
                    new_status = [list(item) for item in snap]
                    before     = {item[0]: item[1] for item in new_status}
                print(f"[MODULE2] Kịch bản '{currently_active}' bị thay bởi '{winner_name}'.")

            state["pre_rule_snapshot"]       = [list(item) for item in new_status]
            state["active_rule_name"]        = winner_name
            state["active_rule_name_expose"] = winner_name

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
            print(f"[MODULE2] ✅ Kích hoạt kịch bản: '{winner_name}'")

        else:
            # Drift protection – duy trì trạng thái kịch bản đang chạy
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
        return self._rule_state.get(houseid, {}).get("active_rule_name_expose")


# ══════════════════════════════════════════════════════════════════
#  DangerChecker  –  không thay đổi
# ══════════════════════════════════════════════════════════════════
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


# ══════════════════════════════════════════════════════════════════
#  AlertDispatcher  –  đọc kênh từ House thông qua channel_mgr
# ══════════════════════════════════════════════════════════════════
class AlertDispatcher:
    def __init__(self, danger_col, channel_mgr: NotificationChannelManager):
        self.danger_col  = danger_col    # db.Danger_log
        self.channel_mgr = channel_mgr   # đọc cấu hình kênh từ House

    async def dispatch(self, houseid: str, violations: list,
                       sensor_data: dict, device_status_ref: list,
                       triggered_rules: list = None) -> dict:
        now = datetime.now(VN_TZ).replace(tzinfo=None)

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
            print(f"[MODULE2] Đã ghi Danger_log")
        except Exception as e:
            print(f"[MODULE2] Lỗi ghi Danger_log: {e}")

        # Lấy cấu hình kênh trực tiếp từ bảng House
        channels_doc = await self.channel_mgr.get_channels_for_dispatch(houseid)
        print(f"[MODULE2] Channels (House): {channels_doc}")

        sent_channels = []
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

        return {"dispatched": True, "sent_channels": sent_channels}

    async def auto_stop_alert(self, houseid: str,
                               device_status_ref: list, is_danger: bool):
        if not is_danger:
            print(f"[MODULE2] An toàn – Yolobit tắt nhạc sau 15s.")


# ══════════════════════════════════════════════════════════════════
#  process_danger_and_rules  –  gọi từ server.py
# ══════════════════════════════════════════════════════════════════
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
    result     = DangerChecker.check(sensor_data, thresholds)
    is_danger  = result["is_danger"]
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


# ══════════════════════════════════════════════════════════════════
#  init_module2  –  server.py gọi khi khởi động
# ══════════════════════════════════════════════════════════════════
def init_module2(app, threshold_mgr, channel_mgr, rule_mgr,
                 alert_dispatcher, danger_col):
    """
    Tham số thay đổi so với phiên bản cũ:
      - Bỏ notif_channel_col (không còn collection riêng)
      - threshold_mgr và channel_mgr giờ đều dùng house_col
    """
    app.state.threshold_mgr     = threshold_mgr
    app.state.channel_mgr       = channel_mgr
    app.state.rule_mgr          = rule_mgr
    app.state.alert_dispatcher  = alert_dispatcher
    app.state.danger_collection = danger_col
    print("[MODULE2] init_module2 hoàn tất.")


# ══════════════════════════════════════════════════════════════════
#  API Endpoints
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
    mgr   = request.app.state.rule_mgr
    rules = await mgr.get_rules(houseid)
    active_name = mgr.get_active_rule_name(houseid)
    for r in rules:
        r["is_active_now"] = (r.get("name") == active_name) if active_name else False
    return rules


@router.post("/automation-rules")
async def create_automation_rule(request: Request, payload: dict = Body(...)):
    mgr        = request.app.state.rule_mgr
    houseid    = payload.get("houseid", "HS001")
    name       = payload.get("name")
    conditions = payload.get("conditions", [])
    actions    = payload.get("actions") or payload.get("action")
    enabled    = payload.get("enabled", payload.get("isactive", True))
    force      = payload.get("force", False)
    original_name = payload.get("original_name")
    original_id   = payload.get("original_id") 
    res = await mgr.add_rule(houseid, name, conditions, actions, enabled, force=force, original_name=original_name, original_id=original_id)
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