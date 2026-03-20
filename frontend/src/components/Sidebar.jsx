import React from 'react';

const NAV_ITEMS = [
  { key: 'dashboard', icon: '📊', label: 'Tổng quan' },
  { key: 'devices',   icon: '🎛️', label: 'Thiết bị' },
  { key: 'alerts',    icon: '🔔', label: 'Cảnh báo' }, 
  { key: 'settings',  icon: '⚙️', label: 'Cài đặt' },
];

export default function Sidebar({ activeTab, onTabChange }) {
  return (
    <div className="sidebar">
      <div className="logo-section">
        <div className="logo-icon">🏠</div>
        <div className="logo-text">
          <h2>Smart Home</h2>
          <span>IoT Dashboard</span>
        </div>
      </div>
      <div className="nav-links">
        {NAV_ITEMS.map(item => (
          <a
            key={item.key}
            href="#"
            className={`nav-item ${activeTab === item.key ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); onTabChange(item.key); }}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </a>
        ))}
      </div>
    </div>
  );
}
