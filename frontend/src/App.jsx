import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [data, setData] = useState({ temp: '--', humi: '--', light: '--', time: '--' });
  const [error, setError] = useState(null);

  // URL backend - Lưu ý: Nếu chạy Docker/WSL, hãy chắc chắn port 5000 đã được map
  const API_URL = 'http://localhost:5000/api/sensor-data';

  const fetchSensorData = async () => {
    try {
      const response = await axios.get(API_URL);
      if (response.status === 200) {
        setData(response.data);
        setError(null);
      }
    } catch (err) {
      console.error("Lỗi kết nối Backend:", err);
      setError("Mất kết nối với Server");
    }
  };

  useEffect(() => {
    // Lấy dữ liệu ngay lập tức khi load trang
    fetchSensorData();
    
    // Cập nhật mỗi 3 giây
    const timer = setInterval(fetchSensorData, 3000); 
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>IoT Dashboard - Hệ Thống Giám Sát</h1>
      
      {error && <p style={styles.error}>{error}</p>}
      
      {/* Cảnh báo mất kết nối (UC001.3) */}
      {data.connected === false && (
         <div style={styles.warningBox}>
            ⚠️ CẢNH BÁO: Mất kết nối với thiết bị Cảm biến! Hệ thống không nhận được dữ liệu mới.
         </div>
      )}

      <div style={styles.cardContainer}>
        <div style={styles.card}>
          <h2 style={styles.label}>Nhiệt độ</h2>
          <p style={{...styles.value, color: '#ff4d4d'}}>{data.temp}°C</p>
        </div>

        <div style={styles.card}>
          <h2 style={styles.label}>Độ ẩm</h2>
          <p style={{...styles.value, color: '#3399ff'}}>{data.humi}%</p>
        </div>

        <div style={styles.card}>
          <h2 style={styles.label}>Ánh sáng</h2>
          <p style={{...styles.value, color: '#ffcc00'}}>{data.light}%</p>
        </div>
      </div>

      <div style={styles.footer}>
        <p>Trạng thái: 
          <span style={{color: data.connected !== false ? '#00ff00' : '#ff4d4d', fontWeight: 'bold', marginLeft: '8px'}}>
            {data.connected !== false ? 'Đang trực tuyến' : 'Ngoại tuyến (Mất kết nối)'}
          </span>
        </p>
        <p>Cập nhật cuối: {data.time}</p>
      </div>
    </div>
  );
}

// CSS-in-JS cơ bản
const styles = {
  container: {
    textAlign: 'center',
    backgroundColor: '#1a1a2e',
    color: 'white',
    minHeight: '100vh',
    padding: '40px 20px',
    fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif'
  },
  title: { marginBottom: '40px', fontSize: '2.5rem', fontWeight: 'bold' },
  cardContainer: { display: 'flex', justifyContent: 'center', gap: '20px', flexWrap: 'wrap' },
  card: {
    background: '#16213e',
    padding: '30px',
    borderRadius: '15px',
    boxShadow: '0 10px 20px rgba(0,0,0,0.3)',
    width: '200px',
    border: '1px solid #0f3460'
  },
  label: { fontSize: '1.2rem', color: '#8892b0', marginBottom: '10px' },
  value: { fontSize: '3rem', margin: '0', fontWeight: 'bold' },
  error: { color: '#ff4d4d', background: 'rgba(255,77,77,0.1)', padding: '10px', borderRadius: '5px' },
  warningBox: {
    backgroundColor: 'rgba(255, 77, 77, 0.15)',
    border: '1px solid #ff4d4d',
    color: '#ff4d4d',
    padding: '15px',
    borderRadius: '10px',
    marginBottom: '30px',
    fontWeight: 'bold',
    fontSize: '1.1rem',
    maxWidth: '600px',
    margin: '0 auto 30px auto'
  },
  footer: { marginTop: '50px', color: '#8892b0', fontSize: '0.9rem' }
};

export default App;