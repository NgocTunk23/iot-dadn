import React from 'react';
import DeviceControls from './DeviceControls';

const internalCSS = `
/* ============ Devices Tab: Column Layout ============ */
.devices-tab-container { width: 100%; }
.column-left { display: flex; flex-direction: column; gap: 20px; }

/* ============ Anti-Theft Panel ============ */
.anti-theft-panel { border: 1px solid rgba(16, 185, 129, 0.25); box-shadow: 0 0 14px rgba(16, 185, 129, 0.08); }
.anti-theft-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 14px; border-bottom: 1px solid var(--border-color); margin-bottom: 12px; }
.anti-theft-info { display: flex; align-items: center; gap: 12px; }
.anti-theft-title { font-size: 1rem; font-weight: 600; color: var(--text-primary); margin: 0; }
.anti-theft-subtitle { font-size: 0.8rem; color: var(--text-secondary); margin: 2px 0 0 0; }
.anti-theft-note { font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5; padding: 10px 14px; background: rgba(16, 185, 129, 0.05); border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.12); }

/* ============ Mode Item Enhancements ============ */
.mode-device-count { font-size: 0.78rem; color: var(--text-secondary); background: rgba(0, 209, 255, 0.08); padding: 2px 8px; border-radius: 10px; margin-left: 8px; }
.mode-device-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.mode-device-tag { font-size: 0.72rem; padding: 3px 8px; border-radius: 6px; background: rgba(255, 255, 255, 0.04); border: 1px solid var(--border-color); color: var(--text-secondary); }
.mode-item.active .mode-device-tag { background: rgba(0, 209, 255, 0.08); border-color: rgba(0, 209, 255, 0.25); color: var(--accent-blue); }
.mode-actions { display: flex; gap: 8px; margin-top: 6px; }
.btn-icon { flex: 1; padding: 8px 12px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-card-inner); color: var(--text-secondary); cursor: pointer; font-size: 0.82rem; font-weight: 500; transition: all 0.2s; }
.btn-icon.edit:hover { background: rgba(0, 209, 255, 0.1); border-color: var(--accent-blue); color: var(--accent-blue); }
.btn-icon.delete:hover { background: rgba(234, 67, 53, 0.1); border-color: var(--accent-red); color: var(--accent-red); }
.btn-secondary { background: rgba(139, 148, 158, 0.1); color: var(--text-secondary); border: 1px solid var(--border-color); }
.btn-secondary:hover { background: rgba(139, 148, 158, 0.2); color: var(--text-primary); }
.empty-message { text-align: center; color: var(--text-secondary); padding: 30px 20px; font-size: 0.9rem; }
.placeholder-content { text-align: center; color: var(--text-secondary); padding: 40px 20px; font-size: 0.9rem; line-height: 1.6; }

/* ============ Scene Step UI ============ */
.scene-step { animation: fadeIn 0.25s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.step-header { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px dashed var(--border-color); }
.step-title { font-size: 0.95rem; font-weight: 500; color: var(--text-primary); }

/* ============ Device Checkbox List (Step 1) ============ */
.device-checkbox-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }
.device-checkbox-item { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-radius: 10px; background: var(--bg-card-inner); border: 1px solid var(--border-color); cursor: pointer; transition: all 0.2s ease; user-select: none; }
.device-checkbox-item:hover { border-color: rgba(0, 209, 255, 0.3); background: rgba(0, 209, 255, 0.04); }
.device-checkbox-item.checked { border-color: rgba(0, 209, 255, 0.45); background: rgba(0, 209, 255, 0.08); box-shadow: 0 0 12px rgba(0, 209, 255, 0.1); }
.device-checkbox-left { display: flex; align-items: center; gap: 12px; }
.custom-checkbox { width: 22px; height: 22px; border-radius: 6px; border: 2px solid var(--border-color); display: flex; align-items: center; justify-content: center; transition: all 0.2s; font-size: 0.8rem; color: #fff; flex-shrink: 0; }
.custom-checkbox.checked { background: linear-gradient(135deg, var(--accent-blue), #0077FF); border-color: var(--accent-blue); box-shadow: 0 0 8px rgba(0, 209, 255, 0.3); }
.device-checkbox-icon { display: flex; align-items: center; }
.device-checkbox-label { font-size: 0.95rem; font-weight: 500; color: var(--text-primary); }

/* ============ Scene Config List (Step 2) ============ */
.scene-device-config-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.scene-device-config-item .device-row { margin-bottom: 0; }

/* ============ Form Actions ============ */
.form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 10px; padding-top: 15px; border-top: 1px solid var(--border-color); }
.form-actions .btn { min-width: 100px; }
.form-actions .btn:disabled { opacity: 0.4; cursor: not-allowed; }
.mode-item-info { display: flex; align-items: center; }
`;
/* ======================== DEVICE ICONS ======================== */
const IconLight = ({ active }) => {
  const color = active ? '#FFB020' : '#8B949E';
  const glow = active ? 'rgba(255, 176, 32, 0.25)' : 'rgba(139, 148, 158, 0.1)';
  const bg = active ? 'rgba(255, 176, 32, 0.08)' : 'rgba(139, 148, 158, 0.05)';
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{marginRight: '6px', transition: 'all 0.3s'}}>
      <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" fill={bg} stroke={color} strokeWidth="1.5" strokeDasharray="3 3"/>
      <path d="M12 6c-2.5 0-4.5 2-4.5 4.5 0 1.5 1 2.5 1.5 3.5.5.8.5 1.5.5 2.5h5c0-1 0-1.5.5-2.5.5-1 1.5-2 1.5-3.5C16.5 8 14.5 6 12 6z" fill={glow} stroke={color} strokeWidth="1.5"/>
      <path d="M10 18h4M11 21h2" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
};

