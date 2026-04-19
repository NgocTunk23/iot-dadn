import React from 'react';

const IconLight = ({ active }) => {
  const color = active ? '#FFB020' : '#8B949E';
  const glow = active ? 'rgba(255, 176, 32, 0.25)' : 'rgba(139, 148, 158, 0.1)';
  const bg = active ? 'rgba(255, 176, 32, 0.08)' : 'rgba(139, 148, 158, 0.05)';
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{marginRight: '8px', transition: 'all 0.3s'}}>
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
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{marginRight: '8px', transition: 'all 0.3s'}}>
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
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{marginRight: '8px', transition: 'all 0.3s'}}>
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

export default function DeviceControls({ stateObj, updater, deviceList }) {
  if (!deviceList || deviceList.length === 0) {
    return <div className="device-list p-4 text-center text-gray-400">Đang tải thiết bị...</div>;
  }

  return (
    <div className="device-list">
      {deviceList.map(dev => {
        const devKey = dev.key;
        const devState = stateObj[devKey];

        if (!devState) return null; // Still loading this device's state

        // --- Render Switch (Đèn) ---
        if (dev.type === 'switch') {
          return (
            <div className={`device-row ${devState.state ? 'device-active' : ''}`} key={devKey}>
              <div className="device-row-header">
                <div className="device-row-title"><IconLight active={devState.state} /> {dev.label}</div>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={devState.state}
                    onChange={(e) => updater(devKey, 'state', e.target.checked)}
                  />
                  <span className="slider"></span>
                </label>
              </div>
            </div>
          );
        }

        // --- Render Servo (Cửa) ---
        if (dev.type === 'servo') {
          return (
            <div className={`device-row ${devState === 'open' ? 'device-active' : ''}`} key={devKey}>
              <div className="device-row-header">
                <div className="device-row-title"><IconDoor state={devState} /> {dev.label}</div>
              </div>
              <div className="servo-btns">
                <button className={`servo-btn ${devState === 'close' ? 'active' : ''}`} onClick={() => updater(devKey, null, 'close')}>Đóng</button>
                <button className={`servo-btn ${devState === 'open' ? 'active' : ''}`} onClick={() => updater(devKey, null, 'open')}>Mở</button>
              </div>
            </div>
          );
        }

        // --- Render Fan (Quạt) ---
        if (dev.type === 'fan') {
          const fanLabel = devState === 0 ? '0%'
            : devState === 1 ? '70%'
              : devState === 2 ? '80%'
                : devState === 3 ? '90%'
                  : '100%';

          return (
            <div className={`device-row ${devState > 0 ? 'device-active' : ''}`} key={devKey}>
              <div className="device-row-header">
                <div className="device-row-title"><IconFan speed={devState} /> {dev.label} ({fanLabel})</div>
              </div>
              <div className="fan-levels">
                {[0, 1, 2, 3, 4].map(level => (
                  <button
                    key={level}
                    className={`fan-level ${devState === level ? 'active' : ''}`}
                    onClick={() => updater(devKey, null, level)}
                  >
                    {level}
                  </button>
                ))}
              </div>
            </div>
          );
        }

        return null;
      })}
    </div>
  );
}
