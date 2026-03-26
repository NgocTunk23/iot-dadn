"""
MODULE 2 - Quản lý Cảnh báo & Ngưỡng An toàn
"""

from datetime import datetime, timedelta, timezone
from typing import Any
import re
from module.notifiers import dispatch_all_channels

DEFAULT_THRESHOLDS = {
    "temp":  {"min": 0,   "max": 40},
    "humi":  {"min": 20,  "max": 80},
    "light": {"min": 0,   "max": 90},
}

DEVICE_NAMES = {
    1: "Đèn 1", 2: "Đèn 2", 3: "Đèn 3", 4: "Đèn 4", 5: "Đèn 5",
    6: "Servo (Cửa)", 7: "Quạt"
}

VN_TZ = timezone(timedelta(hours=7))


class ThresholdManager:
    def __init__(self, collection):
        self.col = collection

    @staticmethod
    def validate(sensor: str, min_val: float, max_val: float) -> dict:
        PHYSICAL_LIMITS = {"temp": (-50, 500), "humi": (0, 100), "light": (0, 100)}
        if sensor not in PHYSICAL_LIMITS:
            return {"ok": False, "message": f"Cảm biến '{sensor}' không tồn tại."}
        lo, hi = PHYSICAL_LIMITS[sensor]
        try:
            min_val = float(min_val)
            max_val = float(max_val)
        except (TypeError, ValueError):
            return {"ok": False, "message": "Giá trị ngưỡng phải là số."}
        if not (lo <= min_val <= hi) or not (lo <= max_val <= hi):
            return {"ok": False, "message": f"Giá trị vượt phạm vi vật lý ({lo} – {hi})."}
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

    async def set_threshold(self, houseid: str, sensor: str, min_val: float, max_val: float) -> dict:
        check = self.validate(sensor, min_val, max_val)
        if not check["ok"]:
            return {"status": "error", "message": check["message"]}
        await self.col.update_one(
            {"_id": houseid},
            {"$set": {sensor: {"min": float(min_val), "max": float(max_val)}, "updated_at": datetime.now(VN_TZ)}},
            upsert=True
        )
        return {"status": "success", "message": "Cập nhật ngưỡng thành công."}

    async def reset_to_default(self, houseid: str) -> dict:
        await self.col.update_one(
            {"_id": houseid},
            {"$set": {**DEFAULT_THRESHOLDS, "updated_at": datetime.now(VN_TZ)}},
            upsert=True
        )
        return {"status": "success", "thresholds": DEFAULT_THRESHOLDS}


class NotificationChannelManager:
    CHANNELS = ("sms", "email", "app", "telegram")

    def __init__(self, collection):
        self.col = collection

    @staticmethod
    def validate_contact(channel: str, info: dict) -> dict:
        if channel == "sms":
            phone = info.get("phone", "")
            if not re.fullmatch(r"0\d{9}", str(phone)):
                return {"ok": False, "message": "Số điện thoại không hợp lệ."}
        elif channel == "email":
            address = info.get("address", "")
            if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", str(address)):
                return {"ok": False, "message": "Địa chỉ email không hợp lệ."}
        return {"ok": True}

    async def get_channels(self, houseid: str) -> dict:
        doc = await self.col.find_one({"_id": houseid})
        if doc:
            doc.pop("_id", None)
            return doc
        return {"sms": {"enabled": False}, "email": {"enabled": False}, "app": {"enabled": True}, "telegram": {"enabled": False}}

    async def update_channel(self, houseid: str, channel: str, enabled: bool, contact_info: dict = None) -> dict:
        if channel not in self.CHANNELS:
            return {"status": "error", "message": f"Kênh '{channel}' không được hỗ trợ."}
        if contact_info:
            check = self.validate_contact(channel, contact_info)
            if not check["ok"]:
                return {"status": "error", "message": check["message"]}
        update_data: dict[str, Any] = {f"{channel}.enabled": enabled}
        if contact_info:
            for k, v in contact_info.items():
                update_data[f"{channel}.{k}"] = v
        await self.col.update_one({"_id": houseid}, {"$set": update_data}, upsert=True)
        return {"status": "success", "message": "Cập nhật thành công."}


