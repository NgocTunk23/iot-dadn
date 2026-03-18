import React from 'react';

/**
 * Shared device controls for both direct control (Khung 1) and mode editing (Khung 3).
 * @param {{ stateObj: object, updater: function }} props
 */
export default function DeviceControls({ stateObj, updater }) {
  const renderLight = (key, label) => (
    <div className={`device-row ${stateObj[key].state ? 'device-active' : ''}`} key={key}>
      <div className="device-row-header">
        <div className="device-row-title">💡 {label}</div>
        <label className="toggle-switch">
          <input
            type="checkbox"
            checked={stateObj[key].state}
            onChange={(e) => updater(key, 'state', e.target.checked)}
          />
          <span className="slider"></span>
        </label>
      </div>
      <div className="device-row-slider">
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
      </div>
    </div>
  );

  const fanLabel = stateObj.fan === 0 ? '0%'
    : stateObj.fan === 1 ? '70%'
    : stateObj.fan === 2 ? '80%'
    : stateObj.fan === 3 ? '90%'
    : '100%';

  return (
    <div className="device-list">
      {renderLight('light1', 'Đèn 1')}
      {renderLight('light2', 'Đèn 2')}
      {renderLight('light3', 'Đèn 3')}
      {renderLight('light4', 'Đèn 4')}
      {renderLight('light5', 'Đèn 5')}

      {/* Servo */}
      <div className={`device-row ${stateObj.servo === 'open' ? 'device-active' : ''}`}>
        <div className="device-row-header">
          <div className="device-row-title">🚪 Servo (Cửa)</div>
        </div>
        <div className="servo-btns">
          <button className={`servo-btn ${stateObj.servo === 'open' ? 'active' : ''}`} onClick={() => updater('servo', null, 'open')}>Mở</button>
          <button className={`servo-btn ${stateObj.servo === 'close' ? 'active' : ''}`} onClick={() => updater('servo', null, 'close')}>Đóng</button>
        </div>
      </div>

      {/* Fan */}
      <div className={`device-row ${stateObj.fan > 0 ? 'device-active' : ''}`}>
        <div className="device-row-header">
          <div className="device-row-title">🌀 Quạt ({fanLabel})</div>
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
