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
    </div>
  );
}
