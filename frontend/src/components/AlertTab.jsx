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
  input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type=number] {
  -moz-appearance: textfield;
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

const ResetIconSVG = ({ size = 16, color = '#ef4444' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
    <path d="M3 3v5h5" />
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

  /* --- CHANGE 1: Nút tăng/giảm +/- cho threshold --- */
  const StepBtn = ({ color, onClick, children }) => (
    <button onClick={onClick} style={{
      width: '36px', height: '36px', borderRadius: '10px', border: `1.5px solid ${color}55`,
      background: `linear-gradient(135deg, ${color}18 0%, ${color}08 100%)`,
      color: color, fontWeight: 900, fontSize: '1.2rem',
      cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0, transition: 'all 0.18s', lineHeight: 1,
      boxShadow: `0 2px 8px ${color}22`,
    }}
    onMouseEnter={e => { e.currentTarget.style.background = `linear-gradient(135deg, ${color}35 0%, ${color}18 100%)`; e.currentTarget.style.transform = 'scale(1.1)'; }}
    onMouseLeave={e => { e.currentTarget.style.background = `linear-gradient(135deg, ${color}18 0%, ${color}08 100%)`; e.currentTarget.style.transform = 'scale(1)'; }}
    >{children}</button>
  );

  return (
    <>
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          marginBottom: "16px",
        }}
      >
        <button
          onClick={handleReset}
          style={{
            padding: "8px 16px",
            borderRadius: "10px",
            background:
              "linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(239, 68, 68, 0.04) 100%)",
            border: "1.5px solid rgba(239, 68, 68, 0.35)",
            color: "#ef4444",
            fontWeight: 700,
            fontSize: "0.85rem",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
            boxShadow: "0 2px 10px rgba(239, 68, 68, 0.1)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background =
              "linear-gradient(135deg, rgba(239, 68, 68, 0.22) 0%, rgba(239, 68, 68, 0.08) 100%)";
            e.currentTarget.style.transform = "translateY(-2px)";
            e.currentTarget.style.boxShadow =
              "0 6px 16px rgba(239, 68, 68, 0.25)";
            e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)";
            // Hiệu ứng xoay icon nhẹ khi hover
            const svg = e.currentTarget.querySelector("svg");
            if (svg) svg.style.transform = "rotate(-45deg)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background =
              "linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(239, 68, 68, 0.04) 100%)";
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow =
              "0 2px 10px rgba(239, 68, 68, 0.1)";
            e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.35)";
            const svg = e.currentTarget.querySelector("svg");
            if (svg) svg.style.transform = "rotate(0deg)";
          }}
        >
          <div style={{ transition: "transform 0.3s ease", display: "flex" }}>
            <ResetIconSVG size={16} color="#ef4444" />
          </div>
          Reset về mặc định
        </button>
      </div>

      {/* CHANGE 2: Grid 3 cột ngang hàng trên desktop, 1 cột trên mobile */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "18px",
          alignItems: "start",
        }}
      >
        {SENSORS.map((s) => {
          const IconComp = SENSOR_ICON_MAP[s.key];
          const color = SENSOR_COLOR[s.key];

          /* --- CHANGE 3: Icon lớn + animated background cho header mỗi card --- */
          const bgGradient = {
            temp: "radial-gradient(ellipse at top left, rgba(255,159,67,0.13) 0%, transparent 70%)",
            humi: "radial-gradient(ellipse at top left, rgba(0,209,255,0.13) 0%, transparent 70%)",
            light:
              "radial-gradient(ellipse at top left, rgba(255,193,7,0.13) 0%, transparent 70%)",
          }[s.key];

          return (
            <div
              key={s.key}
              className="card-hover-lift"
              style={{
                background: `linear-gradient(160deg, var(--bg-card) 0%, rgba(0,0,0,0.08) 100%)`,
                borderRadius: "18px",
                border: `1px solid ${color}33`,
                padding: "22px",
                position: "relative",
                overflow: "hidden",
                boxShadow: `0 2px 20px ${color}14, 0 2px 16px rgba(0,0,0,0.14)`,
              }}
            >
              {/* glow bg */}
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  background: bgGradient,
                  pointerEvents: "none",
                }}
              />

              {/* Header với icon to, sinh động */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "14px",
                  marginBottom: "20px",
                  paddingBottom: "16px",
                  borderBottom: `1px solid ${color}22`,
                }}
              >
                <div
                  style={{
                    width: "62px",
                    height: "62px",
                    borderRadius: "16px",
                    background: `linear-gradient(135deg, ${color}22 0%, ${color}0a 100%)`,
                    border: `1.5px solid ${color}44`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    boxShadow: `0 4px 18px ${color}30, inset 0 1px 0 ${color}22`,
                    flexShrink: 0,
                  }}
                >
                  <IconComp size={36} />
                </div>
                <div>
                  <div
                    style={{
                      fontWeight: 800,
                      fontSize: "1.05rem",
                      color: color,
                      letterSpacing: "0.02em",
                    }}
                  >
                    {s.label}
                  </div>
                  <div
                    style={{
                      fontSize: "0.76rem",
                      color: "var(--text-secondary)",
                      marginTop: "2px",
                    }}
                  >
                    Đơn vị:{" "}
                    <span style={{ color: color, fontWeight: 700 }}>
                      {s.unit}
                    </span>
                    &nbsp;·&nbsp;Khoảng: {s.min} → {s.max}
                  </div>
                </div>
              </div>

              {/* Min / Max với nút +/- */}
              {["min", "max"].map((bound) => {
                const bColor = bound === "min" ? "#00D1FF" : "#FF6B6B";
                const step = s.key === "temp" ? 0.5 : 1;
                const curVal = parseFloat(draft[s.key]?.[bound]) || 0;
                const otherBound = bound === "min" ? "max" : "min";
                const otherVal =
                  parseFloat(draft[s.key]?.[otherBound]) ??
                  (bound === "min" ? s.max : s.min);

                const adjustVal = (delta) => {
                  const newVal = Math.round((curVal + delta) * 10) / 10;
                  const clamped = clamp(newVal, s.min, s.max);
                  setDraft((prev) => ({
                    ...prev,
                    [s.key]: { ...prev[s.key], [bound]: clamped },
                  }));
                };

                return (
                  <div
                    key={bound}
                    style={{
                      marginBottom: "14px",
                      background: `linear-gradient(135deg, ${bColor}08 0%, transparent 100%)`,
                      borderRadius: "12px",
                      padding: "12px 14px",
                      border: `1px solid ${bColor}22`,
                    }}
                  >
                    <div
                      style={{
                        fontSize: "0.72rem",
                        fontWeight: 700,
                        color: bColor,
                        letterSpacing: "0.06em",
                        textTransform: "uppercase",
                        marginBottom: "10px",
                        display: "flex",
                        alignItems: "center",
                        gap: "5px",
                      }}
                    >
                      <span
                        style={{
                          width: "3px",
                          height: "10px",
                          borderRadius: "2px",
                          background: bColor,
                          boxShadow: `0 0 5px ${bColor}88`,
                          display: "inline-block",
                        }}
                      />
                      {bound === "min" ? "↓ Ngưỡng dưới" : "↑ Ngưỡng trên"}
                    </div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <StepBtn color={bColor} onClick={() => adjustVal(-step)}>
                        −
                      </StepBtn>
                      <div style={{ flex: 1, position: "relative" }}>
                        <input
                          type="number"
                          style={{
                            ...inputStyle,
                            width: "100%",
                            textAlign: "center",
                            fontWeight: 800,
                            fontSize: "1.1rem",
                            color: bColor,
                            paddingRight: "32px",
                          }}
                          value={draft[s.key]?.[bound] ?? ""}
                          onChange={(e) => {
                            const val =
                              e.target.value === ""
                                ? ""
                                : parseFloat(e.target.value);
                            setDraft((prev) => ({
                              ...prev,
                              [s.key]: { ...prev[s.key], [bound]: val },
                            }));
                          }}
                        />
                        <span
                          style={{
                            position: "absolute",
                            right: "10px",
                            top: "50%",
                            transform: "translateY(-50%)",
                            fontSize: "0.8rem",
                            color: bColor,
                            fontWeight: 600,
                            pointerEvents: "none",
                          }}
                        >
                          {s.unit}
                        </span>
                      </div>
                      <StepBtn color={bColor} onClick={() => adjustVal(step)}>
                        +
                      </StepBtn>
                    </div>
                  </div>
                );
              })}

              <DualThresholdSlider
                sensor={s}
                draft={draft}
                setDraft={setDraft}
                activeThumb={activeThumb}
                setActiveThumb={setActiveThumb}
                getNum={getNum}
                clamp={clamp}
              />
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  marginTop: "10px",
                }}
              >
                <button
                  className="btn btn-primary"
                  disabled={saving}
                  onClick={() => handleSave(s.key)}
                  style={{
                    background: `linear-gradient(135deg, ${color}cc 0%, ${color}88 100%)`,
                    border: "none",
                    color: "#fff",
                    fontWeight: 700,
                    padding: "8px 20px",
                    borderRadius: "10px",
                    cursor: "pointer",
                    fontSize: "0.88rem",
                    boxShadow: `0 4px 14px ${color}44`,
                    transition: "all 0.2s",
                  }}
                >
                  {saving ? "Lưu..." : "Lưu"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

/* ─────────────────── 2. KÊNH THÔNG BÁO ─────────────────── */
/* ─────────────────── 2. KÊNH THÔNG BÁO ─────────────────── */
function ChannelTab({ addToast }) {
  const [channels, setChannels] = useState({ telegram: { enabled: false }, email: { enabled: false } });
  const [draft, setDraft]       = useState(null);
  const [saving, setSaving]     = useState('');
  const prevDraftRef = useRef(null);

  useEffect(() => {
    axios.get(`${API}/notification-channels?houseid=HS001`)
      .then(r => { setChannels(r.data); const d = JSON.parse(JSON.stringify(r.data)); setDraft(d); prevDraftRef.current = JSON.parse(JSON.stringify(d)); })
      .catch(() => { const d = { telegram: { enabled: false }, email: { enabled: false } }; setDraft(d); prevDraftRef.current = JSON.parse(JSON.stringify(d)); });
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
      prevDraftRef.current = JSON.parse(JSON.stringify({ ...prevDraftRef.current, [channel]: d }));
      addToast(`✅ Đã cập nhật kênh ${channel === 'telegram' ? 'Telegram' : 'Email'}!`, 'success');
    } catch (e) { addToast(e.response?.data?.message || 'Lỗi cập nhật kênh!', 'error'); }
    setSaving('');
  };

  const setField = (channel, field, value) =>
    setDraft(prev => ({ ...prev, [channel]: { ...prev[channel], [field]: value } }));

  const handleToggle = async (channel, newVal) => {
    setField(channel, 'enabled', newVal);
    setSaving(channel);
    const d = { ...(draft[channel] || {}), enabled: newVal };
    const body = { houseid: 'HS001', channel, enabled: newVal };
    if (channel === 'telegram') { body.bot_token = d.bot_token || ''; body.chat_id = d.chat_id || ''; }
    if (channel === 'email')    { body.address = d.address || ''; }
    try {
      await axios.post(`${API}/notification-channels`, body);
      setChannels(prev => ({ ...prev, [channel]: d }));
      prevDraftRef.current = JSON.parse(JSON.stringify({ ...prevDraftRef.current, [channel]: d }));
      addToast(`${newVal ? '🔔 Đã bật' : '🔕 Đã tắt'} kênh ${channel === 'telegram' ? 'Telegram' : 'Email'}!`, 'success');
    } catch (e) { addToast('Lỗi thay đổi trạng thái!', 'error'); }
    setSaving('');
  };

  if (!draft) return <p style={{ color: 'var(--text-secondary)' }}>Đang tải...</p>;

  /* SỬA LỖI TẠI ĐÂY: Đổi tên thành chữ thường và coi nó như một hàm render */
  const renderChannelCard = (channel, accentColor, icon, title, fields) => {
    const isEnabled = !!draft[channel]?.enabled;
    const isSaving  = saving === channel;
    return (
      <div className="card-hover-lift" style={{
        borderRadius: '18px', padding: '24px', marginBottom: '20px',
        border: `1.5px solid ${isEnabled ? accentColor + '55' : 'var(--border-color)'}`,
        background: isEnabled
          ? `linear-gradient(160deg, ${accentColor}12 0%, ${accentColor}05 50%, rgba(0,0,0,0.05) 100%)`
          : 'linear-gradient(160deg, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0.18) 100%)',
        boxShadow: isEnabled
          ? `0 4px 28px ${accentColor}20, 0 1px 0 ${accentColor}18 inset`
          : '0 2px 16px rgba(0,0,0,0.18)',
        transition: 'all 0.4s cubic-bezier(0.4,0,0.2,1)',
        position: 'relative', overflow: 'hidden',
      }}>
        {isEnabled && <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`, pointerEvents: 'none' }} />}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', paddingBottom: '14px', paddingLeft: '14px', borderBottom: `1px solid ${isEnabled ? accentColor + '33' : 'var(--border-color)'}`, position: 'relative' }}>
          <span style={{ position: 'absolute', left: 0, top: '2px', bottom: '14px', width: '3px', borderRadius: '4px', background: `linear-gradient(180deg, ${accentColor}, ${accentColor}44)`, boxShadow: `0 0 8px ${accentColor}66` }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px', margin: 0, opacity: isEnabled ? 1 : 0.55, transition: 'opacity 0.3s' }}>
            {icon}
            <span style={{ color: isEnabled ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{title}</span>
            <StatusBadge ok={channels[channel]?.enabled} label={channels[channel]?.enabled ? 'Đang bật' : 'Tắt'} />
          </h3>
          <label className="toggle-switch" style={{ position: 'relative', zIndex: 1 }}>
            <input type="checkbox" checked={isEnabled} onChange={e => handleToggle(channel, e.target.checked)} />
            <span className="slider"></span>
          </label>
        </div>

        <div style={{ opacity: isEnabled ? 1 : 0.38, pointerEvents: isEnabled ? 'auto' : 'none', transition: 'opacity 0.35s' }}>
          {fields}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
            <button className="btn btn-primary" disabled={isSaving} onClick={() => handleSave(channel)}
              style={{ background: `linear-gradient(135deg, ${accentColor}cc 0%, ${accentColor}88 100%)`, border: 'none', color: '#fff', fontWeight: 700, padding: '8px 20px', borderRadius: '10px', cursor: 'pointer', fontSize: '0.88rem', boxShadow: `0 4px 14px ${accentColor}44`, transition: 'all 0.2s' }}>
              {isSaving ? 'Lưu...' : 'Lưu thông tin'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      {/* SỬA LỖI TẠI ĐÂY: Gọi hàm render trực tiếp thay vì dùng thẻ <ChannelCard /> */}
      {renderChannelCard(
        "telegram",
        "#2AABEE",
        <TelegramIconSVG size={22} />,
        "Telegram Bot",
        <>
          <InputRow label="Bot Token">
            <input style={{ ...inputStyle, flex: 1, minWidth: '200px' }} placeholder="7123456789:AAF..."
              value={draft.telegram?.bot_token || ''} onChange={e => setField('telegram', 'bot_token', e.target.value)} />
          </InputRow>
          <InputRow label="Chat ID">
            <input style={{ ...inputStyle, flex: 1, minWidth: '200px' }} placeholder="123456789"
              value={draft.telegram?.chat_id || ''} onChange={e => setField('telegram', 'chat_id', e.target.value)} />
          </InputRow>
        </>
      )}

      {renderChannelCard(
        "email",
        "#EA4335",
        <EmailIconSVG size={22} />,
        "Email (Gmail)",
        <>
          <InputRow label="Email nhận">
            <input style={{ ...inputStyle, flex: 1, minWidth: '200px' }} type="email" placeholder="recipient@gmail.com"
              value={draft.email?.address || ''} onChange={e => setField('email', 'address', e.target.value)} />
          </InputRow>
        </>
      )}
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
  { id: 1, label: '🚨 Đèn báo trộm' }, { id: 2, label: '💡 Đèn 2' },
  { id: 3, label: '💡 Đèn 3' }, { id: 4, label: '💡 Đèn 4' },
  { id: 6, label: '🚪 Servo' },
  { id: 7, label: '🌀 Quạt (0-100%)' },
];
const FAN_LEVELS   = [70, 80, 90, 100];
/* CHANGE 5: EMPTY_RULE nay dùng conditions (mảng), thay vì condition đơn lẻ */
const EMPTY_RULE   = {
  name: '', enabled: true,
  conditions: [{ sensor: 'temp', op: 'gt', value: 35 }],
  actions: []
};

const StatusPicker = ({ value, onChange, accentColor = '#10b981' }) => {
  const options = [
    { val: 'true', label: 'Bật', icon: '✅', color: '#10b981' },
    { val: 'false', label: 'Tắt', icon: '⭕', color: '#ef4444' }
  ];

  return (
    <div style={{
      display: 'flex',
      background: 'rgba(0,0,0,0.2)',
      padding: '4px',
      borderRadius: '10px',
      border: '1px solid var(--border-color)',
      gap: '4px'
    }}>
      {options.map(opt => {
        const isActive = String(value) === opt.val;
        return (
          <button
            key={opt.val}
            onClick={() => onChange(opt.val === 'true')}
            style={{
              padding: '6px 12px',
              borderRadius: '7px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.82rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              background: isActive ? opt.color : 'transparent',
              color: isActive ? '#fff' : 'var(--text-secondary)',
              boxShadow: isActive ? `0 4px 12px ${opt.color}44` : 'none',
              transform: isActive ? 'scale(1.05)' : 'scale(1)',
            }}
          >
            <span style={{ fontSize: '1rem', filter: isActive ? 'none' : 'grayscale(1)' }}>
              {opt.icon}
            </span>
            {opt.label}
          </button>
        );
      })}
    </div>
  );
};

function AutoRuleTab({ addToast }) {
  const [rules, setRules]       = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft]       = useState(EMPTY_RULE);
  const [editName, setEditName] = useState(null);
  const [saving, setSaving]     = useState(false);
  /* CHANGE 5: state cho Device Picker popup */
  const [showDevicePicker, setShowDevicePicker] = useState(false);

  const fetchRules = useCallback(async () => {
    try { const r = await axios.get(`${API}/automation-rules?houseid=HS001`); setRules(r.data || []); } catch {}
  }, []);

  useEffect(() => { fetchRules(); }, [fetchRules]);

  const openCreate = () => { setDraft(JSON.parse(JSON.stringify(EMPTY_RULE))); setEditName(null); setShowForm(true); };
  const openEdit = (rule) => {
    /* CHANGE 5: hỗ trợ cả conditions (mảng mới) lẫn condition (cũ) */
    const conds = rule.conditions
      ? rule.conditions.map(c => ({ sensor: c.sensor || 'temp', op: c.op || 'gt', value: c.value || 0 }))
      : [{ sensor: rule.condition?.sensor || 'temp', op: rule.condition?.op || 'gt', value: rule.condition?.value || 0 }];
    setDraft({
      name: rule.name,
      enabled: rule.enabled,
      conditions: conds,
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
    if (draft.actions.length === 0) {
      addToast('Bạn chưa thêm thiết bị phản hồi cho kịch bản!', 'error');
      return;
    }
    for (const c of draft.conditions) {
      if (isNaN(parseFloat(c.value))) { addToast('Giá trị điều kiện phải là số!', 'error'); return; }
    }
    /* CHANGE 5: kiểm tra conflict - cùng sensor + op đối lập */
    const sensorConds = {};
    for (const c of draft.conditions) {
      if (!sensorConds[c.sensor]) sensorConds[c.sensor] = [];
      sensorConds[c.sensor].push(c);
    }
    for (const [sensor, conds] of Object.entries(sensorConds)) {
      if (conds.length > 1) {
        const hasGt = conds.some(c => c.op === 'gt' || c.op === 'gte');
        const hasLt = conds.some(c => c.op === 'lt' || c.op === 'lte');
        if (hasGt && hasLt) {
          const gtVal = Math.max(...conds.filter(c => c.op === 'gt' || c.op === 'gte').map(c => parseFloat(c.value)));
          const ltVal = Math.min(...conds.filter(c => c.op === 'lt' || c.op === 'lte').map(c => parseFloat(c.value)));
          if (gtVal >= ltVal) { addToast(`⚠️ Xung đột điều kiện: ${SENSOR_LABEL[sensor]} không thể vừa > ${gtVal} vừa < ${ltVal}!`, 'error'); return; }
        }
      }
    }
    setSaving(true);
    try {
      await axios.post(`${API}/automation-rules`, {
        houseid: 'HS001', name: draft.name.trim(),
        /* CHANGE 5: gửi cả conditions (mảng) + condition (tương thích ngược = cond đầu tiên) */
        conditions: draft.conditions.map(c => ({ ...c, value: parseFloat(c.value) })),
        condition: { ...draft.conditions[0], value: parseFloat(draft.conditions[0].value) },
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

  const usedDeviceIds = (rowIndex) =>
    new Set(draft.actions.filter((_, j) => j !== rowIndex).map(a => parseInt(a.numberdevice)));

  const setAction    = (i, field, val) => setDraft(prev => { const acts = [...prev.actions]; acts[i] = { ...acts[i], [field]: val }; return { ...prev, actions: acts }; });

  /* CHANGE 5: thêm thiết bị qua Device Picker */
  const addActionWithDevice = (deviceId) => {
    const used = new Set(draft.actions.map(a => parseInt(a.numberdevice)));
    if (used.has(deviceId)) { addToast('Thiết bị này đã có trong kịch bản!', 'info'); return; }
    const dev = DEVICE_OPTS.find(d => d.id === deviceId);
    const defaultStatus = deviceId >= 1 && deviceId <= 5 ? true : 0;
    setDraft(prev => ({ ...prev, actions: [...prev.actions, { numberdevice: deviceId, status: defaultStatus }] }));
    setShowDevicePicker(false);
  };
  const removeAction = (i) => setDraft(prev => ({ ...prev, actions: prev.actions.filter((_, j) => j !== i) }));

  /* CHANGE 5: thêm / xóa điều kiện */
  const addCondition = () => {
    const usedSensors = new Set(draft.conditions.map(c => c.sensor));
    const nextSensor = SENSOR_OPTS.find(s => !usedSensors.has(s));
    if (!nextSensor) { addToast('Đã thêm tất cả loại cảm biến!', 'info'); return; }
    setDraft(prev => ({ ...prev, conditions: [...prev.conditions, { sensor: nextSensor, op: 'gt', value: 0 }] }));
  };
  const removeCondition = (i) => setDraft(prev => ({ ...prev, conditions: prev.conditions.filter((_, j) => j !== i) }));
  const setCondition = (i, field, val) => setDraft(prev => {
    const conds = [...prev.conditions];
    conds[i] = { ...conds[i], [field]: val };
    return { ...prev, conditions: conds };
  });

  /* CHANGE 5: nút +/- to cho giá trị điều kiện */
  const CondStepBtn = ({ onClick, children }) => (
    <button onClick={onClick} style={{
      width: '34px', height: '34px', borderRadius: '9px', border: '1.5px solid rgba(0,209,255,0.4)',
      background: 'linear-gradient(135deg, rgba(0,209,255,0.15) 0%, rgba(0,209,255,0.05) 100%)',
      color: '#00D1FF', fontWeight: 900, fontSize: '1.15rem',
      cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0, transition: 'all 0.18s', lineHeight: 1,
      boxShadow: '0 2px 8px rgba(0,209,255,0.2)',
    }}
    onMouseEnter={e => { e.currentTarget.style.background = 'rgba(0,209,255,0.25)'; e.currentTarget.style.transform = 'scale(1.1)'; }}
    onMouseLeave={e => { e.currentTarget.style.background = 'linear-gradient(135deg, rgba(0,209,255,0.15) 0%, rgba(0,209,255,0.05) 100%)'; e.currentTarget.style.transform = 'scale(1)'; }}
    >{children}</button>
  );

  /* CHANGE 5: nút +/- cho action */
  const ActStepBtn = ({ color, onClick, children }) => (
    <button onClick={onClick} style={{
      width: '34px', height: '34px', borderRadius: '9px', border: `1.5px solid ${color}44`,
      background: `linear-gradient(135deg, ${color}18 0%, ${color}08 100%)`,
      color: color, fontWeight: 900, fontSize: '1.15rem',
      cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0, transition: 'all 0.18s', lineHeight: 1,
    }}
    onMouseEnter={e => { e.currentTarget.style.background = `${color}28`; e.currentTarget.style.transform = 'scale(1.1)'; }}
    onMouseLeave={e => { e.currentTarget.style.background = `linear-gradient(135deg, ${color}18 0%, ${color}08 100%)`; e.currentTarget.style.transform = 'scale(1)'; }}
    >{children}</button>
  );

  /* CHANGE 5: Device Picker modal/dropdown */
  const DevicePickerModal = () => {
    const usedIds = new Set(draft.actions.map(a => parseInt(a.numberdevice)));
    const available = DEVICE_OPTS.filter(d => !usedIds.has(d.id));
    return (
      <div style={{ position: 'fixed', inset: 0, zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(4px)' }}
        onClick={() => setShowDevicePicker(false)}>
        <div style={{ background: 'var(--bg-card)', borderRadius: '18px', padding: '24px', minWidth: '300px', maxWidth: '380px', width: '90%', border: '1px solid rgba(16,185,129,0.3)', boxShadow: '0 8px 40px rgba(0,0,0,0.4), 0 0 60px rgba(16,185,129,0.08)' }}
          onClick={e => e.stopPropagation()}>
          <div style={{ fontWeight: 800, fontSize: '1rem', color: '#10b981', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BoltIconSVG size={18} color="#10b981" /> Chọn thiết bị
          </div>
          {available.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '20px 0', fontSize: '0.88rem' }}>✅ Tất cả thiết bị đã được thêm</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {available.map(dev => (
                <button key={dev.id} onClick={() => addActionWithDevice(dev.id)} style={{
                  padding: '12px 16px', borderRadius: '12px', border: '1.5px solid rgba(16,185,129,0.25)',
                  background: 'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, transparent 100%)',
                  color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.92rem', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: '10px', textAlign: 'left',
                  transition: 'all 0.18s',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(16,185,129,0.15)'; e.currentTarget.style.borderColor = 'rgba(16,185,129,0.5)'; e.currentTarget.style.transform = 'translateX(4px)'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, transparent 100%)'; e.currentTarget.style.borderColor = 'rgba(16,185,129,0.25)'; e.currentTarget.style.transform = 'translateX(0)'; }}
                >
                  <span style={{ fontSize: '1.3rem' }}>{dev.label.split(' ')[0]}</span>
                  <span>{dev.label.slice(dev.label.indexOf(' ')+1)}</span>
                  <span style={{ marginLeft: 'auto', color: '#10b981', fontSize: '0.78rem', fontWeight: 700 }}>+ Thêm</span>
                </button>
              ))}
            </div>
          )}
          <button onClick={() => setShowDevicePicker(false)} style={{ marginTop: '16px', width: '100%', padding: '9px', borderRadius: '10px', border: '1px solid var(--border-color)', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}>Đóng</button>
        </div>
      </div>
    );
  };

  return (
    <>
      {/* CHANGE 5: Device Picker modal */}
      {showDevicePicker && <DevicePickerModal />}

      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          marginBottom: "16px",
        }}
      >
        <button
          onClick={openCreate}
          style={{
            padding: "10px 22px",
            borderRadius: "11px",
            background:
              "linear-gradient(135deg, rgba(167,139,250,0.18) 0%, rgba(167,139,250,0.08) 100%)",
            border: "1px solid rgba(167,139,250,0.4)",
            color: "#a78bfa",
            fontWeight: 700,
            fontSize: "0.88rem",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            boxShadow: "0 0 16px rgba(167,139,250,0.15)",
            transition: "all 0.2s",
          }}
        >
          <BoltIconSVG size={18} color="#a78bfa" /> Tạo kịch bản mới
        </button>
      </div>

      {showForm && (
        <Card
          style={{
            border: "1px solid rgba(0,209,255,0.3)",
            boxShadow: "0 0 28px rgba(0,209,255,0.08)",
          }}
        >
          <SectionTitle color="#00D1FF">
            <RadarIconSVG size={17} color="#00D1FF" />
            {editName ? `Sửa: ${editName}` : "Tạo kịch bản mới"}
          </SectionTitle>

          <InputRow label="Tên kịch bản">
            <input
              style={{ ...inputStyle, flex: 1 }}
              placeholder="VD: Bật quạt khi nóng"
              value={draft.name}
              onChange={(e) =>
                setDraft((p) => ({ ...p, name: e.target.value }))
              }
            />
          </InputRow>

          {/* CHANGE 5: Multi-conditions block */}
          <div
            style={{
              background:
                "linear-gradient(135deg, rgba(0,209,255,0.06) 0%, var(--bg-card-inner) 100%)",
              borderRadius: "12px",
              padding: "16px",
              marginBottom: "16px",
              border: "1px solid rgba(0,209,255,0.15)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "12px",
              }}
            >
              <div
                style={{
                  fontSize: "0.78rem",
                  fontWeight: 700,
                  color: "#00D1FF",
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span
                  style={{
                    width: "3px",
                    height: "14px",
                    background: "#00D1FF",
                    borderRadius: "2px",
                    boxShadow: "0 0 6px #00D1FF88",
                    display: "inline-block",
                  }}
                />
                <RadarIconSVG size={14} color="#00D1FF" /> Điều kiện kích hoạt
              </div>
              {/* CHANGE 5: nút thêm điều kiện */}
              {draft.conditions.length < 3 && (
                <button
                  onClick={addCondition}
                  style={{
                    padding: "5px 12px",
                    borderRadius: "8px",
                    border: "1.5px solid rgba(0,209,255,0.4)",
                    background: "rgba(0,209,255,0.1)",
                    color: "#00D1FF",
                    fontWeight: 700,
                    fontSize: "0.8rem",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "5px",
                  }}
                >
                  + Thêm điều kiện
                </button>
              )}
            </div>

            {draft.conditions.map((cond, ci) => (
              <div
                key={ci}
                style={{
                  display: "flex",
                  gap: "8px",
                  flexWrap: "wrap",
                  alignItems: "center",
                  marginBottom: ci < draft.conditions.length - 1 ? "10px" : 0,
                  padding: "10px",
                  background: "rgba(0,209,255,0.04)",
                  borderRadius: "10px",
                  border: "1px solid rgba(0,209,255,0.1)",
                }}
              >
                {ci > 0 && (
                  <span
                    style={{
                      fontSize: "0.7rem",
                      fontWeight: 800,
                      color: "#00D1FF",
                      background: "rgba(0,209,255,0.18)",
                      border: "1px solid rgba(0,209,255,0.3)",
                      borderRadius: "5px",
                      padding: "2px 7px",
                      flexShrink: 0,
                    }}
                  >
                    VÀ
                  </span>
                )}
                <span
                  style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}
                >
                  Nếu
                </span>
                {/* CHANGE 5: chỉ hiển thị sensor chưa được chọn ở điều kiện khác */}
                <select
                  style={selectStyle}
                  value={cond.sensor}
                  onChange={(e) => setCondition(ci, "sensor", e.target.value)}
                >
                  {SENSOR_OPTS.map((s) => {
                    const usedByOther = draft.conditions.some(
                      (c, j) => j !== ci && c.sensor === s,
                    );
                    return (
                      <option key={s} value={s} disabled={usedByOther}>
                        {SENSOR_LABEL[s]}
                        {usedByOther ? " (đã dùng)" : ""}
                      </option>
                    );
                  })}
                </select>
                <select
                  style={selectStyle}
                  value={cond.op}
                  onChange={(e) => setCondition(ci, "op", e.target.value)}
                >
                  {OP_OPTS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
                {/* CHANGE 5: nút +/- cho giá trị điều kiện */}
                <CondStepBtn
                  onClick={() =>
                    setCondition(
                      ci,
                      "value",
                      Math.round((parseFloat(cond.value || 0) - 1) * 10) / 10,
                    )
                  }
                >
                  −
                </CondStepBtn>
                <input
                  type="number"
                  style={{
                    ...inputStyle,
                    width: "80px",
                    textAlign: "center",
                    fontWeight: 700,
                  }}
                  value={cond.value}
                  onChange={(e) => setCondition(ci, "value", e.target.value)}
                />
                <CondStepBtn
                  onClick={() =>
                    setCondition(
                      ci,
                      "value",
                      Math.round((parseFloat(cond.value || 0) + 1) * 10) / 10,
                    )
                  }
                >
                  +
                </CondStepBtn>
                {draft.conditions.length > 1 && (
                  <button
                    onClick={() => removeCondition(ci)}
                    style={{
                      padding: "5px 10px",
                      borderRadius: "8px",
                      border: "1px solid rgba(234,67,53,0.3)",
                      background: "rgba(234,67,53,0.08)",
                      color: "var(--accent-red)",
                      fontWeight: 700,
                      fontSize: "0.82rem",
                      cursor: "pointer",
                      flexShrink: 0,
                    }}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>

          <div
            style={{
              background:
                "linear-gradient(135deg, rgba(16,185,129,0.06) 0%, var(--bg-card-inner) 100%)",
              borderRadius: "12px",
              padding: "16px",
              marginBottom: "16px",
              border: "1px solid rgba(16,185,129,0.15)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "12px",
              }}
            >
              <span
                style={{
                  fontSize: "0.78rem",
                  fontWeight: 700,
                  color: "#10b981",
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span
                  style={{
                    width: "3px",
                    height: "14px",
                    background: "#10b981",
                    borderRadius: "2px",
                    boxShadow: "0 0 6px #10b98188",
                    display: "inline-block",
                  }}
                />
                <BoltIconSVG size={14} color="#10b981" /> Hành động phản hồi
              </span>
              {/* CHANGE 5: nút thêm thiết bị mở Device Picker */}
              <button
                style={{
                  padding: "7px 14px",
                  borderRadius: "9px",
                  background:
                    "linear-gradient(135deg, rgba(16,185,129,0.18) 0%, rgba(16,185,129,0.08) 100%)",
                  border: "1.5px solid rgba(16,185,129,0.4)",
                  color: "#10b981",
                  fontWeight: 700,
                  fontSize: "0.82rem",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  transition: "all 0.18s",
                  boxShadow: "0 2px 10px rgba(16,185,129,0.18)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(16,185,129,0.25)";
                  e.currentTarget.style.transform = "translateY(-1px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background =
                    "linear-gradient(135deg, rgba(16,185,129,0.18) 0%, rgba(16,185,129,0.08) 100%)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
                onClick={() => setShowDevicePicker(true)}
              >
                + Thêm thiết bị
              </button>
            </div>

            {draft.actions.length === 0 ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "20px",
                  border: "1px dashed rgba(16,185,129,0.2)",
                  borderRadius: "10px",
                  background: "rgba(16,185,129,0.02)",
                }}
              >
                <p
                  style={{
                    color: "var(--text-secondary)",
                    fontSize: "0.85rem",
                    margin: 0,
                  }}
                >
                  Chưa có thiết bị nào. Nhấn <b>"+ Thêm thiết bị"</b> để
                  chọn.
                </p>
              </div>
            ) : (
              /* Nếu đã có thiết bị thì render danh sách như cũ */
              draft.actions.map((act, i) => {
                const devId = parseInt(act.numberdevice);
                const isLight = devId >= 1 && devId <= 5;
                const isServo = devId === 6;
                const isFan = devId === 7;
                const dev = DEVICE_OPTS.find((d) => d.id === devId);
                const devColor = isLight
                  ? "#FFC107"
                  : isServo
                    ? "#00D1FF"
                    : "#a78bfa";

                return (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      gap: "10px",
                      alignItems: "center",
                      marginBottom: "10px",
                      flexWrap: "wrap",
                      background: `linear-gradient(135deg, ${devColor}08 0%, rgba(255,255,255,0.01) 100%)`,
                      borderRadius: "10px",
                      padding: "10px 12px",
                      border: `1px solid ${devColor}20`,
                    }}
                  >
                    <span style={{ fontSize: "1.1rem" }}>
                      {dev?.label.split(" ")[0]}
                    </span>
                    <span
                      style={{
                        color: "var(--text-primary)",
                        fontWeight: 600,
                        fontSize: "0.88rem",
                      }}
                    >
                      {dev?.label.slice(dev.label.indexOf(" ") + 1)}
                    </span>
                    <span
                      style={{
                        color: "var(--text-secondary)",
                        fontSize: "0.85rem",
                        marginLeft: "4px",
                      }}
                    >
                      →
                    </span>

                    {/* Tận dụng StatusPicker mới nếu bạn đã thêm ở bước trước */}
                    {isLight && (
                      <StatusPicker
                        value={act.status}
                        onChange={(val) => setAction(i, "status", val)}
                      />
                    )}

                    {isServo && (
                      <select
                        style={{ ...selectStyle, width: "130px" }}
                        value={String(act.status)}
                        onChange={(e) =>
                          setAction(i, "status", parseFloat(e.target.value))
                        }
                      >
                        <option value="90">🔓 Mở (90°)</option>
                        <option value="0">🔒 Đóng (0°)</option>
                      </select>
                    )}

                    {isFan && (
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                        }}
                      >
                        <ActStepBtn
                          color="#a78bfa"
                          onClick={() => {
                            /* logic giảm mức quạt */
                          }}
                        >
                          −
                        </ActStepBtn>
                        <select
                          style={{ ...selectStyle, width: "110px" }}
                          value={act.status}
                          onChange={(e) =>
                            setAction(i, "status", parseFloat(e.target.value))
                          }
                        >
                          {FAN_LEVELS.map((l) => (
                            <option key={l} value={l}>
                              Mức {l}%
                            </option>
                          ))}
                        </select>
                        <ActStepBtn
                          color="#a78bfa"
                          onClick={() => {
                            /* logic tăng mức quạt */
                          }}
                        >
                          +
                        </ActStepBtn>
                      </div>
                    )}

                    {/* Nút xóa thiết bị này khỏi kịch bản */}
                    <button
                      style={{
                        marginLeft: "auto",
                        padding: "5px 10px",
                        borderRadius: "8px",
                        border: "1px solid rgba(234,67,53,0.3)",
                        background: "rgba(234,67,53,0.08)",
                        color: "var(--accent-red)",
                        fontWeight: 700,
                        fontSize: "0.82rem",
                        cursor: "pointer",
                      }}
                      onClick={() => removeAction(i)}
                    >
                      ✕
                    </button>
                  </div>
                );
              })
            )}
          </div>

          <InputRow label="Kích hoạt">
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={draft.enabled}
                onChange={(e) =>
                  setDraft((p) => ({ ...p, enabled: e.target.checked }))
                }
              />
              <span className="slider"></span>
            </label>
            <span
              style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}
            >
              {draft.enabled ? "Bật ngay" : "Tạm tắt"}
            </span>
          </InputRow>

          <div
            style={{
              display: "flex",
              gap: "12px",
              justifyContent: "flex-end",
              marginTop: "16px",
            }}
          >
            <button
              className="btn btn-danger"
              onClick={() => setShowForm(false)}
            >
              Hủy
            </button>
            <button
              className="btn btn-success"
              disabled={saving}
              onClick={handleSave}
            >
              {saving ? "Lưu..." : "Lưu"}
            </button>
          </div>
        </Card>
      )}

      {rules.length === 0 && !showForm && (
        <Card>
          <p
            style={{
              color: "var(--text-secondary)",
              textAlign: "center",
              padding: "30px",
            }}
          >
            Chưa có kịch bản nào. Nhấn "Tạo kịch bản mới" để bắt đầu.
          </p>
        </Card>
      )}

      {rules.map((rule) => {
        /* CHANGE 5: hiển thị tất cả conditions, fallback về condition đơn */
        const conds =
          rule.conditions || (rule.condition ? [rule.condition] : []);
        const firstCond = conds[0] || {};
        const sColor =
          { temp: "#FF9F43", humi: "#00D1FF", light: "#FFC107" }[
            firstCond?.sensor
          ] || "var(--accent-blue)";
        const SIcon = SENSOR_ICON_MAP[firstCond?.sensor];
        const actionList = rule.actions || rule.action || [];
        return (
          <Card
            key={rule._id}
            style={{
              borderLeft: `3px solid ${rule.enabled ? sColor : "var(--border-color)"}`,
              boxShadow: rule.enabled
                ? `0 2px 20px ${sColor}14, 0 2px 16px rgba(0,0,0,0.14)`
                : undefined,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                flexWrap: "wrap",
                gap: "10px",
              }}
            >
              <div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    marginBottom: "10px",
                  }}
                >
                  {SIcon && <SIcon size={28} />}
                  <span
                    style={{
                      fontWeight: 700,
                      fontSize: "0.98rem",
                      color: "var(--text-primary)",
                    }}
                  >
                    {rule.name}
                  </span>
                  <StatusBadge
                    ok={rule.enabled}
                    label={rule.enabled ? "Đang bật" : "Tắt"}
                  />
                </div>
                {/* CHANGE 5: hiển thị nhiều điều kiện */}
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                    marginBottom: "6px",
                  }}
                >
                  {conds.map((cond, ci) => {
                    const opLabel =
                      OP_OPTS.find((o) => o.value === cond?.op)?.label ||
                      cond?.op;
                    const cColor =
                      { temp: "#FF9F43", humi: "#00D1FF", light: "#FFC107" }[
                        cond?.sensor
                      ] || "var(--accent-blue)";
                    return (
                      <div
                        key={ci}
                        style={{
                          fontSize: "0.83rem",
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                          flexWrap: "wrap",
                        }}
                      >
                        {ci > 0 && (
                          <span
                            style={{
                              fontSize: "0.68rem",
                              fontWeight: 800,
                              color: "#00D1FF",
                              background: "rgba(0,209,255,0.15)",
                              border: "1px solid rgba(0,209,255,0.3)",
                              borderRadius: "4px",
                              padding: "1px 5px",
                            }}
                          >
                            VÀ
                          </span>
                        )}
                        <span style={{ color: "var(--text-secondary)" }}>
                          Nếu
                        </span>
                        <span
                          style={{
                            background: `${cColor}18`,
                            color: cColor,
                            border: `1px solid ${cColor}44`,
                            borderRadius: "6px",
                            padding: "2px 8px",
                            fontWeight: 700,
                            fontSize: "0.8rem",
                          }}
                        >
                          {SENSOR_LABEL[cond?.sensor]}
                        </span>
                        <span
                          style={{
                            background: "rgba(0,209,255,0.1)",
                            color: "#00D1FF",
                            border: "1px solid rgba(0,209,255,0.3)",
                            borderRadius: "6px",
                            padding: "2px 8px",
                            fontWeight: 700,
                            fontSize: "0.8rem",
                          }}
                        >
                          {opLabel}
                        </span>
                        <span
                          style={{
                            background: "rgba(255,159,67,0.1)",
                            color: "#FF9F43",
                            border: "1px solid rgba(255,159,67,0.3)",
                            borderRadius: "6px",
                            padding: "2px 8px",
                            fontWeight: 700,
                            fontSize: "0.8rem",
                          }}
                        >
                          {cond?.value}
                        </span>
                      </div>
                    );
                  })}
                </div>
                <div
                  style={{
                    fontSize: "0.83rem",
                    color: "var(--text-secondary)",
                    display: "flex",
                    alignItems: "center",
                    gap: "5px",
                  }}
                >
                  <BoltIconSVG size={14} color="#10b981" />
                  {actionList
                    .map((a) => {
                      const devLabel =
                        DEVICE_OPTS.find(
                          (d) => d.id === parseInt(a.numberdevice),
                        )?.label || `Thiết bị ${a.numberdevice}`;
                      return `${devLabel} → ${fmtDeviceVal(a.status)}`;
                    })
                    .join("  ·  ")}
                </div>
              </div>
              <div
                style={{
                  display: "flex",
                  gap: "8px",
                  alignItems: "center",
                  flexShrink: 0,
                }}
              >
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={rule.enabled}
                    onChange={() => handleToggle(rule)}
                  />
                  <span className="slider"></span>
                </label>
                <button
                  className="btn btn-primary"
                  style={{ padding: "6px 14px", borderRadius: "9px" }}
                  onClick={() => openEdit(rule)}
                >
                  Sửa
                </button>
                <button
                  className="btn btn-danger"
                  style={{ padding: "6px 12px", borderRadius: "9px" }}
                  onClick={() => handleDelete(rule.name)}
                >
                  🗑
                </button>
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