import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API = 'http://localhost:5000/api';

/* ─────────────────── GLOBAL KEYFRAME STYLES ─────────────────── */
const GLOBAL_CSS = `
@keyframes thermoPulse {
  0%,100% { height: 28px; }
  50%      { height: 34px; }
}
@keyframes humiFloat {
  0%,100% { transform: translateY(0px); }
  50%      { transform: translateY(-5px); }
}
@keyframes lightSpin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes lightRingPulse {
  0%,100% { opacity: 0.3; transform: scale(1); }
  50%      { opacity: 0.7; transform: scale(1.08); }
}
@keyframes radarSweep {
  0%   { transform: rotate(0deg); opacity: 1; }
  100% { transform: rotate(360deg); opacity: 1; }
}
@keyframes radarPing {
  0%   { transform: scale(0.6); opacity: 0.9; }
  100% { transform: scale(2.0); opacity: 0;   }
}
@keyframes bellSwing {
  0%,100% { transform: rotate(0deg); }
  15%     { transform: rotate(-20deg); }
  35%     { transform: rotate(20deg); }
  55%     { transform: rotate(-12deg); }
  75%     { transform: rotate(8deg); }
}
@keyframes gearSpin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes boltFlicker {
  0%,100% { opacity: 1; filter: drop-shadow(0 0 4px #a78bfa); }
  45%     { opacity: 0.55; filter: drop-shadow(0 0 1px #a78bfa); }
}
@keyframes logSlideIn {
  from { opacity: 0; transform: translateX(-8px); }
  to   { opacity: 1; transform: translateX(0); }
}
.card-hover-lift {
  transition: transform 0.26s cubic-bezier(0.34,1.4,0.64,1),
              box-shadow 0.26s ease !important;
}
.card-hover-lift:hover {
  transform: translateY(-4px) !important;
  box-shadow: 0 12px 30px rgba(0,0,0,0.24) !important;
}
.tab-btn-hover {
  transition: all 0.22s cubic-bezier(0.4,0,0.2,1) !important;
}
.tab-btn-hover:not([data-active="true"]):hover {
  transform: translateY(-2px) !important;
  background: rgba(255,255,255,0.04) !important;
  color: var(--text-primary) !important;
}
select option {
  background-color: #1e293b;
  color: #f8fafc;
  padding: 8px;
}
.thermo-rect   { animation: thermoPulse 2.2s ease-in-out infinite; transform-origin: bottom center; }
.humi-drop     { animation: humiFloat 2.4s ease-in-out infinite; }
.light-rays    { animation: lightSpin 7s linear infinite; transform-origin: 29px 29px; }
.light-ring    { animation: lightRingPulse 2.2s ease-in-out infinite; transform-origin: 29px 29px; }
.radar-arm     { animation: radarSweep 2.4s linear infinite; transform-origin: 12px 12px; }
.radar-ping    { animation: radarPing 2.4s ease-out infinite; transform-origin: 12px 12px; }
.bell-group    { animation: bellSwing 3.2s ease-in-out infinite; transform-origin: 12px 3px; }
.gear-g        { animation: gearSpin 5s linear infinite; transform-origin: 12px 12px; }
.bolt-g        { animation: boltFlicker 1.6s ease-in-out infinite; }
.log-item      { animation: logSlideIn 0.3s ease both; }
`;

function InjectCSS() {
  useEffect(() => {
    const id = 'alert-tab-v4-css';
    if (document.getElementById(id)) return;
    const el = document.createElement('style');
    el.id = id; el.textContent = GLOBAL_CSS;
    document.head.appendChild(el);
  }, []);
  return null;
}

/* ─────────────────── SVG ICONS ─────────────────── */
const TempIconSVG = ({ size = 46 }) => (
  <svg width={size} height={size} viewBox="0 0 40 58" fill="none">
    <rect x="12" y="2" width="16" height="38" rx="8" stroke="url(#tG)" strokeWidth="2.5"/>
    <circle cx="20" cy="46" r="10" stroke="url(#tG)" strokeWidth="2.5"/>
    <rect className="thermo-rect" x="17" y="14" width="6" height="28" rx="3" fill="url(#tG)"/>
    <circle cx="20" cy="46" r="6" fill="url(#tG)"/>
    <defs><linearGradient id="tG" x1="20" y1="0" x2="20" y2="58" gradientUnits="userSpaceOnUse">
      <stop stopColor="#FF9F43"/><stop offset="1" stopColor="#FF6B6B"/>
    </linearGradient></defs>
  </svg>
);

const HumiIconSVG = ({ size = 46 }) => (
  <svg width={size} height={size} viewBox="0 0 44 58" fill="none">
    <g className="humi-drop">
      <path d="M22 4C22 4 6 24 6 36C6 44.837 13.163 52 22 52C30.837 52 38 44.837 38 36C38 24 22 4 22 4Z"
        stroke="url(#hG)" strokeWidth="2.5" fill="url(#hF)"/>
      <ellipse cx="16" cy="34" rx="5" ry="8" fill="rgba(255,255,255,0.15)"/>
    </g>
    <defs>
      <linearGradient id="hG" x1="22" y1="4" x2="22" y2="52" gradientUnits="userSpaceOnUse">
        <stop stopColor="#00D1FF"/><stop offset="1" stopColor="#0077FF"/>
      </linearGradient>
      <linearGradient id="hF" x1="22" y1="4" x2="22" y2="52" gradientUnits="userSpaceOnUse">
        <stop stopColor="rgba(0,209,255,0.12)"/><stop offset="1" stopColor="rgba(0,119,255,0.22)"/>
      </linearGradient>
    </defs>
  </svg>
);