const IconDoor = ({ state }) => {
  const isOpen = state === 'open';
  const color = isOpen ? '#00D1FF' : '#8B949E';
  const bg = isOpen ? 'rgba(0, 209, 255, 0.08)' : 'rgba(139, 148, 158, 0.05)';
  const doorColor = isOpen ? 'rgba(0, 209, 255, 0.2)' : 'rgba(139, 148, 158, 0.15)';
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{marginRight: '6px', transition: 'all 0.3s'}}>
      <rect x="3" y="3" width="18" height="18" rx="2" fill={bg} stroke={color} strokeWidth="1.5"/>
      <path d="M14 3v18M7 3v18" stroke={color} strokeWidth="1.5" opacity="0.3" strokeDasharray="2 2"/>
      <rect x="6" y="6" height="12" rx="1" fill={doorColor} stroke={color} strokeWidth="1.5" style={{ width: isOpen ? '3px' : '12px', transition: 'all 0.3s' }}/>
      <circle cy="12" r="1.5" fill={color} style={{ cx: isOpen ? '7.5px' : '16px', transition: 'all 0.3s' }}/>
    </svg>
  );
};

const IconFan = ({ speed }) => {
  const isActive = speed > 0;
  const color = isActive ? '#a78bfa' : '#8B949E';
  const bg = isActive ? 'rgba(167, 139, 250, 0.08)' : 'rgba(139, 148, 158, 0.05)';
  const blade = isActive ? 'rgba(167, 139, 250, 0.3)' : 'rgba(139, 148, 158, 0.2)';
  const duration = speed === 0 ? '0s' : `${1.5 - (speed * 0.25)}s`;
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{marginRight: '6px', transition: 'all 0.3s'}}>
      <circle cx="12" cy="12" r="10" fill={bg} stroke={color} strokeWidth="1.5"/>
      <g style={{ transformOrigin: '12px 12px', animation: isActive ? `spin ${duration} linear infinite` : 'none' }}>
        <path d="M12 12c0-3 2-5 4-5s4 2 2 4-5 3-6 1z" fill={blade} stroke={color} strokeWidth="1.5"/>
        <path d="M12 12c3 0 5 2 5 4s-2 4-4 2-3-5-1-6z" fill={blade} stroke={color} strokeWidth="1.5"/>
        <path d="M12 12c0 3-2 5-4 5s-4-2-2-4 5-3 6-1z" fill={blade} stroke={color} strokeWidth="1.5"/>
        <path d="M12 12c-3 0-5-2-5-4s2-4 4-2 3 5 1 6z" fill={blade} stroke={color} strokeWidth="1.5"/>
      </g>
      <circle cx="12" cy="12" r="2" fill={color}/>
      <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
    </svg>
  );
};

