import React, { useState, useEffect } from 'react';

export default function SettingsTab({ onLogout }) {
  const [houseInfo, setHouseInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [localCreds, setLocalCreds] = useState({ houseid: '', username: '' });

  useEffect(() => {
    // 1. Đọc dữ liệu từ Local Storage
    let houseid = localStorage.getItem('houseid') || '';
    let userRaw = localStorage.getItem('username') || '';
    
    let username = "";
    try {
      const userObj = JSON.parse(userRaw);
      username = userObj.username || userRaw; 
    } catch {
      username = userRaw;
    }

    // Xóa sạch dấu nháy kép/nháy đơn ở 2 đầu chuỗi để gửi lên Backend chuẩn xác
    if (typeof username === 'string') username = username.replace(/^["']|["']$/g, '');
    if (typeof houseid === 'string') houseid = houseid.replace(/^["']|["']$/g, '');

    setLocalCreds({ houseid, username });

    // 2. Gọi API tra cứu thông tin
    if (houseid && username) {
      fetch(`http://localhost:5000/api/house-info?houseid=${houseid}&username=${username}`)
        .then(res => res.json())
        .then(data => {
          if (!data.error) {
            setHouseInfo(data);
          }
          setLoading(false);
        })
        .catch(err => {
          console.error("[SettingsTab] Lỗi lấy thông tin nhà:", err);
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('houseid');
    localStorage.removeItem('user');
    sessionStorage.removeItem('user');

    if (onLogout) {
      onLogout();
    } else {
      window.location.reload(); 
    }
  };

  return (
    <div className="control-panel">
      <h3 style={{ marginBottom: '18px', color: '#ffffff', fontWeight: 'bold' }}>THÔNG TIN NGÔI NHÀ</h3>
      
      {/* KHU VỰC HIỂN THỊ THÔNG TIN NHÀ */}
      {loading ? (
        <p style={{ color: '#ffffff', marginBottom: '24px' }}>Đang tải dữ liệu...</p>
      ) : houseInfo ? (
        <div style={{ 
          marginBottom: '24px', 
          padding: '16px', 
          backgroundColor: 'rgba(255, 255, 255, 0.05)', // Nền trắng mờ 5% (trong suốt)
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.1)', // Viền mờ
          color: '#ffffff' // Chữ trắng xám
        }}>
          {/* Thông tin định danh */}
          <div style={{ marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px dashed #ffffff' }}>
            <p style={{ margin: '0 0 8px 0' }}><strong>👤 Người dùng:</strong> {houseInfo._id?.username || localCreds.username}</p>
            <p style={{ margin: '0 0 8px 0' }}><strong>🏠 Mã nhà:</strong> {houseInfo._id?.houseid || localCreds.houseid}</p>
          </div>

          {/* Ngưỡng cảm biến an toàn */}
          <div style={{ marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px dashed #ccc' }}>
            <p style={{ margin: '0 0 8px 0', fontWeight: 'bold' }}>Ngưỡng an toàn:</p>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#ffffff' }}>
              <li>Nhiệt độ: {houseInfo.tempmin}°C - {houseInfo.tempmax}°C</li>
              <li>Độ ẩm: {houseInfo.humimin}% - {houseInfo.humimax}%</li>
              <li>Ánh sáng: {houseInfo.lightmin}% - {houseInfo.lightmax}%</li>
            </ul>
          </div>

          {/* Danh sách thiết bị */}
          <div>
            <p style={{ margin: '0 0 8px 0', fontWeight: 'bold', color: '#ffffff' }}>
              Thiết bị quản lý ({houseInfo.numberdevices?.length || 0}):
            </p>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#ffffff', listStyleType: 'square' }}>
              {/* Tạo bản sao mảng bằng [...array] để tránh lỗi mutation và thực hiện sort */}
              {[...(houseInfo.numberdevices || [])]
                .sort((a, b) => a.numberdevice - b.numberdevice) 
                .map((dev, index) => {
                  let statusDisplay = '';
                  
                  if (dev.type === 'quat') {
                    if (dev.status === 0) statusDisplay = 'Tắt';
                    else if (dev.status === 70) statusDisplay = 'Mức 1';
                    else if (dev.status === 80) statusDisplay = 'Mức 2';
                    else if (dev.status === 90) statusDisplay = 'Mức 3';
                    else if (dev.status === 100) statusDisplay = 'Mức 4';
                    else statusDisplay = `Mức ${dev.status}`;
                  } else if (dev.type === 'servo') {
                    statusDisplay = dev.status === 0 ? 'Đóng' : `Mở (${dev.status}°)`;
                  } else {
                    statusDisplay = dev.status ? 'Đang bật' : 'Đang tắt';
                  }

                  return (
                    <li key={index} style={{ marginBottom: '4px', color: '#ffffff' }}>
                      Thiết bị {dev.numberdevice} ({dev.type}): <strong>{statusDisplay}</strong>
                    </li>
                  );
                })}
            </ul>
          </div>
        </div>
      ) : (
        <div style={{ marginBottom: '24px', padding: '16px', backgroundColor: '#fff2f0', border: '1px solid #ffccc7', borderRadius: '8px' }}>
          <p style={{ color: '#ff4d4f', margin: 0 }}>Không tìm thấy thông tin ngôi nhà hoặc kết nối bị lỗi.</p>
          <p style={{ color: '#666', margin: '8px 0 0 0', fontSize: '13px' }}>User: {localCreds.username} | House: {localCreds.houseid}</p>
        </div>
      )}

      {/* NÚT ĐĂNG XUẤT */}
      <button 
        onClick={handleLogout}
        style={{
          width: '100%',
          padding: '12px',
          backgroundColor: 'rgba(255, 77, 79, 0.1)',
          color: '#ff4d4f',
          border: '1px solid #ff4d4f',
          borderRadius: '8px',
          fontSize: '16px',
          fontWeight: '600',
          cursor: 'pointer',
          transition: 'all 0.3s ease'
        }}
      >
        Đăng xuất
      </button>
    </div>
  );
}