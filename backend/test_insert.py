# test_insert.py — tạo file này trong thư mục backend rồi chạy
from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient("mongodb://localhost:27017")
db = client.iot_database

now = datetime.now()

# 1. Sensor_history
db.Sensor_history.insert_many(
    [
        {
            "time": now - timedelta(minutes=i * 5),
            "temp": 28 + i,
            "humi": 65 + i,
            "light": 50 + i,
            "houseid": "HS001",
        }
        for i in range(25)
    ]
)

# 2. Danger_log
db.Danger_log.insert_many(
    [
        {
            "time": now - timedelta(minutes=10),
            "houseid": "HS001",
            "violations": [{"sensor": "temp", "value": 45}],
        },
        {
            "time": now - timedelta(minutes=20),
            "houseid": "HS001",
            "violations": [{"sensor": "humi", "value": 85}],
        },
        {
            "time": now - timedelta(minutes=30),
            "houseid": "HS001",
            "violations": [{"sensor": "temp", "value": 38}],
        },
    ]
)

# 3. Device_log
db.Device_log.insert_many(
    [
        {
            "time": now - timedelta(minutes=5),
            "numberdevice": 1,
            "old_status": False,
            "new_status": True,
            "reason": "do người dùng bật thủ công",
        },
        {
            "time": now - timedelta(minutes=15),
            "numberdevice": 2,
            "old_status": True,
            "new_status": False,
            "reason": "do hệ thống tự động bật (chống trộm)",
        },
        {
            "time": now - timedelta(minutes=25),
            "numberdevice": 5,
            "old_status": False,
            "new_status": True,
            "reason": "do người dùng bật thủ công",
        },
    ]
)

# 4. System_update_log
db.System_update_log.insert_many(
    [
        {
            "time": now - timedelta(hours=1),
            "field": "temp.max",
            "old_value": "40",
            "new_value": "35",
        },
        {
            "time": now - timedelta(hours=2),
            "field": "humi.max",
            "old_value": "80",
            "new_value": "75",
        },
    ]
)

print("✅ Insert xong!")
client.close()
