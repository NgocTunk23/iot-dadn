import React, { useState } from 'react';
import './index.css';

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
  alerts:    'Cảnh báo & Ngưỡng', 
  settings: 'Cài đặt Hệ thống',
};

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { data } = useSensorData();
  const { messages, addToast, dismissToast } = useToast();
  const devices = useDevices(addToast);

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

        {activeTab === 'dashboard' && <Dashboard data={data} />}
        {activeTab === 'devices' && <DevicesTab {...devices} />}
        {activeTab === 'alerts' && <AlertTab addToast={addToast} />}
        {activeTab === 'settings' && <SettingsTab />}
        
      </div>

      {/* Toast Notifications */}
      <ToastContainer messages={messages} onDismiss={dismissToast} />
    </div>
  );
}

export default App;