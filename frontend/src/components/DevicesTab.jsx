import React from 'react';
import DeviceControls from './DeviceControls'; // Add this import

export default function DevicesTab({
  deviceStates,
  updateDevice,
  modes,
  draftMode,
  setDraftMode,
  startCreateMode,
  startEditMode,
  cancelEditMode,
  saveMode,
  deleteMode,
  toggleMode,
  availableDevices,
  selectedDevices,
  onDragStart,
  onDropToSelected,
  onDropToAvailable,
  updateDraftDevice
}) {
  const isEditing = draftMode && modes.find(m => m.id === draftMode.id);

  return (
    <div className="devices-tab-container">
      {/* KHUNG CHỐNG TRỘM (LIGHT 1) */}
      <div className="anti-theft-panel control-panel">
        <div className="panel-header">
          <h3 className="panel-title">🛡️ Chế độ Chống trộm</h3>
          <p className="panel-subtitle">Sử dụng Đèn 1 kết hợp cảm biến</p>
        </div>
        <div className="anti-theft-control">
          <span className="device-label">Bật/Tắt Chống trộm (Đèn 1)</span>
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={deviceStates.light1.state}
              onChange={(e) => updateDevice('light1', 'state', e.target.checked)}
            />
            <span className="slider"></span>
          </label>
        </div>
      </div>

      <div className="devices-3col-grid">
        {/* Khung 1: Điều khiển Thiết bị Thủ công */}
        <div className="control-panel">
          <h3 className="panel-title">Điều khiển Thủ công</h3>
          <DeviceControls stateObj={deviceStates} updater={updateDevice} />
        </div>

        {/* Khung 2: Danh sách Chế độ */}
        <div className="control-panel">
          <h3 className="panel-title">Chế độ Kịch bản</h3>
          <button className="btn-add" onClick={startCreateMode}>+ Tạo kịch bản mới</button>

          <div className="mode-list">
            {modes.length === 0 && (
              <p className="empty-message">Chưa có kịch bản nào</p>
            )}
            {modes.map(mode => (
              <div className={`mode-item ${mode.active ? 'active' : ''}`} key={mode.id}>
                <div className="mode-item-header">
                  <div className="mode-item-info">
                    <span className="mode-item-title">{mode.name}</span>
                    <span className="mode-device-count">{mode.action.length} thiết bị</span>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={mode.active}
                      onChange={(e) => toggleMode(mode.id, e.target.checked)}
                    />
                    <span className="slider"></span>
                  </label>
                </div>
                <div className="mode-actions">
                  <button className="btn-icon edit" onClick={() => startEditMode(mode)} title="Chỉnh sửa">
                    ✏️
                  </button>
                  <button className="btn-icon delete" onClick={() => deleteMode(mode.id)} title="Xóa">
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Khung 3: Cấu hình Kịch bản (Drag & Drop) */}
        <div className="control-panel">
          <h3 className="panel-title">
            {draftMode ? (isEditing ? 'Chỉnh sửa kịch bản' : 'Thiết lập kịch bản mới') : 'Cấu hình kịch bản'}
          </h3>

          {!draftMode ? (
            <div className="placeholder-content">
              <p>Nhấn <strong>"Tạo kịch bản mới"</strong> hoặc <strong>"✏️"</strong> để bắt đầu thiết lập.</p>
            </div>
          ) : (
            <div className="dnd-mode-form">
              <input
                type="text"
                className="input-text"
                placeholder="Tên kịch bản (VD: Đi ngủ, Tiếp khách...)"
                value={draftMode.name}
                onChange={(e) => setDraftMode({ ...draftMode, name: e.target.value })}
              />

              <div className="dnd-container">
                {/* Frame: Thiết bị có sẵn */}
                <div 
                  className="dnd-frame available-frame"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={onDropToAvailable}
                >
                  <label className="dnd-label">Thiết bị có sẵn</label>
                  <div className="dnd-list">
                    {availableDevices.map(dev => (
                      <div 
                        key={dev.id} 
                        className="dnd-item"
                        draggable
                        onDragStart={(e) => onDragStart(e, dev)}
                      >
                        {dev.label} ✥
                      </div>
                    ))}
                    {availableDevices.length === 0 && <p className="dnd-hint">Hết thiết bị</p>}
                  </div>
                </div>

                {/* Frame: Thiết bị trong kịch bản */}
                <div 
                  className="dnd-frame selected-frame"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={onDropToSelected}
                >
                  <label className="dnd-label">Thiết bị được chọn (Kéo vào đây)</label>
                  <div className="dnd-list">
                    {selectedDevices.map(dev => (
                      <div 
                        key={dev.id} 
                        className="dnd-selected-item"
                        draggable
                        onDragStart={(e) => onDragStart(e, dev)}
                      >
                        <div className="dnd-selected-header">
                          <span className="dnd-item-label">{dev.label}</span>
                        </div>
                        <div className="dnd-item-controls">
                           {/* Render control tùy theo loại thiết bị */}
                           {dev.type === 'switch' && (
                             <label className="toggle-switch small">
                               <input
                                 type="checkbox"
                                 checked={dev.state.state}
                                 onChange={(e) => updateDraftDevice(dev.id, 'state', e.target.checked)}
                               />
                               <span className="slider"></span>
                             </label>
                           )}
                           {dev.type === 'servo' && (
                             <select 
                               className="input-select small"
                               value={dev.state}
                               onChange={(e) => updateDraftDevice(dev.id, null, e.target.value)}
                             >
                               <option value="close">Đóng</option>
                               <option value="open">Mở</option>
                             </select>
                           )}
                           {dev.type === 'fan' && (
                             <input 
                               type="range"
                               min="0" max="4"
                               value={dev.state}
                               onChange={(e) => updateDraftDevice(dev.id, null, parseInt(e.target.value))}
                             />
                           )}
                        </div>
                      </div>
                    ))}
                    {selectedDevices.length === 0 && <p className="dnd-hint">Kéo thiết bị vào đây</p>}
                  </div>
                </div>
              </div>

              <div className="form-actions">
                <button className="btn btn-secondary" onClick={cancelEditMode}>Hủy</button>
                <button className="btn btn-success" onClick={saveMode}>Lưu kịch bản</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