const LightIconSVG = ({ size = 46 }) => (
  <svg width={size} height={size} viewBox="0 0 58 58" fill="none">
    <circle cx="29" cy="29" r="12" stroke="url(#lG)" strokeWidth="2.5" fill="rgba(255,193,7,0.14)"/>
    <circle className="light-ring" cx="29" cy="29" r="18" stroke="url(#lG)" strokeWidth="1.2" fill="none"/>
    <g className="light-rays">
      {[0,45,90,135,180,225,270,315].map((angle, i) => {
        const rad = angle * Math.PI / 180;
        return <line key={i} x1={29+22*Math.cos(rad)} y1={29+22*Math.sin(rad)} x2={29+27*Math.cos(rad)} y2={29+27*Math.sin(rad)} stroke="url(#lG)" strokeWidth="2.2" strokeLinecap="round"/>;
      })}
    </g>
    <defs><linearGradient id="lG" x1="29" y1="0" x2="29" y2="58" gradientUnits="userSpaceOnUse">
      <stop stopColor="#FFC107"/><stop offset="1" stopColor="#FF9F43"/>
    </linearGradient></defs>
  </svg>
);

const RadarIconSVG = ({ size = 18, color = '#00D1FF' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="9.5" stroke={color} strokeWidth="1.4" opacity="0.25"/>
    <circle cx="12" cy="12" r="5.5" stroke={color} strokeWidth="1.4" opacity="0.5"/>
    <circle cx="12" cy="12" r="1.8" fill={color}/>
    <line className="radar-arm" x1="12" y1="12" x2="20" y2="4" stroke={color} strokeWidth="1.6" strokeLinecap="round" opacity="0.8"/>
    <circle className="radar-ping" cx="12" cy="12" r="9" stroke={color} strokeWidth="1.2" fill="none"/>
  </svg>
);

const BellIconSVG = ({ size = 18, color = '#10b981' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <g className="bell-group">
      <path d="M6 10C6 6.686 8.686 4 12 4s6 2.686 6 6v4.5l2 2.5H4l2-2.5V10z" stroke={color} strokeWidth="1.7" fill={`${color}1a`}/>
    </g>
    <path d="M10 19a2 2 0 004 0" stroke={color} strokeWidth="1.7" strokeLinecap="round"/>
  </svg>
);

const GearIconSVG = ({ size = 18, color = '#FF9F43' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <g className="gear-g">
      <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" stroke={color} strokeWidth="1.7"/>
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" stroke={color} strokeWidth="1.7" fill={`${color}11`}/>
    </g>
  </svg>
);

const BoltIconSVG = ({ size = 18, color = '#a78bfa' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <g className="bolt-g">
      <path d="M13 2L4.5 13.5H11L10 22L19.5 10.5H13L13 2Z" stroke={color} strokeWidth="1.7" strokeLinejoin="round" fill={`${color}22`}/>
    </g>
  </svg>
);

const TelegramIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" fill="rgba(42,171,238,0.1)" stroke="#2AABEE" strokeWidth="1.5"/>
    <path d="M6 12.5L17.5 7.5L14 17.5L11 14.5L6 12.5Z" stroke="#2AABEE" strokeWidth="1.5" strokeLinejoin="round" fill="rgba(42,171,238,0.1)"/>
    <line x1="11" y1="14.5" x2="14" y2="11" stroke="#2AABEE" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);

const EmailIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <rect x="2" y="5" width="20" height="14" rx="3" stroke="#EA4335" strokeWidth="1.7" fill="rgba(234,67,53,0.08)"/>
    <path d="M2 8.5l10 6.5 10-6.5" stroke="#EA4335" strokeWidth="1.7" strokeLinecap="round"/>
  </svg>
);

/* ─────────────────── HELPERS ─────────────────── */
function fmtDeviceVal(v) {
  if (v === true  || v === 1)  return 'BẬT';
  if (v === false || v === 0)  return 'TẮT';
  if (typeof v === 'number')   return v + '%';
  return String(v);
}

/* ─────────────────── TAB META ─────────────────── */
const TAB_META = {
  threshold: { Icon: GearIconSVG,  color: '#FF9F43' },
  channel:   { Icon: BellIconSVG,  color: '#10b981' },
  rules:     { Icon: BoltIconSVG,  color: '#a78bfa' },
};

/* ─────────────────── SHARED UI ─────────────────── */
function TabBar({ tabs, active, onChange }) {
  return (
    <div style={{
      display: 'flex', gap: '6px',
      background: 'linear-gradient(135deg, var(--bg-card-inner) 0%, rgba(0,0,0,0.15) 100%)',
      padding: '5px', borderRadius: '14px',
      border: '1px solid var(--border-color)', marginBottom: '28px', width: 'fit-content',
      boxShadow: '0 4px 24px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.04)',
      backdropFilter: 'blur(12px)',
    }}>
      {tabs.map(t => {
        const isActive = active === t.key;
        const meta = TAB_META[t.key] || {};
        return (
          <button key={t.key} onClick={() => onChange(t.key)}
            className="tab-btn-hover"
            data-active={isActive}
            style={{
              padding: '9px 18px', borderRadius: '10px', border: 'none',
              cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem',
              display: 'flex', alignItems: 'center', gap: '7px',
              position: 'relative', overflow: 'hidden',
              background: isActive ? `linear-gradient(135deg, ${meta.color}22 0%, ${meta.color}11 100%)` : 'transparent',
              color: isActive ? meta.color : 'var(--text-secondary)',
              boxShadow: isActive ? `0 0 0 1px ${meta.color}44, 0 4px 14px ${meta.color}22` : 'none',
              transform: isActive ? 'translateY(-1px)' : 'none',
            }}>
            {isActive && (
              <span style={{
                position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
                background: `linear-gradient(90deg, transparent, ${meta.color}, transparent)`,
                borderRadius: '10px 10px 0 0',
              }} />
            )}
            {meta.Icon && <meta.Icon size={17} color={isActive ? meta.color : '#8B949E'} />}
            {t.label}
            {isActive && (
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: meta.color, boxShadow: `0 0 6px ${meta.color}`, flexShrink: 0 }} />
            )}
          </button>
        );
      })}
    </div>
  );
}

