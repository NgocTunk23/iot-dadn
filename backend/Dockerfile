# Sử dụng Python 3.10 cho tương thích với môi trường của Toon
FROM python:3.10-slim

WORKDIR /app

# Cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code backend và thư mục module
COPY . .

# Chạy server trên cổng 5000 như cấu hình cũ
EXPOSE 5000

CMD ["python", "server.py"]