from yolobit import *
import time
from mqtt import *
from aiot_rgbled import RGBLed
from machine import Pin, SoftI2C
from aiot_dht20 import DHT20
from event_manager import *
from aiot_lcd1602 import LCD1602
from aiot_ir_receiver import *
import urequests
import gc


#? --- CẤU HÌNH ---
SERVER_URL = "http://10.28.128.81:5000/update" # IP Laptop của bạn
tiny_rgb = RGBLed(pin16.pin, 4) # LED RGB nhỏ gắn trên board (chân 16) 1 là ngoài cửa báo trộm, 2 3 4 là đèn trong nhà 
aiot_dht20 = DHT20()
aiot_lcd1602 = LCD1602()
status = 0
event_manager.reset()

# -----------------


#? --- HÀM GỬI DỮ LIỆU (MỖI 10 GIÂY) ---
def on_event_timer_callback_send_data():
  aiot_dht20.read_dht20()
  t = aiot_dht20.dht20_temperature()
  h = aiot_dht20.dht20_humidity()
  l = translate((pin2.read_analog()), 0, 4095, 0, 100)

  
  # 2. Gửi lên Flask Server (Laptop)
  try:
    payload = {"temp": t, "humi": h, "light": l}
    res = urequests.post(SERVER_URL, json=payload)
    print("Đã gửi dữ liệu lên Server:", res.text)
    res.close()
  except Exception as e:
    print("Lỗi gửi dữ liệu lên Server:", e)

  # # 3. Gửi thông báo Telegram
  # try:
  #   telegram_url = 'https://api.telegram.org/bot8303000903:AAEhkqa47g8sroJqP-riayYVri5UjY6b7rI/sendMessage?text=Cập_nhật_dữ_liệu&chat_id=-5054028151'
  #   res_tg = urequests.get(telegram_url)
  #   res_tg.close()
  # except:
  #   pass

  gc.collect()
# --------------------------------------


#? --- HÀM ĐIỀU KHIỂN SERVO nếu muốn chọn thiết bị thì truyền thêm 1 tham số dô rồi if else
def control_servo(angle):
    pin4.servo_write(angle)
    print("Servo quay đến góc:", angle, "độ")
# -----------------------------------------------------------------------------------------


#? --- HÀM ĐIỀU KHIỂN QUẠT (PWM) --- nếu muốn chọn thiết bị thì truyền thêm 1 tham số dô rồi if else
def control_fan(speed_percent):
    # Chuyển đổi từ tỉ lệ % (0-100) sang giá trị Analog (0-1023)
    val = round(translate(speed_percent, 0, 100, 0, 1023))
    pin0.write_analog(val)
    if speed_percent > 0:
        print("Quạt đang chạy:", speed_percent, "%")
    else:
        print("Đã tắt quạt")
# -----------------------------------------------------------------------------------------


#? --- HÀM KIỂM TRA VÀ GHI LOG cho cảm biến chuyển động--- ĐÈN NGOÀI CỬA báo trộm buổi tối
def check_and_log_motion():
    # Đọc tín hiệu số từ chân pin1 (Cảm biến PIR)
    if pin1.read_digital() == 1:
        # Phát hiện có người: Bật LED 1 màu trắng
        tiny_rgb.show(1, hex_to_rgb("#ffffff"))
    else:
        # Không có người: Tắt LED 1
        tiny_rgb.show(1, hex_to_rgb('#000000'))
# -----------------------------------------------------------------------------------------

#? -----------------------------------------------------------------------------------------
def check_devices(number, status):
    # --- TRƯỜNG HỢP 1: KIỂU BOOLEAN 
    if type(status) == bool:
        if status == True and number !=1: # 2 3 4 là đèn trong nhà, nếu status True thì bật đèn, False thì tắt đèn 2 3 4 
            tiny_rgb.show(number, hex_to_rgb("#ffffff"))
            print("Thiết bị", number, ": Đã BẬT")
        else:
            tiny_rgb.show(number, hex_to_rgb("#000000"))
            print("Thiết bị", number, ": Đã TẮT")

    # --- TRƯỜNG HỢP 2: KIỂU INTEGER
    elif type(status) == int:
        if number == 6:
            # Chuyển đổi % (0-100) sang Analog (0-1023)
            val = round(translate(status, 0, 100, 0, 1023))
            pin0.write_analog(val)
            print("Quạt (ID 6) chạy với tốc độ:", status, "%")
            
        elif number == 5:
            # Quay Servo đến góc 'status'
            pin4.servo_write(status)
            print("Servo (ID 4) quay đến góc:", status, "độ")