class AutomationRuleManager:
    OPERATORS = {"gt": ">", "lt": "<", "gte": ">=", "lte": "<=", "eq": "=="}

    def __init__(self, collection):
        self.col = collection

    @staticmethod
    def _check_condition(condition: dict, sensor_data: dict) -> bool:
        sensor  = condition.get("sensor")
        op      = condition.get("op")
        value   = condition.get("value")
        current = sensor_data.get(sensor)
        if current is None or op not in AutomationRuleManager.OPERATORS:
            return False
        ops = {"gt": lambda a, b: a > b, "lt": lambda a, b: a < b,
               "gte": lambda a, b: a >= b, "lte": lambda a, b: a <= b,
               "eq": lambda a, b: a == b}
        return ops[op](float(current), float(value))

    async def add_rule(self, houseid: str, name: str, condition: dict, actions: list, enabled: bool = True) -> dict:
        if not name:
            return {"status": "error", "message": "Thiếu tên kịch bản."}
        if not condition or not all(k in condition for k in ("sensor", "op", "value")):
            return {"status": "error", "message": "Điều kiện không hợp lệ."}
        if not actions:
            return {"status": "error", "message": "Thiếu hành động phản hồi."}
        if condition["op"] not in self.OPERATORS:
            return {"status": "error", "message": f"Toán tử không hỗ trợ."}
        doc_id = f"{houseid}_{name.replace(' ', '_')}"
        doc = {"_id": doc_id, "houseid": houseid, "name": name, "condition": condition,
               "actions": actions, "enabled": enabled, "created_at": datetime.now(VN_TZ)}
        await self.col.update_one({"_id": doc_id}, {"$set": doc}, upsert=True)
        return {"status": "success", "message": "Tạo kịch bản thành công.", "rule_id": doc_id}

    async def delete_rule(self, houseid: str, name: str) -> dict:
        doc_id = f"{houseid}_{name.replace(' ', '_')}"
        result = await self.col.delete_one({"_id": doc_id})
        if result.deleted_count:
            return {"status": "success", "message": "Đã xóa kịch bản."}
        return {"status": "error", "message": "Kịch bản không tồn tại."}

    async def toggle_rule(self, houseid: str, name: str, enabled: bool) -> dict:
        doc_id = f"{houseid}_{name.replace(' ', '_')}"
        result = await self.col.update_one({"_id": doc_id}, {"$set": {"enabled": enabled}})
        if result.matched_count:
            return {"status": "success"}
        return {"status": "error", "message": "Kịch bản không tồn tại."}

    async def get_rules(self, houseid: str) -> list:
        cursor = self.col.find({"houseid": houseid})
        rules  = await cursor.to_list(length=200)
        for r in rules:
            r["_id"] = str(r["_id"])
            if "created_at" in r:
                r["created_at"] = str(r["created_at"])
        return rules

    async def evaluate_and_apply(self, houseid: str, sensor_data: dict,
                                  current_device_status: list) -> tuple:
        """
        Trả về (new_status, triggered_rules_info)
        triggered_rules_info: list các dict mô tả kịch bản đã trigger + thay đổi thiết bị
        """
        cursor   = self.col.find({"houseid": houseid, "enabled": True})
        rules    = await cursor.to_list(length=200)
        new_status = [list(item) for item in current_device_status]

        # Lưu trạng thái trước khi apply để so sánh
        before = {item[0]: item[1] for item in current_device_status}
        triggered_rules = []

        for rule in rules:
            if self._check_condition(rule["condition"], sensor_data):
                rule_changes = []
                for action in rule.get("actions", []):
                    dev_id = int(action.get("numberdevice"))
                    stat   = action.get("status")
                    for item in new_status:
                        if item[0] == dev_id:
                            old_val = before.get(dev_id)
                            item[1] = stat
                            # Ghi nhận thay đổi so với trước
                            rule_changes.append({
                                "device_id":   dev_id,
                                "device_name": DEVICE_NAMES.get(dev_id, f"Thiết bị {dev_id}"),
                                "from":        old_val,
                                "to":          stat,
                                "changed":     old_val != stat
                            })
                            break

                triggered_rules.append({
                    "rule_name": rule["name"],
                    "changes":   rule_changes
                })
                print(f"[MODULE2] Kích hoạt kịch bản: '{rule['name']}'")

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
                violations.append({"sensor": sensor, "value": val, "threshold": "max", "limit": hi})
            elif val < lo:
                violations.append({"sensor": sensor, "value": val, "threshold": "min", "limit": lo})
        return {"is_danger": len(violations) > 0, "violations": violations}


class AlertDispatcher:
    def __init__(self, danger_col, channel_col):
        self.danger_col  = danger_col
        self.channel_col = channel_col

    async def dispatch(self, houseid: str, violations: list, sensor_data: dict,
                       device_status_ref: list, triggered_rules: list = None) -> dict:
        tz_vn = timezone(timedelta(hours=7))
        now   = datetime.now(tz_vn)

        # Bật thiết bị báo động
        alert_device_ok = True
        # try:
        #     for item in device_status_ref:
        #         if item[0] == 7:
        #             item[1] = 100
        # except Exception as e:
        #     alert_device_ok = False
        # print(f"[MODULE2][UC002.5] Lỗi kích hoạt thiết bị: {e}")

        # Ghi log nguy hiểm — thêm triggered_rules vào
        danger_log = {
            "_id": now,
            "time": now,
            "houseid": houseid,
            "type": "Vượt ngưỡng an toàn",
            "violations": violations,
            "value": {k: sensor_data.get(k) for k in ("temp", "humi", "light")},
            "alert_device_ok": alert_device_ok,
            "triggered_rules": triggered_rules or [] 
        }
        try:
            await self.danger_col.insert_one(danger_log)
        except Exception as e:
            print(f"[MODULE2] Lỗi ghi danger log: {e}")

        # Gửi thông báo
        channels_doc = await self.channel_col.find_one({"_id": houseid}) or {}
        print(f"[MODULE2] Channels config: {channels_doc}")
        try:
            results = await dispatch_all_channels(
                houseid, violations, sensor_data, channels_doc,
                triggered_rules=triggered_rules or []
            )
            sent_channels = [r.get("channel") for r in results if r.get("ok")]
            failed = [r for r in results if not r.get("ok")]
            if sent_channels:
                print(f"[MODULE2] ✅ Đã gửi thông báo qua: {sent_channels}")
            if failed:
                print(f"[MODULE2] ❌ Gửi thất bại: {failed}")
        except Exception as e:
            print(f"[MODULE2] Lỗi dispatch: {e}")
            sent_channels = []

        return {"dispatched": True, "sent_channels": sent_channels, "alert_device_ok": alert_device_ok}

    async def auto_stop_alert(self, houseid: str, device_status_ref: list, is_danger: bool):
        if not is_danger:
            for item in device_status_ref:
                if item[0] == 7:
                    item[1] = 0
                    print(f"[MODULE2][UC002.5] An toàn trở lại – Tắt còi báo động.")