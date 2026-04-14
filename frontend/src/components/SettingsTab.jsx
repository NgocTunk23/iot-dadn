import React from 'react';

// Nhận prop onLogout từ App.jsx truyền xuống
export default function SettingsTab({ onLogout }) {
  
  const handleLogout = () => {
    // 1. Xóa toàn bộ dữ liệu phiên đăng nhập
    localStorage.removeItem('houseid');
    localStorage.removeItem('user');
    sessionStorage.removeItem('user');

    // 2. Báo cho App.jsx biết để chuyển về màn hình Login
    if (onLogout) {
      onLogout();
    } else {
      // Nếu không có prop truyền vào thì dùng cách "chữa cháy" là tải lại trang
      window.location.reload(); 
    }
  };

  return (
    <div className="control-panel">
  
        {/* Thêm sự kiện onClick={handleLogout} vào nút */}
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