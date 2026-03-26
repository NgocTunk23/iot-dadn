import React from 'react';

const IconLight = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '8px', color: 'var(--accent-yellow)'}}>
    <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.9 1.2 1.5 1.5 2.5" />
    <path d="M9 18h6" />
    <path d="M10 22h4" />
  </svg>
);

const IconDoor = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '8px', color: 'var(--accent-blue)'}}>
    <path d="M14 22V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v18" />
    <path d="M14 13h2" />
    <path d="M22 22H2" />
  </svg>
);

const IconFan = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '8px', color: 'var(--text-secondary)'}}>
    <path d="M10.827 16.379a6.082 6.082 0 0 1-8.618-7.002l5.412 1.45a6.082 6.082 0 0 1 7.002-8.618l-1.45 5.412a6.082 6.082 0 0 1 8.618 7.002l-5.412-1.45a6.082 6.082 0 0 1-7.002 8.618l1.45-5.412Z" />
    <circle cx="12" cy="12" r="2" />
  </svg>
);

/**
 * Shared device controls for both direct control (Khung 1) and mode editing (Khung 3).
 * @param {{ stateObj: object, updater: function }} props
 */
export default function DeviceControls({ stateObj, updater }) {
  const renderLight = (key, label) => (
    <div className={`device-row ${stateObj[key].state ? 'device-active' : ''}`} key={key}>
      <div className="device-row-header">
        <div className="device-row-title"><IconLight /> {label}</div>
        <label className="toggle-switch">
          <input
            type="checkbox"
            checked={stateObj[key].state}
            onChange={(e) => updater(key, 'state', e.target.checked)}
          />
          <span className="slider"></span>
        </label>
      </div>
      {/* <div className="device-row-slider">
        <input
          type="range"
          min="0" max="100"
          value={stateObj[key].brightness}
          onChange={(e) => updater(key, 'brightness', parseInt(e.target.value))}
          disabled={!stateObj[key].state}
          style={{ opacity: stateObj[key].state ? 1 : 0.5 }}
        />
        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'right', marginTop: '2px' }}>
          {stateObj[key].brightness}%
        </div>
      </div> */}
    </div>
  );

  const fanLabel = stateObj.fan === 0 ? '0%'
    : stateObj.fan === 1 ? '70%'
    : stateObj.fan === 2 ? '80%'
    : stateObj.fan === 3 ? '90%'
    : '100%';

  return (
    <div className="device-list">
      {/* {renderLight('light1', 'Đèn 1')} */}
      {renderLight('light2', 'Đèn 2')}
      {renderLight('light3', 'Đèn 3')}
      {renderLight('light4', 'Đèn 4')}

      {/* Servo */}
      <div className={`device-row ${stateObj.servo === 'open' ? 'device-active' : ''}`}>
        <div className="device-row-header">
          <div className="device-row-title"><IconDoor /> Servo (Cửa)</div>
        </div>
        <div className="servo-btns">
          <button className={`servo-btn ${stateObj.servo === 'open' ? 'active' : ''}`} onClick={() => updater('servo', null, 'open')}>Mở</button>
          <button className={`servo-btn ${stateObj.servo === 'close' ? 'active' : ''}`} onClick={() => updater('servo', null, 'close')}>Đóng</button>
        </div>
      </div>

      {/* Fan */}
      <div className={`device-row ${stateObj.fan > 0 ? 'device-active' : ''}`}>
        <div className="device-row-header">
          <div className="device-row-title"><IconFan /> Quạt ({fanLabel})</div>
        </div>
        <div className="fan-levels">
          {[0, 1, 2, 3, 4].map(level => (
            <button
              key={level}
              className={`fan-level ${stateObj.fan === level ? 'active' : ''}`}
              onClick={() => updater('fan', null, level)}
            >
              {level}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
