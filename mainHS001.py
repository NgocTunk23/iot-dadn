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
import music

#? --- CẤU HÌNH ---
SERVER_URL = "http://10.28.128.104:5000/update" 
COMMANDS_URL = "http://10.28.128.104:5000/api/get-commands" 
HOUSEID = "HS001"

tiny_rgb = RGBLed(pin16.pin, 4) 
aiot_dht20 = DHT20()
event_manager.reset()

IDDENCHONGTROM = 1

# ĐÃ SỬA: Chuyển sang dạng Dictionary với Key là ID thiết bị
current_device_status = {
    IDDENCHONGTROM: {"status": False, "type": "denchongtrom"},  # LED ngoài cửa (PIR)
    2: {"status": False, "type": "den"},  # LED trong nhà
    3: {"status": False, "type": "den"},  # LED trong nhà
    4: {"status": False, "type": "den"},  # LED trong nhà

    6: {"status": 0, "type": "servo"},    # Động cơ Servo
    
    7: {"status": 0, "type": "quat"}      # Động cơ Quạt
}

pir_trigger_time = 0
danger_cleared_time = 0  
is_music_playing = False 
is_pir_active = False

#? --- HÀM GỬI DỮ LIỆU (MỖI 10 GIÂY) ---
def on_event_timer_callback_send_data():
    aiot_dht20.read_dht20()
    t = aiot_dht20.dht20_temperature()
    h = aiot_dht20.dht20_humidity()
    l = translate((pin2.read_analog()), 0, 4095, 0, 100)
    
    devices_array = []
    for dev_num, info in current_device_status.items():
        devices_array.append({
            "numberdevice": dev_num, 
            "status": info["status"],
            "type": info["type"]
        })
        
    try:
        payload = {
            "houseid": HOUSEID, 
            "temp": t, 
            "humi": h, 
            "light": l,
            "numberdevices": devices_array, 
            "pir_active": is_pir_active 
        }
        res = urequests.post(SERVER_URL, json=payload)
        print("Đã gửi dữ liệu lên Server thành công!")
        res.close()
    except Exception as e:
        print("Lỗi gửi dữ liệu lên Server:", e)

    gc.collect() 

# --------------------------------------

def check_and_log_motion():
    global pir_trigger_time, is_pir_active
    current_time = time.ticks_ms()
    
    # ĐÃ SỬA: Truy xuất trạng thái qua key ["status"]
    if current_device_status[IDDENCHONGTROM]["status"] == True:
        if pin1.read_digital() == 1:
            tiny_rgb.show(IDDENCHONGTROM, hex_to_rgb("#ffffff"))
            pir_trigger_time = current_time 
            is_pir_active = True  
        else:
            if time.ticks_diff(current_time, pir_trigger_time) > 10000:
                tiny_rgb.show(IDDENCHONGTROM, hex_to_rgb('#000000'))
                is_pir_active = False 
    else:
        tiny_rgb.show(IDDENCHONGTROM, hex_to_rgb('#000000'))
        is_pir_active = False

#? --- HÀM ĐỊNH TUYẾN & ĐIỀU KHIỂN THIẾT BỊ ---
def check_devices(number, status, typ):
    # ĐÃ SỬA: Chỉ cập nhật key ["status"], giữ nguyên key ["type"]
    if typ == "denchongtrom":
        if current_device_status[number]["status"] != status:
            current_device_status[number]["status"] = status
            if status == False:
                tiny_rgb.show(IDDENCHONGTROM, hex_to_rgb("#000000"))
                
    elif typ == "den":
        if current_device_status[number]["status"] != status:
            if status == True:
                tiny_rgb.show(number, hex_to_rgb("#ffffff"))
            else:
                tiny_rgb.show(number, hex_to_rgb("#000000"))
            current_device_status[number]["status"] = status
            
    elif typ == "servo":
        angle = int(status)
        if current_device_status[number]["status"] != angle:
            pin4.servo_write(angle)
            current_device_status[number]["status"] = angle
            
    elif typ == "quat":
        speed = int(status)
        if current_device_status[number]["status"] != speed:
            val = round(translate(speed, 0, 100, 0, 1023))
            pin0.write_analog(val)
            current_device_status[number]["status"] = speed 
#? -----------------------------------------------------------------------------------------

#? Đăng ký sự kiện gửi dữ liệu mỗi 10000ms (10 giây)
event_manager.add_timer_event(10000, on_event_timer_callback_send_data)

#? --- KHỞI ĐẦU ---
display.scroll('BD')
mqtt.connect_wifi('ACLAB', 'ACLAB2023')
mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='xinchao', password='')
display.scroll('ALL')
last_lcd_update = time.ticks_ms()

# --- VÒNG LẶP CHÍNH ---
while True:
    check_and_log_motion() 
    
    # ĐÃ SỬA: Đưa biến cảnh báo ra đầu vòng lặp để tránh NameError 
    is_danger_alert = False 
    
    try: 
        response = urequests.get(COMMANDS_URL)
        if response.status_code == 200:
            data = response.json()
            
            if 'is_danger' in data:
                is_danger_alert = data['is_danger']

            if 'numberdevices' in data:
                commands = data['numberdevices'] 
                for cmd in commands:
                    dev_id = cmd['numberdevice']     
                    dev_status = cmd['status'] 
                    dev_type = cmd['type'] 
                    check_devices(dev_id, dev_status, dev_type)
        response.close()
    except Exception as e:
        print("Lỗi nhận lệnh từ Server:", e)
        try: response.close()
        except: pass

    # Xử lý bật nhạc và đếm 15s để tắt
    if is_danger_alert == True:
        danger_cleared_time = time.ticks_ms()
        if not is_music_playing:
            music.play(music.RINGTONE, wait=False)
            is_music_playing = True
            print("! PHÁT NHẠC CẢNH BÁO NGƯỠNG !")
    else:
        if is_music_playing == True:
            if time.ticks_diff(time.ticks_ms(), danger_cleared_time) > 15000:
                music.stop() 
                is_music_playing = False
                print("- ĐÃ QUA 15S AN TOÀN, TẮT NHẠC -")

    mqtt.check_message()
    event_manager.run()
    time.sleep_ms(100) 
    gc.collect()