import './index.css';

// Import component Login vừa tạo (Đảm bảo đường dẫn chính xác)
import Login from './Login';

import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import DevicesTab from './components/DevicesTab';
import SettingsTab from './components/SettingsTab';
import { ToastContainer, useToast } from './components/Toast';
import AlertTab from './components/AlertTab';

import useSensorData from './hooks/useSensorData';
import useDevices from './hooks/useDevices';

const PAGE_TITLES = {
  dashboard: 'Tổng quan Hệ thống',
  devices: 'Quản lý Thiết bị',
  alerts: 'Cảnh báo & Ngưỡng',
  settings: 'Cài đặt Hệ thống',
};
import React, { useState, useEffect } from 'react'; // Nhớ import useEffect

function App() {
  // 1. Thêm State quản lý trạng thái đăng nhập
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userData, setUserData] = useState(null);
  const [houseId, setHouseId] = useState('HS001');
  const [activeTab, setActiveTab] = useState('dashboard');
  const { data } = useSensorData();
  const { messages, addToast, dismissToast } = useToast();
  const devices = useDevices(addToast);


  useEffect(() => {
    const storedHouseId = localStorage.getItem('houseid');
    // Kiểm tra cả localStorage và sessionStorage
    const storedUser = localStorage.getItem('user') || sessionStorage.getItem('user');

    if (storedHouseId && storedUser) {
      setHouseId(storedHouseId);
      setUserData(JSON.parse(storedUser));
      setIsAuthenticated(true);
    }
  }, []);
  // 1. THÊM HÀM ĐĂNG XUẤT NÀY VÀO
  const handleLogout = () => {
    setIsAuthenticated(false); // Ép React hiển thị lại <Login />
    setUserData(null);         // Xóa dữ liệu user trong state
    localStorage.removeItem('houseid');
    localStorage.removeItem('user');
    localStorage.removeItem('username');
    setActiveTab('dashboard'); // Tiện tay reset tab về dashboard cho lần đăng nhập sau
  };


  // 2. Hàm xử lý khi người dùng nhấn nút Đăng nhập
  // Trong file App.jsx

  const handleLoginSubmit = async (credentials) => {
    try {
      const response = await fetch('http://localhost:5000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: credentials.email, // Đây là username/email từ form
          password: credentials.password,
          houseid: credentials.houseId // GỬI HOUSEID LÊN ĐÂY
        })
      });

      const data = await response.json();

      if (data.success) {
        setUserData(data.user);
        setHouseId(data.houseid);
        setIsAuthenticated(true);
        // Lưu đúng houseid mà backend đã xác nhận
        localStorage.setItem('houseid', data.houseid);
        localStorage.setItem('username', JSON.stringify(data.user._id));
      } else {
        alert(data.message);
      }
    } catch (error) {
      alert("Lỗi kết nối server");
    }
  };

  // 3. Nếu CHƯA đăng nhập -> Chỉ render màn hình Login
  if (!isAuthenticated) {
    return <Login onLoginSubmit={handleLoginSubmit} />;
  }

  // 4. Nếu ĐÃ đăng nhập -> Render giao diện chính của App
  return (
    <div className="app-container">
      {/* Mobile Top Header */}
      <div className="mobile-header">
        <div className="logo-icon">🏠</div>
        <h2>Smart Home</h2>
      </div>

      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content Area */}
      <div className="main-content">
        <h1 className="page-title">{PAGE_TITLES[activeTab]}</h1>

        {data.connected === false && (
          <div className="danger-alert">
            ⚠️ CẢNH BÁO: Mất kết nối với thiết bị Cảm biến! Vui lòng kiểm tra lại thiết bị hoặc mạng.
          </div>
        )}

        {activeTab === 'dashboard' && <Dashboard data={data} houseId={houseId} />}
        {activeTab === 'devices' && <DevicesTab {...devices} />}
        {activeTab === 'alerts' && <AlertTab houseId={houseId} addToast={addToast} />}
        {activeTab === 'settings' && <SettingsTab onLogout={handleLogout} />}

      </div>

      {/* Toast Notifications */}
      <ToastContainer messages={messages} onDismiss={dismissToast} />
    </div>
  );
}

export default App;