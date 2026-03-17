import requests
import time

BASE_URL = "http://localhost:5000/api"

def test_control():
    print("Testing /api/control...")
    payload = {"commands": [[1, True], [5, 45]]} # Đèn 1 bật, Servo 5 quay 45 độ
    res = requests.post(f"{BASE_URL}/control", json=payload)
    print("Response:", res.status_code, res.json())

def test_create_mode():
    print("\nTesting /api/modes (Create)...")
    payload = {
        "name": "Báo Động", 
        "commands": [[1, True], [6, 100]] # Đèn 1 bật báo trộm, quạt 6 chạy 100
    }
    res = requests.post(f"{BASE_URL}/modes", json=payload)
    print("Response:", res.status_code, res.json())

def test_get_modes():
    print("\nTesting GET /api/modes...")
    res = requests.get(f"{BASE_URL}/modes")
    print("Response:", res.status_code, res.json())

def test_activate_mode():
    print("\nTesting /api/modes/activate...")
    payload = {"name": "Báo Động"}
    res = requests.post(f"{BASE_URL}/modes/activate", json=payload)
    print("Response:", res.status_code, res.json())

def test_get_logs():
    print("\nTesting GET /api/logs?category=actions...")
    res = requests.get(f"{BASE_URL}/logs?category=actions")
    print("Response:", res.status_code, res.json())

if __name__ == "__main__":
    time.sleep(2) # Đợi server khởi động
    test_control()
    test_create_mode()
    test_get_modes()
    test_activate_mode()
    test_get_logs()
    print("\nFinished testing.")