# -----------------------------------------------------------------------------------------


#? Đăng ký sự kiện chạy mỗi 10000ms (10 giây)
event_manager.add_timer_event(10000, on_event_timer_callback_send_data)
#? --- KHỞI ĐẦU ---
display.scroll('BĐ')
# Kết nối WiFi và MQTT Broker
mqtt.connect_wifi('ACLAB', 'ACLAB2023')
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! có thể bỏ 
mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='xinchao', password='')
mqtt.on_receive_message('V4', on_mqtt_message_receive_callback__V4_)
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
display.scroll('ALL')
# --- VÒNG LẶP CHÍNH ---
while True:
    # Gọi hàm kiểm tra cảm biến chuyển động
    check_and_log_motion() #! Cảm biến chuyển động bật đèn vào buổi tối, cần xét thêm điều kiện
    try:
        # 1. Gửi yêu cầu lấy lệnh từ Server (Timeout 2s để tránh treo mạch)
        response = urequests.get("http://10.28.128.81:5000/api/get-commands")
        
        # 2. Kiểm tra nếu phản hồi thành công (Status 200 OK)
        if response.status_code == 200:
            data = response.json()
            
            # Kiểm tra xem có trường 'numberdevice' trong dữ liệu không
            if 'numberdevice' in data:
                commands = data['numberdevice'] # Lấy mảng [[2, True], [6, 80]]
                
                # Duyệt qua từng cặp lệnh trong danh sách
                for cmd in commands:
                    dev_id = cmd[0]     # Ví dụ: 2
                    dev_status = cmd[1] # Ví dụ: True hoặc 80
                    
                    # GỌI HÀM THỰC THI
                    check_devices(dev_id, dev_status)
        
        # 3. QUAN TRỌNG: Phải đóng kết nối để giải phóng RAM
        response.close()

    except Exception as e:
        # In ra lỗi nếu mất WiFi hoặc Server sập để dễ debug
        print("Lỗi nhận lệnh từ Server:", e)
        # Nếu có lỗi, đảm bảo giải phóng bộ nhớ nếu biến response đã tồn tại
        try: response.close()
        except: pass



    # Đọc cảm biến DHT20 
    aiot_dht20.read_dht20()
    # Xóa sạch màn hình LCD trước khi hiển thị dữ liệu mới
    aiot_lcd1602.clear()
    # Nhảy đến tọa độ (0, 0) và hiển thị nhiệt độ
    aiot_lcd1602.move_to(0, 0)
    aiot_lcd1602.putstr('ND:' + str(aiot_dht20.dht20_temperature()))
    # Nhảy đến tọa độ (8, 0) và hiển thị độ ẩm
    aiot_lcd1602.move_to(8, 0)
    aiot_lcd1602.putstr('DA:' + str(aiot_dht20.dht20_humidity()))
    # Nhảy đến tọa độ (0, 1) và hiển thị ánh sáng
    aiot_lcd1602.move_to(0, 1)
    aiot_lcd1602.putstr('AS:' + str(translate((pin2.read_analog()), 0, 4095, 0, 100)))
    #! Lệnh tiếp nhạn dữ liệu từ server mqtt nhưng sau đó ta sẽ sài bằng server.py, ta chỉ bổ sung chứ không xóa code chỗ này để tránh lỗi
    mqtt.check_message()
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Chạy sự kiện ví dụ gửi dữ liệu mỗi 10 giây lên server.py
    event_manager.run()
    # Đợi 5 giây trước khi vòng lặp tiếp theo chạy để tránh quá tải CPU và mạng cũng như reset màn hình LCD 
    time.sleep_ms(5000)