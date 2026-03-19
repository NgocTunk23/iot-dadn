# 🌐 Hệ Thống Giám Sát và Điều Khiển Thiết Bị IoT (IoT Dashboard System)
## 📖 Tổng quan dự án

Đây là hệ thống IoT toàn diện được phát triển nhằm mục đích thu thập, giám sát dữ liệu môi trường theo thời gian thực và điều khiển các thiết bị ngoại vi từ xa. Dự án bao gồm một ứng dụng Web (Full-stack) giao tiếp với các thiết bị phần cứng thông qua giao thức MQTT, được container hóa hoàn toàn bằng Docker để dễ dàng triển khai.

## ✨ Tính năng nổi bật

- **📊 Giám sát thời gian thực:** Thu thập và hiển thị liên tục các thông số môi trường (Nhiệt độ, Độ ẩm, Ánh sáng) lên hệ thống biểu đồ trực quan (SensorChart).
- **🎛️ Điều khiển thiết bị từ xa:** Giao diện điều khiển (DeviceControls) cho phép người dùng thao tác bật/tắt các thiết bị ngoại vi như đèn LED và động cơ Servo ngay trên trình duyệt.
- **💾 Lưu trữ & Quản lý lịch sử:** Ghi log toàn bộ dữ liệu cảm biến và lịch sử thao tác điều khiển thiết bị vào cơ sở dữ liệu để phục vụ truy xuất và phân tích.
- **🐳 Triển khai linh hoạt:** Toàn bộ Frontend, Backend và các services liên quan được cấu hình chạy đồng bộ chỉ với một lệnh thông qua `docker-compose`.

## 🛠️ Công nghệ sử dụng

### Frontend (Giao diện người dùng)
- **Framework:** ReactJS, Vite
- **Thành phần:** Giao diện được chia module rõ ràng (Dashboard, Sidebar, DevicesTab, SettingsTab) để tối ưu trải nghiệm người dùng và dễ bảo trì.

### Backend (Máy chủ & Xử lý dữ liệu)
- **Ngôn ngữ:** Python (Tích hợp mock_server để test luồng dữ liệu khi không có kết nối phần cứng).
- **Giao thức:** Truyền nhận tin nhắn qua MQTT, xử lý và định tuyến dữ liệu.

### Hardware (Thiết bị IoT)
- **Vi điều khiển:** Yolobit.
- **Cảm biến & Khối chấp hành:** Cảm biến nhiệt độ, độ ẩm, ánh sáng; Đèn LED, động cơ Servo.


## 📁 Cấu trúc thư mục chính

```text
📦 iot-dadn
 ┣ 📂 backend           # Chứa mã nguồn máy chủ Python, model dữ liệu và script import log
 ┃ ┣ 📜 Dockerfile
 ┃ ┣ 📜 server.py       # Điểm entry chính của server
 ┃ ┗ 📜 requirements.txt
 ┣ 📂 frontend          # Mã nguồn giao diện React (Vite)
 ┃ ┣ 📂 src/components  # Chứa các UI Components (Dashboard, Chart, Controls...)
 ┃ ┣ 📜 Dockerfile
 ┃ ┗ 📜 package.json
 ┣ 📜 docker-compose.yml # File cấu hình triển khai toàn hệ thống
 ┗ 📜 main.py / main2.py # Các script xử lý luồng dữ liệu trung tâm
```

## Hướng dẫn cài đặt và khởi chạy
Dự án sử dụng Docker để đơn giản hóa quá trình triển khai. Đảm bảo máy tính của bạn đã cài đặt Docker và Docker Compose.

### Bước 1: Clone kho lưu trữ về máy

Bash
git clone [https://github.com/ngoctunk23/iot-dadn.git](https://github.com/ngoctunk23/iot-dadn.git)
cd iot-dadn

### Bước 2: Khởi chạy hệ thống bằng Docker Compose
Chỉ với một lệnh duy nhất, Docker sẽ tự động build images và chạy các containers cho cả Frontend và Backend:

Bash
docker-compose up --build

### Bước 3: Truy cập ứng dụng

Frontend Web: http://localhost:80

Backend API: http://localhost:5000/api/