function Card({ children, style, hoverable = true }) {
  return (
    <div className={hoverable ? 'card-hover-lift' : ''} style={{
      background: 'linear-gradient(160deg, var(--bg-card) 0%, rgba(0,0,0,0.08) 100%)',
      borderRadius: '18px', border: '1px solid var(--border-color)', padding: '24px',
      marginBottom: '20px',
      boxShadow: '0 2px 16px rgba(0,0,0,0.14), 0 1px 0 rgba(255,255,255,0.03) inset',
      position: 'relative', overflow: 'hidden', ...style
    }}>
      <div style={{
        position: 'absolute', top: 0, left: '10%', right: '10%', height: '1px',
        background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent)',
        pointerEvents: 'none',
      }} />
      {children}
    </div>
  );
}

function SectionTitle({ children, color }) {
  const c = color || 'var(--accent-blue)';
  return (
    <h3 style={{
      fontSize: '1rem', fontWeight: 700, marginBottom: '20px',
      paddingBottom: '14px', paddingLeft: '14px',
      borderBottom: '1px solid var(--border-color)', color: 'var(--text-primary)',
      position: 'relative', display: 'flex', alignItems: 'center', gap: '8px',
    }}>
      <span style={{
        position: 'absolute', left: 0, top: '2px', bottom: '14px',
        width: '3px', borderRadius: '4px',
        background: `linear-gradient(180deg, ${c}, ${c}44)`,
        boxShadow: `0 0 8px ${c}66`,
      }} />
      {children}
    </h3>
  );
}

function StatusBadge({ ok, label }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: '3px 10px', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 700,
      background: ok ? 'rgba(16,185,129,0.10)' : 'rgba(234,67,53,0.10)',
      color: ok ? '#10b981' : 'var(--accent-red)',
      border: `1px solid ${ok ? 'rgba(16,185,129,0.4)' : 'rgba(234,67,53,0.4)'}`,
      letterSpacing: '0.03em',
      boxShadow: ok ? '0 0 8px rgba(16,185,129,0.15)' : '0 0 8px rgba(234,67,53,0.15)',
    }}>
      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: ok ? '#10b981' : 'var(--accent-red)', boxShadow: ok ? '0 0 4px #10b981' : '0 0 4px var(--accent-red)', flexShrink: 0 }} />
      {label}
    </span>
  );
}

function InputRow({ label, children }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px', flexWrap: 'wrap' }}>
      <label style={{ minWidth: '110px', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.02em' }}>
        {label}
      </label>
      {children}
    </div>
  );
}

const inputStyle = {
  background: 'linear-gradient(135deg, var(--bg-card-inner) 0%, rgba(0,0,0,0.1) 100%)',
  border: '1px solid var(--border-color)',
  color: 'var(--text-primary)', borderRadius: '10px', padding: '9px 13px',
  fontSize: '0.88rem', outline: 'none',
  boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.15)',
  transition: 'border-color 0.2s, box-shadow 0.2s',
};
const selectStyle = { ...inputStyle, cursor: 'pointer' };

const SENSOR_ICON_MAP = { temp: TempIconSVG, humi: HumiIconSVG, light: LightIconSVG };

/* ─────────────────── 1. CẤU HÌNH NGƯỠNG ─────────────────── */
function DualThresholdSlider({ sensor, draft, setDraft, setActiveThumb, activeThumb, getNum, clamp }) {
  const minValRaw = getNum(draft[sensor.key]?.min, sensor.min);
  const maxValRaw = getNum(draft[sensor.key]?.max, sensor.max);
  const mMin = clamp(minValRaw, sensor.min, sensor.max);
  const mMax = clamp(maxValRaw, sensor.min, sensor.max);
  const activeMin = Math.min(mMin, mMax);
  const activeMax = Math.max(mMin, mMax);
  const denom   = (sensor.max - sensor.min) || 1;
  const leftPct = ((activeMin - sensor.min) / denom) * 100;
  const widthPct = ((activeMax - activeMin) / denom) * 100;
  return (
    <div style={{ marginBottom: '25px', position: 'relative' }}>
      <div className="dual-threshold-slider">
        <div className="base-track">
          <div className="active-track" style={{ left: `${leftPct}%`, width: `${widthPct}%` }} />
        </div>
        <input className="dual-thumb dual-thumb--min" type="range"
          min={sensor.min} max={sensor.max} step="0.1" value={mMin}
          onMouseDown={() => setActiveThumb('min')}
          onChange={e => { const val = parseFloat(e.target.value); setDraft(prev => ({ ...prev, [sensor.key]: { ...prev[sensor.key], min: Math.min(val, mMax) } })); }}
          style={{ zIndex: activeThumb === 'min' ? 5 : 3 }}
        />
        <input className="dual-thumb dual-thumb--max" type="range"
          min={sensor.min} max={sensor.max} step="0.1" value={mMax}
          onMouseDown={() => setActiveThumb('max')}
          onChange={e => { const val = parseFloat(e.target.value); setDraft(prev => ({ ...prev, [sensor.key]: { ...prev[sensor.key], max: Math.max(val, mMin) } })); }}
          style={{ zIndex: activeThumb === 'max' ? 5 : 4 }}
        />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '25px' }}>
        <span>Min: {activeMin.toFixed(1)}{sensor.unit}</span>
        <span>Max: {activeMax.toFixed(1)}{sensor.unit}</span>
      </div>
    </div>
  );
}

