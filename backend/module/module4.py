from datetime import datetime, timezone, timedelta


class LogManager:
    def __init__(self, logs_collection, config_collection):
        self.logs_collection = logs_collection
        self.config_collection = config_collection
        self.tz_vn = timezone(timedelta(hours=7))

    # =====================
    # UC004.6 - LOG EVENT
    # =====================
    async def log_event(self, device_id, level, message, value=None):
        log_data = {
            "device_id": device_id,
            "level": level,
            "message": message,
            "value": value,
            "timestamp": datetime.now(self.tz_vn),
        }

        await self.logs_collection.insert_one(log_data)
        return {"status": "success"}

    # =====================
    # UC004.2 - LOG LEVEL
    # =====================
    async def set_log_level(self, level):
        await self.config_collection.update_one(
            {"type": "logging"}, {"$set": {"level": level}}, upsert=True
        )
        return {"status": "success"}

    # =====================
    # UC004.1 - STRATEGY
    # =====================
    async def set_strategy(self, strategy):
        await self.config_collection.update_one(
            {"type": "analysis"}, {"$set": {"strategy": strategy}}, upsert=True
        )
        return {"status": "success"}

    # =====================
    # UC004.5 - GET LOG
    # =====================
    async def get_logs(self, query={}):
        cursor = self.logs_collection.find(query).sort("timestamp", -1)
        logs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            logs.append(doc)
        return logs

    # =====================
    # UC004.3 + UC004.4
    # =====================
    async def get_report(self, query={}):
        logs = await self.get_logs(query)

        config = await self.config_collection.find_one({"type": "analysis"})
        strategy = config.get("strategy", "frequency") if config else "frequency"

        return analyze_logs(logs, strategy)


# =====================
# CORE ANALYSIS
# =====================
def analyze_logs(logs, strategy):
    result = {}

    if strategy == "frequency":
        for log in logs:
            level = log.get("level")
            result[level] = result.get(level, 0) + 1

    elif strategy == "average":
        sum_val = {}
        count = {}

        for log in logs:
            dev = log.get("device_id")
            val = log.get("value")

            if isinstance(val, (int, float)):
                sum_val[dev] = sum_val.get(dev, 0) + val
                count[dev] = count.get(dev, 0) + 1

        for dev in sum_val:
            result[dev] = sum_val[dev] / count[dev]

    return {"strategy": strategy, "data": result}
