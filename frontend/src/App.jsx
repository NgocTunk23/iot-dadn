// import React, { useState, useEffect } from 'react';
// import axios from 'axios';

// function App() {
//   const [data, setData] = useState({ temp: '--', humi: '--', light: '--', time: '--' });
//   const [error, setError] = useState(null);

//   // URL backend - Lưu ý: Nếu chạy Docker/WSL, hãy chắc chắn port 5000 đã được map
//   const API_URL = 'http://localhost:5000/api/sensor-data';

//   const fetchSensorData = async () => {
//     try {
//       const response = await axios.get(API_URL);
//       if (response.status === 200) {
//         setData(response.data);
//         setError(null);
//       }
//     } catch (err) {
//       console.error("Lỗi kết nối Backend:", err);
//       setError("Mất kết nối với Server");
//     }
//   };

//   useEffect(() => {
//     // Lấy dữ liệu ngay lập tức khi load trang
//     fetchSensorData();
    
//     // Cập nhật mỗi 3 giây
//     const timer = setInterval(fetchSensorData, 3000); 
//     return () => clearInterval(timer);
//   }, []);

//   return (
//     <div style={styles.container}>
//       <h1 style={styles.title}>IoT Dashboard - Hệ Thống Giám Sát</h1>
      
//       {error && <p style={styles.error}>{error}</p>}

//       <div style={styles.cardContainer}>
//         <div style={styles.card}>
//           <h2 style={styles.label}>Nhiệt độ</h2>
//           <p style={{...styles.value, color: '#ff4d4d'}}>{data.temp}°C</p>
//         </div>

//         <div style={styles.card}>
//           <h2 style={styles.label}>Độ ẩm</h2>
//           <p style={{...styles.value, color: '#3399ff'}}>{data.humi}%</p>
//         </div>

//         <div style={styles.card}>
//           <h2 style={styles.label}>Ánh sáng</h2>
//           <p style={{...styles.value, color: '#ffcc00'}}>{data.light}%</p>
//         </div>
//       </div>

//       <div style={styles.footer}>
//         <p>Trạng thái: <span style={{color: '#00ff00'}}>Đang trực tuyến</span></p>
//         <p>Cập nhật cuối: {data.time}</p>
//       </div>
//     </div>
//   );
// }

// // CSS-in-JS cơ bản
// const styles = {
//   container: {
//     textAlign: 'center',
//     backgroundColor: '#1a1a2e',
//     color: 'white',
//     minHeight: '100vh',
//     padding: '40px 20px',
//     fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif'
//   },
//   title: { marginBottom: '40px', fontSize: '2.5rem', fontWeight: 'bold' },
//   cardContainer: { display: 'flex', justifyContent: 'center', gap: '20px', flexWrap: 'wrap' },
//   card: {
//     background: '#16213e',
//     padding: '30px',
//     borderRadius: '15px',
//     boxShadow: '0 10px 20px rgba(0,0,0,0.3)',
//     width: '200px',
//     border: '1px solid #0f3460'
//   },
//   label: { fontSize: '1.2rem', color: '#8892b0', marginBottom: '10px' },
//   value: { fontSize: '3rem', margin: '0', fontWeight: 'bold' },
//   error: { color: '#ff4d4d', background: 'rgba(255,77,77,0.1)', padding: '10px', borderRadius: '5px' },
//   footer: { marginTop: '50px', color: '#8892b0', fontSize: '0.9rem' }
// };

// export default App;





import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  // Cập nhật state mặc định để chứa thêm houseid và mảng numberdevices
  const [data, setData] = useState({ 
    temp: '--', 
    humi: '--', 
    light: '--', 
    time: '--',
    houseid: 'Đang tải...',
    numberdevices: []
  });
  const [error, setError] = useState(null);

  // URL backend
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

      {/* Hiển thị Mã Nhà (houseid) */}
      <div style={styles.houseIdBadge}>
        Mã Nhà: {data.houseid}
      </div>

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

      {/* Vùng hiển thị trạng thái mảng thiết bị (numberdevices) */}
      <h2 style={styles.subTitle}>Trạng Thái Thiết Bị</h2>
      <div style={styles.deviceContainer}>
        {data.numberdevices && data.numberdevices.map((device, index) => (
          <div key={index} style={styles.deviceCard}>
            <h3 style={styles.deviceLabel}>Thiết bị số {device.numberdevice}</h3>
            <p style={styles.deviceStatus}>
              {/* Phân loại cách hiển thị: Bật/Tắt (cho boolean) hoặc Mức (cho số) */}
              {typeof device.status === 'boolean'
                ? (device.status ? '🟢 Đang Bật' : '🔴 Đã Tắt')
                : `Mức độ: ${device.status}`
              }
            </p>
          </div>
        ))}
        {(!data.numberdevices || data.numberdevices.length === 0) && (
          <p style={{ color: '#8892b0' }}>Chưa có dữ liệu thiết bị</p>
        )}
      </div>

      <div style={styles.footer}>
        <p>Trạng thái: <span style={{color: '#00ff00'}}>Đang trực tuyến</span></p>
        <p>Cập nhật cuối: {data.time}</p>
      </div>
    </div>
  );
}

// CSS-in-JS đã được bổ sung thêm style cho houseid và thẻ thiết bị
const styles = {
  container: {
    textAlign: 'center',
    backgroundColor: '#1a1a2e',
    color: 'white',
    minHeight: '100vh',
    padding: '40px 20px',
    fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif'
  },
  title: { marginBottom: '20px', fontSize: '2.5rem', fontWeight: 'bold' },
  subTitle: { marginTop: '50px', marginBottom: '20px', fontSize: '1.8rem', color: '#e6e6e6' },
  houseIdBadge: {
    display: 'inline-block',
    backgroundColor: '#e94560',
    color: 'white',
    padding: '10px 25px',
    borderRadius: '25px',
    fontWeight: 'bold',
    marginBottom: '40px',
    fontSize: '1.2rem',
    boxShadow: '0 4px 6px rgba(0,0,0,0.2)'
  },
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
  deviceContainer: { display: 'flex', justifyContent: 'center', gap: '15px', flexWrap: 'wrap' },
  deviceCard: {
    background: '#0f3460',
    padding: '20px',
    borderRadius: '10px',
    width: '180px',
    border: '1px solid #16213e'
  },
  deviceLabel: { fontSize: '1.1rem', color: '#fff', marginBottom: '10px' },
  deviceStatus: { fontSize: '1.2rem', fontWeight: 'bold', color: '#4dff4d' },
  footer: { marginTop: '50px', color: '#8892b0', fontSize: '0.9rem' }
};

export default App;