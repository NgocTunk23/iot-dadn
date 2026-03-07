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
show collections
# Xem dữ liệu trong database 
docker exec -it iot_mongodb mongosh iot_database --eval "db.sensor_history.find().pretty()"
# Cổng be
http://localhost:5000/
# Cổng fe
http://localhost/
# Lệnh upcode
git add .
git status
git commit -m "Khởi tạo dự án IoT: Backend FastAPI và Frontend React"
git push -u origin main
