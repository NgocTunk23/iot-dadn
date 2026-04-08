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
SERVER_URL = "http://10.28.128.104:5000/update" 
COMMANDS_URL = "http://10.28.128.104:5000/api/get-commands" 
HOUSEID = "HS001"

tiny_rgb = RGBLed(pin16.pin, 4) 
aiot_dht20 = DHT20()
# aiot_lcd1602 = LCD1602()
event_manager.reset()

# ! THÊM MỚI: BỘ NHỚ TRẠNG THÁI THỰC TẾ CỦA YOLOBIT
# Mặc định ban đầu: Đèn tắt (False), Động cơ dừng (0)
current_device_status = {
    1: False, # LED ngoài cửa (PIR)
    2: False, # LED trong nhà
    3: False, # LED trong nhà
    4: False, # LED trong nhà
    5: 0,     # Góc Servo
    6: 0,      # Tốc độ quạt
    7: 0
}
# -----------------
# Biến lưu thời điểm đèn 1 bật do PIR (đơn vị: mili-giây)
pir_trigger_time = 0

# ==================== CODE THÊM MỚI (BẮT ĐẦU) ====================
import music
danger_cleared_time = 0  # Mốc thời gian khi hết nguy hiểm
is_music_playing = False # Cờ đánh dấu nhạc đang kêu hay không
# ==================== CODE THÊM MỚI (KẾT THÚC) ===================

#? --- HÀM GỬI DỮ LIỆU (MỖI 10 GIÂY) ---
def on_event_timer_callback_send_data():
  aiot_dht20.read_dht20()
  t = aiot_dht20.dht20_temperature()
  h = aiot_dht20.dht20_humidity()
  l = translate((pin2.read_analog()), 0, 4095, 0, 100)

  # ! CHUYỂN ĐỔI BỘ NHỚ THÀNH MẢNG OBJECT CHO KHỚP VỚI DATABASE
  devices_array = []
  for dev_num, stat in current_device_status.items():
      devices_array.append({"numberdevice": dev_num, "status": stat})

  try:
    payload = {
        "houseid": HOUSEID, 
        "temp": t, 
        "humi": h, 
        "light": l,
        "numberdevices": devices_array # Gắn mảng thiết bị vào gói tin gửi đi
    }
    res = urequests.post(SERVER_URL, json=payload)
    print("Đã gửi dữ liệu lên Server thành công!")
    res.close()
  except Exception as e:
    print("Lỗi gửi dữ liệu lên Server:", e)

  gc.collect() 
# --------------------------------------


def check_and_log_motion():
    global pir_trigger_time
    current_time = time.ticks_ms()
    
    # CHỈ xử lý cảm biến PIR nếu "công tắc" thiết bị 1 đang BẬT (True)
    if current_device_status.get(1) == True:
        if pin1.read_digital() == 1:
            # Có người -> Giữ đèn sáng và cập nhật mốc thời gian
            tiny_rgb.show(1, hex_to_rgb("#ffffff"))
            pir_trigger_time = current_time 
        else:
            # Không có người -> Kiểm tra xem đã hết 10 giây chưa để tắt đèn tạm thời
            if time.ticks_diff(current_time, pir_trigger_time) > 10000:
                tiny_rgb.show(1, hex_to_rgb('#000000'))
                # Lưu ý: Không set current_device_status[1] = False ở đây 
                # để hệ thống vẫn ở trạng thái "Sẵn sàng chống trộm"
    else:
        # Nếu công tắc đang TẮT, luôn đảm bảo đèn tắt và không đọc PIR
        tiny_rgb.show(1, hex_to_rgb('#000000'))