function ThresholdTab({ addToast }) {
  const SENSORS = [
    { key: 'temp',  label: 'Nhiệt độ', unit: '°C', min: -50, max: 500 },
    { key: 'humi',  label: 'Độ ẩm',    unit: '%',  min: 0,   max: 100 },
    { key: 'light', label: 'Ánh sáng', unit: '%',  min: 0,   max: 100 },
  ];
  const SENSOR_COLOR = { temp: '#FF9F43', humi: '#00D1FF', light: '#FFC107' };
  const [thresholds, setThresholds]   = useState({ temp:{min:0,max:40}, humi:{min:20,max:80}, light:{min:0,max:90} });
  const [draft, setDraft]             = useState(null);
  const [saving, setSaving]           = useState(false);
  const [activeThumb, setActiveThumb] = useState(null);
  const clamp  = (n, min, max) => Math.max(min, Math.min(max, n));
  const getNum = (v, fallback) => { const n = typeof v === 'string' ? parseFloat(v) : v; return Number.isFinite(n) ? n : fallback; };

  useEffect(() => {
    axios.get(`${API}/thresholds?houseid=HS001`)
      .then(r => { setThresholds(r.data); setDraft(JSON.parse(JSON.stringify(r.data))); })
      .catch(() => setDraft(JSON.parse(JSON.stringify(thresholds))));
  }, []);

  const handleSave = async (sensor) => {
    setSaving(true);
    try {
      await axios.post(`${API}/thresholds`, { houseid: 'HS001', sensor, min: parseFloat(draft[sensor].min), max: parseFloat(draft[sensor].max) });
      setThresholds(prev => ({ ...prev, [sensor]: draft[sensor] }));
      addToast(`✅ Đã cập nhật ngưỡng ${SENSORS.find(s=>s.key===sensor)?.label}!`, 'success');
    } catch (e) { addToast(e.response?.data?.message || 'Lỗi cập nhật ngưỡng!', 'error'); }
    setSaving(false);
  };

  const handleReset = async () => {
    try {
      const r = await axios.post(`${API}/thresholds/reset`, { houseid: 'HS001' });
      setThresholds(r.data.thresholds); setDraft(JSON.parse(JSON.stringify(r.data.thresholds)));
      addToast('✅ Đã reset ngưỡng về mặc định!', 'success');
    } catch { addToast('Lỗi reset ngưỡng!', 'error'); }
  };

  if (!draft) return <p style={{ color: 'var(--text-secondary)' }}>Đang tải...</p>;

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
        <button onClick={handleReset} style={{
          padding: '9px 18px', borderRadius: '10px',
          background: 'rgba(234,67,53,0.08)', border: '1px solid rgba(234,67,53,0.3)',
          color: 'var(--accent-red)', fontWeight: 700, fontSize: '0.85rem',
          cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', transition: 'all 0.2s',
        }}>🔄 Reset về mặc định</button>
      </div>
      {SENSORS.map(s => {
        const IconComp = SENSOR_ICON_MAP[s.key];
        const color    = SENSOR_COLOR[s.key];
        return (
          <Card key={s.key}>
            <SectionTitle color={color}>
              <IconComp size={22} />
              {s.label}
              <span style={{ fontSize: '0.76rem', fontWeight: 400, color: 'var(--text-secondary)', marginLeft: '2px' }}>({s.unit})</span>
            </SectionTitle>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '20px' }}>
              {['min', 'max'].map(bound => (
                <div key={bound} style={{
                  background: bound === 'min' ? 'linear-gradient(135deg, rgba(0,209,255,0.06) 0%, var(--bg-card-inner) 100%)' : 'linear-gradient(135deg, rgba(234,67,53,0.06) 0%, var(--bg-card-inner) 100%)',
                  borderRadius: '10px', padding: '12px',
                  border: `1px solid ${bound === 'min' ? 'rgba(0,209,255,0.18)' : 'rgba(234,67,53,0.18)'}`,
                }}>
                  <label style={{
                    display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.75rem', fontWeight: 700,
                    marginBottom: '8px', color: bound === 'min' ? '#00D1FF' : 'var(--accent-red)',
                    letterSpacing: '0.05em', textTransform: 'uppercase',
                  }}>
                    <span style={{ width: '3px', height: '12px', borderRadius: '2px', display: 'inline-block', background: bound === 'min' ? '#00D1FF' : 'var(--accent-red)', boxShadow: `0 0 5px ${bound === 'min' ? '#00D1FF88' : 'rgba(234,67,53,0.6)'}` }} />
                    {bound === 'min' ? '↓ Ngưỡng dưới (Min)' : '↑ Ngưỡng trên (Max)'}
                  </label>
                  <input type="number" style={{ ...inputStyle, width: '100%' }}
                    value={draft[s.key]?.[bound] ?? ''}
                    onChange={e => { const val = e.target.value === '' ? '' : parseFloat(e.target.value); setDraft(prev => ({ ...prev, [s.key]: { ...prev[s.key], [bound]: val } })); }}
                  />
                </div>
              ))}
            </div>
            <DualThresholdSlider sensor={s} draft={draft} setDraft={setDraft}
              activeThumb={activeThumb} setActiveThumb={setActiveThumb} getNum={getNum} clamp={clamp} />
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
              <button className="btn btn-primary" disabled={saving} onClick={() => handleSave(s.key)}>
                {saving ? 'Đang lưu...' : 'Lưu'}
              </button>
            </div>
          </Card>
        );
      })}
    </>
  );
}

