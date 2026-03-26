import React from 'react';

export default function SettingsTab() {
  return (
    <div className="control-panel">
      <h3 className="panel-title">Cấu hình Hệ thống</h3>
      <div className="device-item" style={{ marginBottom: '15px' }}>
        <div className="device-info">
          <div className="device-text">
            <h4>Chế độ Ban Đêm (Dark Mode)</h4>
            <p>Luôn bật trên giao diện hiện tại</p>
          </div>
        </div>
        <label className="toggle-switch">
          <input type="checkbox" defaultChecked disabled />
          <span className="slider"></span>
        </label>
      </div>

      <div style={{ marginTop: '30px' }}>
        <button 
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
    </div>
  );
}