#? --- HÀM ĐỊNH TUYẾN & ĐIỀU KHIỂN THIẾT BỊ ---
def check_devices(number, status):
    
    # --- XỬ LÝ RIÊNG THIẾT BỊ 1 (CẢM BIẾN CHUYỂN ĐỘNG) ---
    if number == 1:
        if current_device_status[1] != status:
            current_device_status[1] = status # Cập nhật trạng thái kích hoạt/tắt
            
            if status == True:
                print("Hệ thống chống trộm (Đèn 1): ĐÃ KÍCH HOẠT CHỜ")
                # KHÔNG BẬT ĐÈN Ở ĐÂY, để hàm check_and_log_motion tự lo
            else:
                tiny_rgb.show(1, hex_to_rgb("#000000"))
                print("Hệ thống chống trộm (Đèn 1): ĐÃ TẮT HOÀN TOÀN")

    # --- Các đèn LED bình thường (ID: 2, 3, 4) ---
    elif number in [2, 3, 4]:
        if current_device_status[number] != status:
            if status == True:
                tiny_rgb.show(number, hex_to_rgb("#ffffff"))
                print("Đèn LED số", number, ": Đã BẬT")
            else:
                tiny_rgb.show(number, hex_to_rgb("#000000"))
                print("Đèn LED số", number, ": Đã TẮT")
            current_device_status[number] = status

    # --- Nhóm 2: Động cơ Servo (ID: 6) ---
    elif number == 6:
        angle = int(status)
        if current_device_status[6] != angle:
            pin4.servo_write(angle)
            print("Servo (ID 6) quay đến góc:", angle, "độ")
            current_device_status[6] = angle # CẬP NHẬT BỘ NHỚ

    # --- Nhóm 3: Quạt / Động cơ PWM (ID: 7) ---
    elif number == 7:
        speed = int(status)
        if current_device_status[7] != speed:
            val = round(translate(speed, 0, 100, 0, 1023))
            pin0.write_analog(val)
            if speed > 0:
                print("Quạt (ID 7) đang chạy mức:", speed, "%")
            else:
                print("Quạt (ID 7) : Đã TẮT")
            current_device_status[7] = speed # CẬP NHẬT BỘ NHỚ
# -----------------------------------------------------------------------------------------


# Đăng ký sự kiện gửi dữ liệu mỗi 10000ms (10 giây)
event_manager.add_timer_event(10000, on_event_timer_callback_send_data)

#? --- KHỞI ĐẦU ---
display.scroll('BD')
mqtt.connect_wifi('ACLAB', 'ACLAB2023')
mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='xinchao', password='')
# mqtt.on_receive_message('V4', on_mqtt_message_receive_callback__V4_)
display.scroll('ALL')
last_lcd_update = time.ticks_ms()

# --- VÒNG LẶP CHÍNH ---
while True:
    
    check_and_log_motion() 
    
    try: # Nhận lệnh từ Server (Mỗi 5 giây một lần)
        response = urequests.get(COMMANDS_URL)
        is_danger_alert = False # Biến lưu trạng thái cảnh báo nguy hiểm
        
        if response.status_code == 200:
            data = response.json()
            
            # Đọc trạng thái cảnh báo từ Server
            if 'is_danger' in data:
                is_danger_alert = data['is_danger']

            if 'numberdevices' in data:
                commands = data['numberdevices'] 
                
                for cmd in commands:
                    dev_id = cmd['numberdevice']     
                    dev_status = cmd['status'] 
                    
                    check_devices(dev_id, dev_status)
                    
        response.close()

    except Exception as e:
        print("Lỗi nhận lệnh từ Server:", e)
        try: response.close()
        except: pass

    # Phát nhạc vượt ngưỡng khi nhiệt độ cao (báo cháy)
    # ==================== CODE THÊM MỚI (BẮT ĐẦU) ====================
    # Xử lý bật nhạc và đếm 15s để tắt
    if 'is_danger_alert' in locals():
        if is_danger_alert == True:
            # Đang nguy hiểm -> Cập nhật liên tục mốc thời gian và bật nhạc
            danger_cleared_time = time.ticks_ms()
            if not is_music_playing:
                music.play(music.RINGTONE, wait=False)
                is_music_playing = True
                print("! PHÁT NHẠC CẢNH BÁO NGƯỠNG !")
        else:
            # Hết nguy hiểm -> Kiểm tra xem nhạc có đang kêu không và đã qua 15s chưa
            if is_music_playing == True:
                if time.ticks_diff(time.ticks_ms(), danger_cleared_time) > 15000:
                    music.stop() # Tắt nhạc
                    is_music_playing = False
                    print("- ĐÃ QUA 15S AN TOÀN, TẮT NHẠC -")
    # ==================== CODE THÊM MỚI (KẾT THÚC) ===================

    mqtt.check_message()
    event_manager.run()
    time.sleep_ms(100) # Giữ nguyên 100ms của bạn để API phản hồi nhanh
    gc.collect()