/* ─────────────────── 2. KÊNH THÔNG BÁO ─────────────────── */
function ChannelTab({ addToast }) {
  const [channels, setChannels] = useState({ telegram: { enabled: false }, email: { enabled: false } });
  const [draft, setDraft]       = useState(null);
  const [saving, setSaving]     = useState('');

  useEffect(() => {
    axios.get(`${API}/notification-channels?houseid=HS001`)
      .then(r => { setChannels(r.data); setDraft(JSON.parse(JSON.stringify(r.data))); })
      .catch(() => setDraft({ telegram: { enabled: false }, email: { enabled: false } }));
  }, []);

  const handleSave = async (channel) => {
    setSaving(channel);
    const d = draft[channel] || {};
    const body = { houseid: 'HS001', channel, enabled: d.enabled };
    if (channel === 'telegram') { body.bot_token = d.bot_token || ''; body.chat_id = d.chat_id || ''; }
    if (channel === 'email')    { body.address = d.address || ''; }
    try {
      await axios.post(`${API}/notification-channels`, body);
      setChannels(prev => ({ ...prev, [channel]: d }));
      addToast(`✅ Đã cập nhật kênh ${channel === 'telegram' ? 'Telegram' : 'Email'}!`, 'success');
    } catch (e) { addToast(e.response?.data?.message || 'Lỗi cập nhật kênh!', 'error'); }
    setSaving('');
  };

  const setField = (channel, field, value) =>
    setDraft(prev => ({ ...prev, [channel]: { ...prev[channel], [field]: value } }));

  if (!draft) return <p style={{ color: 'var(--text-secondary)' }}>Đang tải...</p>;

  return (
    <>
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', paddingBottom: '14px', paddingLeft: '14px', borderBottom: '1px solid var(--border-color)', position: 'relative' }}>
          <span style={{ position: 'absolute', left: 0, top: '2px', bottom: '14px', width: '3px', borderRadius: '4px', background: 'linear-gradient(180deg, #2AABEE, #2AABEE44)', boxShadow: '0 0 8px #2AABEE66' }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
            <TelegramIconSVG size={22} />
            <span>Telegram Bot</span>
            <StatusBadge ok={channels.telegram?.enabled} label={channels.telegram?.enabled ? 'Đang bật' : 'Tắt'} />
          </h3>
          <label className="toggle-switch">
            <input type="checkbox" checked={!!draft.telegram?.enabled} onChange={e => setField('telegram', 'enabled', e.target.checked)} />
            <span className="slider"></span>
          </label>
        </div>
        <InputRow label="Bot Token">
          <input style={{ ...inputStyle, flex: 1, minWidth: '200px' }} placeholder="7123456789:AAF..."
            value={draft.telegram?.bot_token || ''} onChange={e => setField('telegram', 'bot_token', e.target.value)} />
        </InputRow>
        <InputRow label="Chat ID">
          <input style={{ ...inputStyle, flex: 1, minWidth: '200px' }} placeholder="123456789"
            value={draft.telegram?.chat_id || ''} onChange={e => setField('telegram', 'chat_id', e.target.value)} />
        </InputRow>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-primary" disabled={saving === 'telegram'} onClick={() => handleSave('telegram')}>
            {saving === 'telegram' ? 'Đang lưu...' : 'Lưu thông tin'}
          </button>
        </div>
      </Card>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', paddingBottom: '14px', paddingLeft: '14px', borderBottom: '1px solid var(--border-color)', position: 'relative' }}>
          <span style={{ position: 'absolute', left: 0, top: '2px', bottom: '14px', width: '3px', borderRadius: '4px', background: 'linear-gradient(180deg, #EA4335, #EA433544)', boxShadow: '0 0 8px #EA433566' }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
            <EmailIconSVG size={22} />
            <span>Email (Gmail)</span>
            <StatusBadge ok={channels.email?.enabled} label={channels.email?.enabled ? 'Đang bật' : 'Tắt'} />
          </h3>
          <label className="toggle-switch">
            <input type="checkbox" checked={!!draft.email?.enabled} onChange={e => setField('email', 'enabled', e.target.checked)} />
            <span className="slider"></span>
          </label>
        </div>
        <InputRow label="Email nhận">
          <input style={{ ...inputStyle, flex: 1, minWidth: '200px' }} type="email" placeholder="recipient@gmail.com"
            value={draft.email?.address || ''} onChange={e => setField('email', 'address', e.target.value)} />
        </InputRow>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-primary" disabled={saving === 'email'} onClick={() => handleSave('email')}>
            {saving === 'email' ? 'Đang lưu...' : 'Lưu thông tin'}
          </button>
        </div>
      </Card>
    </>
  );
}

/* ─────────────────── 3. KỊCH BẢN TỰ ĐỘNG ─────────────────── */
const SENSOR_OPTS  = ['temp', 'humi', 'light'];
const OP_OPTS      = [
  { value: 'gt',  label: '> lớn hơn' },
  { value: 'gte', label: '≥ lớn hơn hoặc bằng' },
  { value: 'lt',  label: '< nhỏ hơn' },
  { value: 'lte', label: '≤ nhỏ hơn hoặc bằng' },
  { value: 'eq',  label: '= bằng' },
];
const SENSOR_LABEL = { temp: 'Nhiệt độ (°C)', humi: 'Độ ẩm (%)', light: 'Ánh sáng (%)' };
const DEVICE_OPTS  = [
  { id: 1, label: '💡 Đèn 1' }, { id: 2, label: '💡 Đèn 2' },
  { id: 3, label: '💡 Đèn 3' }, { id: 4, label: '💡 Đèn 4' },
  { id: 5, label: '💡 Đèn 5' }, { id: 6, label: '🚪 Servo' },
  { id: 7, label: '🌀 Quạt (0-100%)' },
];
const FAN_LEVELS   = [70, 80, 90, 100];
const EMPTY_RULE   = { name: '', enabled: true, condition: { sensor: 'temp', op: 'gt', value: 35 }, actions: [{ numberdevice: 7, status: 100 }] };

function AutoRuleTab({ addToast }) {
  const [rules, setRules]       = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft]       = useState(EMPTY_RULE);
  const [editName, setEditName] = useState(null);
  const [saving, setSaving]     = useState(false);

  const fetchRules = useCallback(async () => {
    try { const r = await axios.get(`${API}/automation-rules?houseid=HS001`); setRules(r.data || []); } catch {}
  }, []);

  useEffect(() => { fetchRules(); }, [fetchRules]);

  const openCreate = () => { setDraft(JSON.parse(JSON.stringify(EMPTY_RULE))); setEditName(null); setShowForm(true); };
  const openEdit = (rule) => {
    setDraft({
      name: rule.name,
      enabled: rule.enabled,
      condition: { sensor: rule.condition?.sensor || 'temp', op: rule.condition?.op || 'gt', value: rule.condition?.value || 0 },
      actions: (rule.actions || rule.action || []).map(a => ({ numberdevice: parseInt(a.numberdevice), status: a.status }))
    });
    setEditName(rule.name);
    setShowForm(true);
  };

  const serializeStatus = (devId, status) => {
    const id = parseInt(devId);
    if (id >= 1 && id <= 5) { if (status === true || status === 'true') return true; if (status === false || status === 'false') return false; return Boolean(status); }
    return parseFloat(status) || 0;
  };

  const handleSave = async () => {
    if (!draft.name.trim()) { addToast('Tên kịch bản không được rỗng!', 'error'); return; }
    const condValue = parseFloat(draft.condition.value);
    if (isNaN(condValue)) { addToast('Giá trị điều kiện phải là số!', 'error'); return; }
    setSaving(true);
    try {
      await axios.post(`${API}/automation-rules`, {
        houseid: 'HS001', name: draft.name.trim(),
        condition: { ...draft.condition, value: condValue },
        actions: draft.actions.map(a => ({ numberdevice: parseInt(a.numberdevice), status: serializeStatus(a.numberdevice, a.status) })),
        enabled: draft.enabled,
      });
      addToast(`✅ Đã lưu kịch bản "${draft.name}"!`, 'success');
      setShowForm(false); fetchRules();
    } catch (e) { addToast(e.response?.data?.message || 'Lỗi lưu kịch bản!', 'error'); }
    setSaving(false);
  };

  const handleDelete = async (name) => {
    if (!window.confirm(`Xóa kịch bản "${name}"?`)) return;
    try { await axios.delete(`${API}/automation-rules`, { params: { houseid: 'HS001', name } }); addToast(`Đã xóa "${name}".`, 'info'); fetchRules(); }
    catch { addToast('Lỗi xóa kịch bản!', 'error'); }
  };

  const handleToggle = async (rule) => {
    try { await axios.patch(`${API}/automation-rules/toggle`, { houseid: 'HS001', name: rule.name, enabled: !rule.enabled }); fetchRules(); }
    catch { addToast('Lỗi thay đổi trạng thái!', 'error'); }
  };

  // Tập hợp ID thiết bị đã được dùng trong các hàng khác (để disable)
  const usedDeviceIds = (rowIndex) =>
    new Set(draft.actions
      .filter((_, j) => j !== rowIndex)
      .map(a => parseInt(a.numberdevice))
    );

  const setAction    = (i, field, val) => setDraft(prev => { const acts = [...prev.actions]; acts[i] = { ...acts[i], [field]: val }; return { ...prev, actions: acts }; });
  const addAction    = () => {
    const used = new Set(draft.actions.map(a => parseInt(a.numberdevice)));
    const next = DEVICE_OPTS.find(d => !used.has(d.id));
    if (!next) { addToast('Tất cả thiết bị đã được thêm vào kịch bản!', 'info'); return; }
    const defaultStatus = next.id >= 1 && next.id <= 5 ? true : 0;
    setDraft(prev => ({ ...prev, actions: [...prev.actions, { numberdevice: next.id, status: defaultStatus }] }));
  };
  const removeAction = (i) => setDraft(prev => ({ ...prev, actions: prev.actions.filter((_, j) => j !== i) }));

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
        <button onClick={openCreate} style={{
          padding: '10px 22px', borderRadius: '11px',
          background: 'linear-gradient(135deg, rgba(167,139,250,0.18) 0%, rgba(167,139,250,0.08) 100%)',
          border: '1px solid rgba(167,139,250,0.4)', color: '#a78bfa', fontWeight: 700, fontSize: '0.88rem',
          cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px',
          boxShadow: '0 0 16px rgba(167,139,250,0.15)', transition: 'all 0.2s',
        }}>
          <BoltIconSVG size={18} color="#a78bfa" /> Tạo kịch bản mới
        </button>
      </div>

      {showForm && (
        <Card style={{ border: '1px solid rgba(0,209,255,0.3)', boxShadow: '0 0 28px rgba(0,209,255,0.08)' }}>
          <SectionTitle color="#00D1FF">
            <RadarIconSVG size={17} color="#00D1FF" />
            {editName ? `Sửa: ${editName}` : 'Tạo kịch bản mới'}
          </SectionTitle>

          <InputRow label="Tên kịch bản">
            <input style={{ ...inputStyle, flex: 1 }} placeholder="VD: Bật quạt khi nóng"
              value={draft.name} onChange={e => setDraft(p => ({ ...p, name: e.target.value }))} />
          </InputRow>

          <div style={{ background: 'linear-gradient(135deg, rgba(0,209,255,0.06) 0%, var(--bg-card-inner) 100%)', borderRadius: '12px', padding: '16px', marginBottom: '16px', border: '1px solid rgba(0,209,255,0.15)' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#00D1FF', marginBottom: '12px', letterSpacing: '0.06em', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '3px', height: '14px', background: '#00D1FF', borderRadius: '2px', boxShadow: '0 0 6px #00D1FF88', display: 'inline-block' }} />
              <RadarIconSVG size={14} color="#00D1FF" /> Điều kiện kích hoạt
            </div>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Nếu</span>
              <select style={selectStyle} value={draft.condition.sensor} onChange={e => setDraft(p => ({ ...p, condition: { ...p.condition, sensor: e.target.value } }))}>
                {SENSOR_OPTS.map(s => <option key={s} value={s}>{SENSOR_LABEL[s]}</option>)}
              </select>
              <select style={selectStyle} value={draft.condition.op} onChange={e => setDraft(p => ({ ...p, condition: { ...p.condition, op: e.target.value } }))}>
                {OP_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
              <input type="number" style={{ ...inputStyle, width: '90px' }} value={draft.condition.value}
                onChange={e => setDraft(p => ({ ...p, condition: { ...p.condition, value: e.target.value } }))} />
            </div>
          </div>

          <div style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.06) 0%, var(--bg-card-inner) 100%)', borderRadius: '12px', padding: '16px', marginBottom: '16px', border: '1px solid rgba(16,185,129,0.15)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#10b981', letterSpacing: '0.06em', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '3px', height: '14px', background: '#10b981', borderRadius: '2px', boxShadow: '0 0 6px #10b98188', display: 'inline-block' }} />
                <BoltIconSVG size={14} color="#10b981" /> Hành động phản hồi
              </span>
              <button className="btn btn-primary" style={{ padding: '4px 12px', fontSize: '0.8rem' }} onClick={addAction}>+ Thêm</button>
            </div>

            {draft.actions.map((act, i) => {
              const devId   = parseInt(act.numberdevice);
              const isLight = devId >= 1 && devId <= 5;
              const isServo = devId === 6;
              const isFan   = devId === 7;
              const used = usedDeviceIds(i);

              return (
                <div key={i} style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', padding: '8px 10px' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>→ Thiết bị</span>
                  <select style={selectStyle} value={act.numberdevice}
                    onChange={e => {
                      const newId = parseInt(e.target.value);
                      setAction(i, 'numberdevice', e.target.value);
                      setAction(i, 'status', newId >= 1 && newId <= 5 ? true : 0);
                    }}>
                    {DEVICE_OPTS.map(d => (
                      <option key={d.id} value={d.id} disabled={used.has(d.id)}>
                        {used.has(d.id) ? `${d.label} (đã dùng)` : d.label}
                      </option>
                    ))}
                  </select>

                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Trạng thái</span>
                  {isLight && <select style={{ ...selectStyle, width: '130px' }} value={String(act.status)} onChange={e => setAction(i, 'status', e.target.value === 'true')}><option value="true">✅ Bật</option><option value="false">⭕ Tắt</option></select>}
                  {isServo && <select style={{ ...selectStyle, width: '130px' }} value={String(act.status)} onChange={e => setAction(i, 'status', parseFloat(e.target.value))}><option value="90">🔓 Mở (90°)</option><option value="0">🔒 Đóng (0°)</option></select>}
                  {isFan   && <select style={{ ...selectStyle, width: '130px' }} value={act.status} onChange={e => setAction(i, 'status', parseFloat(e.target.value))}>{FAN_LEVELS.map(l => <option key={l} value={l}>Mức {l}%</option>)}</select>}
                  {draft.actions.length > 1 && <button className="btn btn-danger" style={{ padding: '4px 10px', fontSize: '0.8rem' }} onClick={() => removeAction(i)}>✕</button>}
                </div>
              );
            })}
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
              💡 Mỗi thiết bị chỉ được chọn một lần để tránh xung đột
            </p>
          </div>

          <InputRow label="Kích hoạt">
            <label className="toggle-switch">
              <input type="checkbox" checked={draft.enabled} onChange={e => setDraft(p => ({ ...p, enabled: e.target.checked }))} />
              <span className="slider"></span>
            </label>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{draft.enabled ? 'Bật ngay' : 'Tạm tắt'}</span>
          </InputRow>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
            <button className="btn btn-danger" onClick={() => setShowForm(false)}>Hủy</button>
            <button className="btn btn-success" disabled={saving} onClick={handleSave}>{saving ? 'Đang lưu...' : 'Lưu'}</button>
          </div>
        </Card>
      )}

      {rules.length === 0 && !showForm && (
        <Card>
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '30px' }}>
            Chưa có kịch bản nào. Nhấn "Tạo kịch bản mới" để bắt đầu.
          </p>
        </Card>
      )}

      {rules.map(rule => {
        const cond    = rule.condition;
        const opLabel = OP_OPTS.find(o => o.value === cond?.op)?.label || cond?.op;
        const sColor  = { temp: '#FF9F43', humi: '#00D1FF', light: '#FFC107' }[cond?.sensor] || 'var(--accent-blue)';
        const SIcon   = SENSOR_ICON_MAP[cond?.sensor];
        const actionList = rule.actions || rule.action || [];
        return (
          <Card key={rule._id} style={{
            borderLeft: `3px solid ${rule.enabled ? sColor : 'var(--border-color)'}`,
            boxShadow: rule.enabled ? `0 2px 20px ${sColor}14, 0 2px 16px rgba(0,0,0,0.14)` : undefined,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                  {SIcon && <SIcon size={28} />}
                  <span style={{ fontWeight: 700, fontSize: '0.98rem', color: 'var(--text-primary)' }}>{rule.name}</span>
                  <StatusBadge ok={rule.enabled} label={rule.enabled ? 'Đang bật' : 'Tắt'} />
                </div>
                <div style={{ fontSize: '0.83rem', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Nếu</span>
                  <span style={{ background: `${sColor}18`, color: sColor, border: `1px solid ${sColor}44`, borderRadius: '6px', padding: '2px 8px', fontWeight: 700, fontSize: '0.8rem' }}>{SENSOR_LABEL[cond?.sensor]}</span>
                  <span style={{ background: 'rgba(0,209,255,0.1)', color: '#00D1FF', border: '1px solid rgba(0,209,255,0.3)', borderRadius: '6px', padding: '2px 8px', fontWeight: 700, fontSize: '0.8rem' }}>{opLabel}</span>
                  <span style={{ background: 'rgba(255,159,67,0.1)', color: '#FF9F43', border: '1px solid rgba(255,159,67,0.3)', borderRadius: '6px', padding: '2px 8px', fontWeight: 700, fontSize: '0.8rem' }}>{cond?.value}</span>
                </div>
                <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <BoltIconSVG size={14} color="#10b981" />
                  {actionList.map(a => {
                    const devLabel = DEVICE_OPTS.find(d => d.id === parseInt(a.numberdevice))?.label || `Thiết bị ${a.numberdevice}`;
                    return `${devLabel} → ${fmtDeviceVal(a.status)}`;
                  }).join('  ·  ')}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexShrink: 0 }}>
                <label className="toggle-switch">
                  <input type="checkbox" checked={rule.enabled} onChange={() => handleToggle(rule)} />
                  <span className="slider"></span>
                </label>
                <button className="btn btn-primary" style={{ padding: '6px 14px', borderRadius: '9px' }} onClick={() => openEdit(rule)}>Sửa</button>
                <button className="btn btn-danger" style={{ padding: '6px 12px', borderRadius: '9px' }} onClick={() => handleDelete(rule.name)}>🗑</button>
              </div>
            </div>
          </Card>
        );
      })}
    </>
  );
}

/* ─────────────────── MAIN ─────────────────── */
const TABS = [
  { key: 'threshold', label: 'Cấu hình ngưỡng' },
  { key: 'channel',   label: 'Kênh thông báo'  },
  { key: 'rules',     label: 'Kịch bản tự động' },
];

/**
 * @param {function} addToast
 * @param {function} onDeviceUpdate - callback(numberdevice: Array) để App cập nhật deviceStates
 *   Được gọi khi phát hiện kịch bản backend vừa thay đổi trạng thái thiết bị.
 */
export default function AlertTab({ addToast, onDeviceUpdate }) {
  const [sub, setSub] = useState('threshold');
  useEffect(() => {
    if (!onDeviceUpdate) return;
    let prevState = null;
    const checkBackend = async () => {
      try {
        const res = await axios.get('http://localhost:5000/api/sensor-data');
        if (res.data && res.data.numberdevice) {
          const currState = JSON.stringify(res.data.numberdevice);
          if (prevState && prevState !== currState) {
            // Kịch bản vừa chạy → notify App cập nhật deviceStates
            onDeviceUpdate(res.data.numberdevice);
          }
          prevState = currState;
        }
      } catch {}
    };
    const timer = setInterval(checkBackend, 2000);
    return () => clearInterval(timer);
  }, [onDeviceUpdate]);

  return (
    <div>
      <InjectCSS />
      <TabBar tabs={TABS} active={sub} onChange={setSub} />
      {sub === 'threshold' && <ThresholdTab addToast={addToast} />}
      {sub === 'channel'   && <ChannelTab   addToast={addToast} />}
      {sub === 'rules'     && <AutoRuleTab  addToast={addToast} />}
    </div>
  );
}