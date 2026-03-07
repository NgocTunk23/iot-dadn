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

# --- CẤU HÌNH ---
SERVER_URL = "http://10.28.128.81:5000/update" # IP Laptop của bạn
tiny_rgb = RGBLed(pin16.pin, 4)
aiot_dht20 = DHT20()
aiot_lcd1602 = LCD1602()
status = 0
event_manager.reset()

# --- HÀM XỬ LÝ MQTT ---
def on_mqtt_message_receive_callback__V4_(msg):
  if msg == '1':
    tiny_rgb.show(4, hex_to_rgb('#ffff00'))
  else:
    tiny_rgb.show(4, hex_to_rgb('#0000ff'))

# --- HÀM XỬ LÝ IR (REMOTE) ---
aiot_ir_rx = IR_RX(Pin(pin10.pin, Pin.IN))
aiot_ir_rx.start()

def on_ir_receive_callback(t_in_hieu, addr, ext):
  global status
  if aiot_ir_rx.get_code() == IR_REMOTE_A:
    if status == 0:
      tiny_rgb.show(2, hex_to_rgb('#0000ff'))
      status = 1
    else:
      tiny_rgb.show(2, hex_to_rgb('#000000'))
      status = 0
  aiot_ir_rx.clear_code()

aiot_ir_rx.on_received(on_ir_receive_callback)

# --- HÀM GỬI DỮ LIỆU (MỖI 5 GIÂY) ---
def on_event_timer_callback_send_data():
  aiot_dht20.read_dht20()
  t = aiot_dht20.dht20_temperature()
  h = aiot_dht20.dht20_humidity()
  l = translate((pin2.read_analog()), 0, 4095, 0, 100)
  
  # 1. Gửi lên MQTT OhStem
  mqtt.publish('V1', t)
  mqtt.publish('V2', h)
  mqtt.publish('V3', l)
  
  # 2. Gửi lên Flask Server (Laptop)
  try:
    payload = {"temp": t, "humi": h, "light": l}
    res = urequests.post(SERVER_URL, json=payload)
    print("Đã gửi Flask:", res.text)
    res.close()
  except Exception as e:
    print("Lỗi gửi Flask:", e)

  # 3. Gửi thông báo Telegram
  try:
    telegram_url = 'https://api.telegram.org/bot8303000903:AAEhkqa47g8sroJqP-riayYVri5UjY6b7rI/sendMessage?text=Cập_nhật_dữ_liệu&chat_id=-5054028151'
    res_tg = urequests.get(telegram_url)
    res_tg.close()
  except:
    pass

  gc.collect()

# Đăng ký sự kiện chạy mỗi 5000ms (5 giây)
event_manager.add_timer_event(5000, on_event_timer_callback_send_data)

# --- KHỞI ĐẦU ---
display.scroll('M')
mqtt.connect_wifi('ACLAB', 'ACLAB2023')
mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='xinchao', password='')
mqtt.on_receive_message('V4', on_mqtt_message_receive_callback__V4_)
display.scroll('ALL')

# --- VÒNG LẶP CHÍNH ---
while True:
  # Cảm biến chuyển động bật đèn đỏ
  if pin1.read_digital() == 1:
    tiny_rgb.show(1, hex_to_rgb('#ff0000'))
  else:
    tiny_rgb.show(1, hex_to_rgb('#000000'))
  
  # Cập nhật LCD
  aiot_dht20.read_dht20()
  aiot_lcd1602.clear()
  aiot_lcd1602.move_to(0, 0)
  aiot_lcd1602.putstr('ND:' + str(aiot_dht20.dht20_temperature()))
  aiot_lcd1602.move_to(8, 0)
  aiot_lcd1602.putstr('DA:' + str(aiot_dht20.dht20_humidity()))
  aiot_lcd1602.move_to(0, 1)
  aiot_lcd1602.putstr('AS:' + str(translate((pin2.read_analog()), 0, 4095, 0, 100)))
  
  mqtt.check_message()
  event_manager.run()
  time.sleep_ms(1000)