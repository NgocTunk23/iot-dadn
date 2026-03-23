import React from 'react';
import DeviceControls from './DeviceControls';

const IconTimer = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '4px', verticalAlign: 'text-bottom'}}>
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
);

const IconManual = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '4px', verticalAlign: 'text-bottom'}}>
    <path d="M18 11V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2" />
    <path d="M14 10V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2" />
    <path d="M10 10.5V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v5" />
    <path d="M6 13.5V11a2 2 0 0 0-2-2a2 2 0 0 0-2 2v7a6 6 0 0 0 6 6h2a8 8 0 0 0 8-8v-7a2 2 0 0 0-2-2a2 2 0 0 0-2 2v3" />
  </svg>
);

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
  updateDraftDevice,
}) {
  const isEditing = draftMode && modes.find(m => m.id === draftMode.id);

  return (
    <div className="devices-3col-grid">
      {/* Khung 1: Điều khiển Thiết bị */}
      <div className="control-panel">
        <h3 className="panel-title">Điều khiển Thiết bị</h3>
        <DeviceControls stateObj={deviceStates} updater={updateDevice} />
      </div>

      {/* Khung 2: Chế độ hiện có */}
      <div className="control-panel">
        <h3 className="panel-title">Chế độ hiện có</h3>
        <button className="btn-add" onClick={startCreateMode}>+ Tạo mới</button>

        <div className="mode-list">
          {modes.length === 0 && (
            <p style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '20px' }}>
              Chưa có chế độ nào
            </p>
          )}
          {modes.map(mode => (
            <div className="mode-item" key={mode.id}>
              <div className="mode-item-header">
                <div>
                  <div className="mode-item-title">{mode.name}</div>
                  {mode.triggerType === 'timer' && (
                    <div className="mode-badge"><IconTimer /> Hẹn giờ: {mode.triggerTime}</div>
                  )}
                  {mode.triggerType === 'manual' && (
                    <div className="mode-badge"><IconManual /> Kích hoạt thủ công</div>
                  )}
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
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => startEditMode(mode)}>
                  Chỉnh sửa
                </button>
                <button className="btn btn-danger" onClick={() => deleteMode(mode.id)}>
                  Hủy bỏ
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Khung 3: Chỉnh sửa/Tạo chế độ */}
      <div className="control-panel">
        <h3 className="panel-title">
          {draftMode ? (isEditing ? 'Chỉnh sửa chế độ' : 'Tạo chế độ mới') : 'Chỉnh sửa chế độ'}
        </h3>

        {!draftMode ? (
          <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '50px', padding: '0 20px' }}>
            <p>Chọn <strong>"Chỉnh sửa"</strong> hoặc <strong>"Tạo mới"</strong> để bắt đầu thiết lập chế độ kịch bản.</p>
          </div>
        ) : (
          <div className="mode-edit-form">
            <input
              type="text"
              className="input-text"
              placeholder="Tên chế độ (VD: Buổi tối, Ra ngoài...)"
              value={draftMode.name}
              onChange={(e) => setDraftMode({ ...draftMode, name: e.target.value })}
            />

            <div className="trigger-section">
              <label className="trigger-label">Điều kiện kích hoạt</label>
              <div className="radio-group">
                <label className="radio-label">
                  <input 
                    type="radio" 
                    name="triggerType" 
                    value="manual"
                    checked={draftMode.triggerType === 'manual'}
                    onChange={() => setDraftMode({ ...draftMode, triggerType: 'manual'})}
                  /> 
                  Thủ công
                </label>
                <label className="radio-label">
                  <input 
                    type="radio" 
                    name="triggerType" 
                    value="timer"
                    checked={draftMode.triggerType === 'timer'}
                    onChange={() => setDraftMode({ ...draftMode, triggerType: 'timer'})}  
                  /> 
                  Hẹn giờ
                </label>
              </div>

              {draftMode.triggerType === 'timer' && (
                <div className="time-input-group">
                  <label>Chọn thời gian (24 giờ):</label>
                  <div className="custom-time-picker">
                    <select 
                      className="time-select"
                      value={draftMode.triggerTime ? draftMode.triggerTime.split(':')[0] : '00'}
                      onChange={(e) => {
                        const m = draftMode.triggerTime ? draftMode.triggerTime.split(':')[1] : '00';
                        setDraftMode({ ...draftMode, triggerTime: `${e.target.value}:${m}` });
                      }}
                    >
                      {Array.from({length: 24}).map((_, i) => (
                        <option key={`h-${i}`} value={i.toString().padStart(2, '0')}>
                          {i.toString().padStart(2, '0')}
                        </option>
                      ))}
                    </select>
                    <span className="time-separator">:</span>
                    <select 
                      className="time-select"
                      value={draftMode.triggerTime ? draftMode.triggerTime.split(':')[1] : '00'}
                      onChange={(e) => {
                        const h = draftMode.triggerTime ? draftMode.triggerTime.split(':')[0] : '00';
                        setDraftMode({ ...draftMode, triggerTime: `${h}:${e.target.value}` });
                      }}
                    >
                      {Array.from({length: 60}).map((_, i) => (
                        <option key={`m-${i}`} value={i.toString().padStart(2, '0')}>
                          {i.toString().padStart(2, '0')}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}
            </div>

            <DeviceControls stateObj={draftMode.devices} updater={updateDraftDevice} />

            <div style={{ display: 'flex', gap: '15px', marginTop: '20px' }}>
              <button className="btn btn-danger" style={{ flex: 1 }} onClick={cancelEditMode}>Hủy</button>
              <button className="btn btn-success" style={{ flex: 1 }} onClick={saveMode}>Lưu</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
