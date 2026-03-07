import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [data, setData] = useState({ temp: '--', humi: '--', light: '--', time: '--' });

  // Gọi API lấy dữ liệu từ Backend (Port 5000)
  const fetchSensorData = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/sensor-data');
      if (response.status === 200) setData(response.data);
    } catch (err) {
      console.error("Không kết nối được Backend!");
    }
  };

  useEffect(() => {
    const timer = setInterval(fetchSensorData, 3000); // Cập nhật mỗi 3 giây
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{ textAlign: 'center', backgroundColor: '#282c34', color: 'white', minHeight: '100vh', padding: '20px' }}>
      <h1>IoT Dashboard - DOAN_DA_NGANH</h1>
      <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '50px' }}>
        <div className="card"> <h2>Nhiệt độ</h2> <p style={{ fontSize: '3rem' }}>{data.temp}°C</p> </div>
        <div className="card"> <h2>Độ ẩm</h2> <p style={{ fontSize: '3rem' }}>{data.humi}%</p> </div>
        <div className="card"> <h2>Ánh sáng</h2> <p style={{ fontSize: '3rem' }}>{data.light}%</p> </div>
      </div>
      <p>Cập nhật cuối: {data.time}</p>
    </div>
  );
}

export default App;