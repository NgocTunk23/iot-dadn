# Lệnh chạy
docker compose up --build
# Lệnh tắt 
docker compose down -v



# Lệnh tạo dữ liệu mẫu để sài chỉ gọi 1 lần
python3 backend/import_logs.py
# Truy vấn ngày 06/03/2026
curl -s "http://localhost:5000/api/history" | jq '.'



# Reset dữ liệu trong database nếu chạy lệnh tạo dữ liệu mẫu 2 lần
docker exec -it iot_mongodb mongosh
use iot_database
db.sensor_history.deleteMany({})

# Xem tất cả dữ liệu trong database 
docker exec -it iot_mongodb mongosh iot_database --eval "db.getCollectionNames().forEach(function(coll) { print('--- Collection: ' + coll + ' ---'); printjson(db[coll].find().toArray()); })"


# Cổng be
http://localhost:5000/
# Cổng fe
http://localhost:80
# Cổng dữ liệu cảm biến
http://localhost:5000/api/sensor-data


# Các tính năng cần thêm trong giao cái api
dữ liệu vượt ngưỡng thì màn hình lcd sẽ hiện ra thông báp thay vì cập nhật 3 chỉ số + 1 đèn báo đỏ
 