const IconShield = ({ active }) => {
  const color = active ? '#10b981' : '#8B949E';
  const bg = active ? 'rgba(16, 185, 129, 0.15)' : 'rgba(139, 148, 158, 0.05)';
  const innerBg = active ? 'rgba(16, 185, 129, 0.3)' : 'none';
  
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" style={{marginRight: '6px', transition: 'all 0.3s'}}>
      {active && (
        <circle cx="12" cy="12" r="10" fill={bg} style={{ animation: 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite' }} />
      )}
      <path d="M12 3l8 3v6c0 5.5-3.5 10.5-8 12-4.5-1.5-8-6.5-8-12V6l8-3z" fill={bg} stroke={color} strokeWidth="1.5"/>
      <path d="M12 8v8M9 12l3 3 5-5" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill={innerBg}/>
      <style>{`
        @keyframes ping {
          0% { transform: scale(0.8); opacity: 0.8; }
          100% { transform: scale(1.5); opacity: 0; }
        }
      `}</style>
    </svg>
  );
};

const DEVICE_NAMES = {
  1: 'Đèn 1', 2: 'Đèn 2', 3: 'Đèn 3', 4: 'Đèn 4',
  6: 'Cửa (Servo)', 7: 'Quạt',
};

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
  // 2-step props
  sceneStep,
  checkedDeviceIds,
  toggleDeviceCheck,
  goToStep1,
  goToStep2,
  selectedDevices,
  updateDraftDevice,
  SCENE_DEVICE_KEYS,
  antiTheftId,
}) {
  const isEditing = draftMode && modes.find(m => m.id === draftMode.id);
  const antiTheftKey = antiTheftId ? `device_${antiTheftId}` : null;
  const antiTheftState = antiTheftKey ? deviceStates[antiTheftKey] : null;

  return (
    <>
      <style>{internalCSS}</style>
      <div className="devices-tab-container">
        <div className="devices-3col-grid">
          {/* ═══════ KHUNG 1: ĐIỀU KHIỂN THỦ CÔNG + CHỐNG TRỘM ═══════ */}
          <div className="column-left">
            <div className="control-panel">
              <h3 className="panel-title">Điều khiển Thiết bị</h3>
              <DeviceControls stateObj={deviceStates} updater={updateDevice} deviceList={SCENE_DEVICE_KEYS} />
            </div>

            {/* KHUNG CHỐNG TRỘM */}
            {antiTheftKey && (
              <div className="control-panel anti-theft-panel">
                <div className="anti-theft-header">
                  <div className="anti-theft-info">
                    <IconShield active={antiTheftState?.state} />
                    <div>
                      <h3 className="anti-theft-title">{antiTheftState?.name || 'Chế độ an ninh'}</h3>
                      <p className="anti-theft-subtitle">Chế độ tự động thông báo & cảnh báo</p>
                    </div>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={antiTheftState?.state || false}
                      onChange={(e) => updateDevice(antiTheftKey, 'state', e.target.checked)}
                    />
                    <span className="slider"></span>
                  </label>
                </div>
                <p className="anti-theft-note">
                  {antiTheftState?.state
                    ? '🟢 Đang bật — Đèn sẽ phản hồi khi cảm biến PIR phát hiện chuyển động'
                    : '⚪ Đang tắt — Cảm biến PIR vẫn ghi nhận nhưng đèn không phản hồi'}
                </p>
              </div>
            )}
          </div>

          {/* ═══════ KHUNG 2: DANH SÁCH CHẾ ĐỘ ═══════ */}
          <div className="control-panel">
            <h3 className="panel-title">Chế độ hiện có</h3>
            <button className="btn-add" onClick={startCreateMode}>+ Tạo mới</button>

            <div className="mode-list">
              {modes.length === 0 && (
                <p className="empty-message">Chưa có kịch bản nào</p>
              )}
              {modes.map(mode => (
                <div className={`mode-item ${mode.active ? 'active' : ''}`} key={mode.id}>
                  <div className="mode-item-header">
                    <div className="mode-item-info">
                      <span className="mode-item-title">{mode.name}</span>
                      <span className="mode-device-count">
                        {mode.action.length} thiết bị
                      </span>
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
                      Chỉnh sửa
                    </button>
                    <button className="btn-icon delete" onClick={() => deleteMode(mode.id)} title="Xóa">
                      Hủy bỏ
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ═══════ KHUNG 3: CẤU HÌNH KỊCH BẢN (2 BƯỚC) ═══════ */}
          <div className="control-panel">
            <h3 className="panel-title">
              {draftMode
                ? (isEditing ? 'Chỉnh sửa chế độ' : 'Tạo chế độ mới')
                : 'Chỉnh sửa chế độ'}
            </h3>

            {!draftMode ? (
              <div className="placeholder-content">
                <p>Chọn <strong>"Chỉnh sửa"</strong> hoặc <strong>"Tạo mới"</strong> để bắt đầu thiết lập chế độ kịch bản.</p>
              </div>
            ) : sceneStep === 1 ? (
              /* ──── BƯỚC 1: CHỌN THIẾT BỊ ──── */
              <div className="scene-step scene-step-1">
                <div className="step-header">
                  <span className="step-title">Chọn thiết bị cho kịch bản</span>
                </div>

                <input
                  type="text"
                  className="input-text"
                  placeholder="Tên chế độ (VD: Buổi tối, Ra ngoài...)"
                  value={draftMode.name}
                  onChange={(e) => setDraftMode({ ...draftMode, name: e.target.value })}
                />

                <div className="device-checkbox-list">
                  {SCENE_DEVICE_KEYS.map(dev => {
                    const isChecked = checkedDeviceIds.includes(dev.id);
                    return (
                      <label
                        key={dev.id}
                        className={`device-checkbox-item ${isChecked ? 'checked' : ''}`}
                        onClick={() => toggleDeviceCheck(dev.id)}
                      >
                        <div className="device-checkbox-left">
                          <div className={`custom-checkbox ${isChecked ? 'checked' : ''}`}>
                            {isChecked && <span>✓</span>}
                          </div>
                          <span className="device-checkbox-icon">
                            {dev.type === 'switch' && <IconLight active={isChecked} />}
                            {dev.type === 'servo' && <IconDoor state={isChecked ? 'open' : 'close'} />}
                            {dev.type === 'fan' && <IconFan speed={isChecked ? 2 : 0} />}
                          </span>
                          <span className="device-checkbox-label">{dev.label}</span>
                        </div>
                      </label>
                    );
                  })}
                </div>

                <div className="form-actions">
                  <button className="btn btn-secondary" onClick={cancelEditMode}>Hủy</button>
                  <button
                    className="btn btn-success"
                    onClick={goToStep2}
                    disabled={checkedDeviceIds.length === 0}
                  >
                    Tiếp tục ({checkedDeviceIds.length} thiết bị) →
                  </button>
                </div>
              </div>
            ) : (
              /* ──── BƯỚC 2: CẤU HÌNH TRẠNG THÁI ──── */
              <div className="scene-step scene-step-2">
                <div className="step-header">
                  <span className="step-title">Cấu hình trạng thái</span>
                </div>

                <input
                  type="text"
                  className="input-text"
                  placeholder="Tên chế độ (VD: Buổi tối, Ra ngoài...)"
                  value={draftMode.name}
                  onChange={(e) => setDraftMode({ ...draftMode, name: e.target.value })}
                />

                <div className="scene-device-config-list">
                  {selectedDevices.map(dev => (
                    <div key={dev.id} className="scene-device-config-item">
                      {/* ─── SWITCH (Đèn) ─── */}
                      {dev.type === 'switch' && (
                        <div className={`device-row ${dev.state?.state ? 'device-active' : ''}`}>
                          <div className="device-row-header">
                            <div className="device-row-title">
                              <IconLight active={dev.state?.state} /> {dev.label}
                            </div>
                            <label className="toggle-switch">
                              <input
                                type="checkbox"
                                checked={dev.state?.state || false}
                                onChange={(e) => updateDraftDevice(dev.id, 'state', e.target.checked)}
                              />
                              <span className="slider"></span>
                            </label>
                          </div>
                        </div>
                      )}
                      {/* ─── SERVO ─── */}
                      {dev.type === 'servo' && (
                        <div className={`device-row ${dev.state === 'open' ? 'device-active' : ''}`}>
                          <div className="device-row-header">
                            <div className="device-row-title">
                              <IconDoor state={dev.state} /> {dev.label}
                            </div>
                          </div>
                          <div className="servo-btns">
                            <button
                              className={`servo-btn ${dev.state === 'close' ? 'active' : ''}`}
                              onClick={() => updateDraftDevice(dev.id, null, 'close')}
                            >Đóng</button>
                            <button
                              className={`servo-btn ${dev.state === 'open' ? 'active' : ''}`}
                              onClick={() => updateDraftDevice(dev.id, null, 'open')}
                            >Mở</button>
                          </div>
                        </div>
                      )}
                      {/* ─── FAN ─── */}
                      {dev.type === 'fan' && (
                        <div className={`device-row ${dev.state > 0 ? 'device-active' : ''}`}>
                          <div className="device-row-header">
                            <div className="device-row-title">
                              <IconFan speed={dev.state} /> {dev.label} ({dev.state === 0 ? '0%' : dev.state === 1 ? '70%' : dev.state === 2 ? '80%' : dev.state === 3 ? '90%' : '100%'})
                            </div>
                          </div>
                          <div className="fan-levels">
                            {[0, 1, 2, 3, 4].map(level => (
                              <button
                                key={level}
                                className={`fan-level ${dev.state === level ? 'active' : ''}`}
                                onClick={() => updateDraftDevice(dev.id, null, level)}
                              >
                                {level}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <div className="form-actions">
                  <button className="btn btn-secondary" onClick={goToStep1}>
                    {isEditing ? 'Thiết bị' : '← Quay lại'}
                  </button>
                  <button className="btn btn-secondary" onClick={cancelEditMode}>Hủy</button>
                  <button className="btn btn-success" onClick={saveMode}>Lưu</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
