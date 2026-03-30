import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API = 'http://localhost:5000/api';

function formatVNTime(timeStr) {
  if (!timeStr) return '--';
  try {
    const match = timeStr.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/);
    if (match) {
      const [_, y, mo, d, h, mi, s] = match;
      return `${h}:${mi}:${s}  ${d}/${mo}/${y}`;
    }
    return timeStr;
  } catch { return timeStr; }
}

function TabBar({ tabs, active, onChange }) {
  return (
    <div style={{
      display: 'flex', gap: '4px',
      background: 'var(--bg-card-inner)', padding: '4px', borderRadius: '10px',
      border: '1px solid var(--border-color)', marginBottom: '24px', width: 'fit-content'
    }}>
      {tabs.map(t => (
        <button key={t.key} onClick={() => onChange(t.key)} style={{
          padding: '8px 20px', borderRadius: '7px', border: 'none',
          cursor: 'pointer', fontWeight: 500, fontSize: '0.9rem', transition: 'all 0.2s',
          background: active === t.key ? 'var(--accent-blue)' : 'transparent',
          color: active === t.key ? '#fff' : 'var(--text-secondary)',
        }}>{t.label}</button>
      ))}
    </div>
  );
}

function Card({ children, style }) {
  return (
    <div style={{
      background: 'var(--bg-card)', borderRadius: '15px',
      border: '1px solid var(--border-color)', padding: '24px',
      marginBottom: '20px', ...style
    }}>{children}</div>
  );
}

function SectionTitle({ children }) {
  return (
    <h3 style={{
      fontSize: '1.05rem', fontWeight: 600, marginBottom: '18px',
      paddingBottom: '12px', borderBottom: '1px solid var(--border-color)',
      color: 'var(--text-primary)'
    }}>{children}</h3>
  );
}

function StatusBadge({ ok, label }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: '3px 10px', borderRadius: '20px', fontSize: '0.78rem', fontWeight: 600,
      background: ok ? 'rgba(16,185,129,0.12)' : 'rgba(234,67,53,0.12)',
      color: ok ? '#10b981' : 'var(--accent-red)',
      border: `1px solid ${ok ? '#10b981' : 'var(--accent-red)'}`,
    }}>
      <span style={{ fontSize: '0.6rem' }}>●</span>
      {label}
    </span>
  );
}

function InputRow({ label, children }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px', flexWrap: 'wrap' }}>
      <label style={{ minWidth: '110px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{label}</label>
      {children}
    </div>
  );
}

const inputStyle = {
  background: 'var(--bg-card-inner)', border: '1px solid var(--border-color)',
  color: 'var(--text-primary)', borderRadius: '8px', padding: '8px 12px',
  fontSize: '0.9rem', outline: 'none',
};
const selectStyle = { ...inputStyle, cursor: 'pointer' };

// ── Helper format giá trị thiết bị ────────────────────────────
function fmtDeviceVal(v) {
  if (v === true  || v === 1)  return 'BẬT';
  if (v === false || v === 0)  return 'TẮT';
  if (typeof v === 'number')   return v + '%';
  return String(v);
}

// ── 1. Giám sát ngưỡng ────────────────────────────────────────
function MonitorTab({ addToast }) {
  const [sensor, setSensor]       = useState(null);
  const [thresholds, setThresholds] = useState(null);
  const [logs, setLogs]           = useState([]);
  const [loading, setLoading]     = useState(true);
  const [showLogs, setShowLogs]   = useState(true);

  const SENSOR_META = {
    temp:  { label: 'Nhiệt độ', icon: '🌡️', unit: '°C', color: '#FF9F43' },
    humi:  { label: 'Độ ẩm',    icon: '💧', unit: '%',  color: '#00D1FF' },
    light: { label: 'Ánh sáng', icon: '💡', unit: '%',  color: '#FFC107' },
  };

  const fetchAll = useCallback(async () => {
    try {
      const [thRes, logRes, sensorRes] = await Promise.all([
        axios.get(`${API}/thresholds?houseid=HS001`),
        axios.get(`${API}/danger-logs?houseid=HS001&limit=8`),
        axios.get(`${API}/sensor-data`),
      ]);
      setThresholds(thRes.data);
      setLogs(logRes.data || []);
      setSensor(sensorRes.data);
    } catch { }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    fetchAll();
    const t = setInterval(fetchAll, 10000);
    return () => clearInterval(t);
  }, [fetchAll]);

  if (loading) return <p style={{ color: 'var(--text-secondary)' }}>Đang tải...</p>;

  return (
    <>
      {sensor?.is_danger && (
        <div style={{
          background: 'rgba(234,67,53,0.12)', border: '1px solid var(--accent-red)',
          borderRadius: '12px', padding: '14px 20px', marginBottom: '20px',
          display: 'flex', alignItems: 'center', gap: '10px',
          color: 'var(--accent-red)', fontWeight: 600
        }}>
          🚨 HỆ THỐNG ĐANG CÓ CẢNH BÁO NGUY HIỂM! Kiểm tra dữ liệu bên dưới.
        </div>
      )}

      {/* Cards cảm biến */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: '16px', marginBottom: '24px' }}>
        {Object.entries(SENSOR_META).map(([key, meta]) => {
          const val    = sensor?.[key] ?? '--';
          const th     = thresholds?.[key];
          const numVal = parseFloat(val);
          const over   = th && !isNaN(numVal) && (numVal > th.max || numVal < th.min);
          return (
            <div key={key} style={{
              background: 'var(--bg-card)', borderRadius: '14px', padding: '20px',
              border: `1px solid ${over ? 'var(--accent-red)' : 'var(--border-color)'}`,
              boxShadow: over ? '0 0 16px rgba(234,67,53,0.2)' : 'none', transition: 'all 0.3s'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{meta.icon} {meta.label}</span>
                <StatusBadge ok={!over} label={over ? 'Vượt ngưỡng' : 'An toàn'} />
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: over ? 'var(--accent-red)' : meta.color }}>
                {val}{meta.unit}
              </div>
              {th && (
                <div style={{ marginTop: '8px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  Ngưỡng: {th.min}{meta.unit} – {th.max}{meta.unit}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Lịch sử cảnh báo */}
      <Card>
        <SectionTitle>📋 Lịch sử cảnh báo gần đây</SectionTitle>

        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginBottom: '16px', marginTop: '-10px', gap: '10px' }}>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 600 }}>
            {showLogs ? 'Hiển thị' : 'Ẩn'}
          </span>
          <label className="toggle-switch" title="Giật công tắc để bật/tắt hiển thị lịch sử cảnh báo">
            <input type="checkbox" checked={showLogs} onChange={(e) => setShowLogs(e.target.checked)} />
            <span className="slider"></span>
          </label>
        </div>

        {showLogs ? (
          logs.length === 0
            ? <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '20px' }}>Chưa có cảnh báo nào.</p>
            : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {logs.map((log, i) => (
                  <div key={i} style={{
                    background: 'var(--bg-card-inner)', borderRadius: '10px',
                    padding: '14px 16px', borderLeft: '4px solid var(--accent-red)',
                    borderRadius: '0 10px 10px 0'
                  }}>
                    {/* Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px' }}>
                      <span style={{ fontWeight: 600, color: 'var(--accent-red)' }}>⚠️ {log.type}</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {formatVNTime(log.time)}
                      </span>
                    </div>

                    {/* Vi phạm ngưỡng */}
                    {log.violations?.length > 0 && (
                      <div style={{ marginTop: '6px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {log.violations.map((v, j) => (
                          <span key={j} style={{ marginRight: '10px' }}>
                            {SENSOR_META[v.sensor]?.icon} {SENSOR_META[v.sensor]?.label}: {v.value}
                            {SENSOR_META[v.sensor]?.unit} ({v.threshold === 'max' ? '↑ vượt MAX' : '↓ dưới MIN'} {v.limit})
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Kịch bản tự động */}
                    {log.triggered_rules?.length > 0 && (
                      <div style={{
                        marginTop: '8px', paddingTop: '8px',
                        borderTop: '1px dashed var(--border-color)', fontSize: '0.82rem'
                      }}>
                        {log.triggered_rules.map((rule, ri) => {
                          const changedItems = rule.changes?.filter(c => c.changed) || [];
                          return (
                            <div key={ri} style={{ marginTop: ri > 0 ? '6px' : '0' }}>
                              <span style={{ color: '#10b981', fontWeight: 600 }}>
                                ⚡ {rule.rule_name}:
                              </span>
                              {changedItems.length === 0 ? (
                                <span style={{ color: 'var(--text-secondary)', marginLeft: '8px', fontStyle: 'italic' }}>
                                  ℹ️ Không có thay đổi so với trạng thái hiện tại
                                </span>
                              ) : (
                                changedItems.map((c, ci) => (
                                  <span key={ci} style={{ color: 'var(--text-secondary)', marginLeft: '8px' }}>
                                    {c.device_name}:{' '}
                                    <span style={{ color: 'var(--accent-red)' }}>{fmtDeviceVal(c.from)}</span>
                                    {' ➜ '}
                                    <span style={{ color: '#10b981' }}>{fmtDeviceVal(c.to)}</span>
                                  </span>
                                ))
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Không có kịch bản nào */}
                    {(!log.triggered_rules || log.triggered_rules.length === 0) && log.type !== 'Mất kết nối cảm biến (Quá 30 giây)' && (
                      <div style={{ marginTop: '6px', fontSize: '0.8rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                        ✅ Không có kịch bản tự động nào được kích hoạt
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )
        ) : (
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '20px', fontStyle: 'italic' }}>
            Lịch sử cảnh báo đang bị tắt. Giật công tắc để hiển thị lại.
          </p>
        )}
      </Card>
    </>
  );
}

// ── 2. Cấu hình ngưỡng ────────────────────────────────────────
function DualThresholdSlider({ sensor, draft, setDraft, setActiveThumb, activeThumb, getNum, clamp }) {
  const minValRaw = getNum(draft[sensor.key]?.min, sensor.min);
  const maxValRaw = getNum(draft[sensor.key]?.max, sensor.max);
  
  const mMin = clamp(minValRaw, sensor.min, sensor.max);
  const mMax = clamp(maxValRaw, sensor.min, sensor.max);
  
  const activeMin = Math.min(mMin, mMax);
  const activeMax = Math.max(mMin, mMax);

  const denom = (sensor.max - sensor.min) || 1;
  const leftPct = ((activeMin - sensor.min) / denom) * 100;
  const widthPct = ((activeMax - activeMin) / denom) * 100;

  return (
    <div style={{ marginBottom: '25px', position: 'relative' }}>
      <div className="dual-threshold-slider">
        <div className="base-track">
          <div className="active-track" style={{ left: `${leftPct}%`, width: `${widthPct}%` }} />
        </div>
        
        <input
          className="dual-thumb dual-thumb--min"
          type="range"
          min={sensor.min}
          max={sensor.max}
          step="0.1"
          value={mMin}
          onMouseDown={() => setActiveThumb('min')}
          onChange={(e) => {
            const val = parseFloat(e.target.value);
            setDraft(prev => ({
              ...prev,
              [sensor.key]: { ...prev[sensor.key], min: Math.min(val, mMax) } // Ràng buộc Min <= Max
            }));
          }}
          style={{ 
            zIndex: activeThumb === 'min' ? 5 : 3 
          }}
        />
        
        <input
          className="dual-thumb dual-thumb--max"
          type="range"
          min={sensor.min}
          max={sensor.max}
          step="0.1"
          value={mMax}
          onMouseDown={() => setActiveThumb('max')}
          onChange={(e) => {
            const val = parseFloat(e.target.value);
            setDraft(prev => ({
              ...prev,
              [sensor.key]: { ...prev[sensor.key], max: Math.max(val, mMin) } // Ràng buộc Max >= Min
            }));
          }}
          style={{ 
            zIndex: activeThumb === 'max' ? 5 : 4 
          }}
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
    { key: 'temp',  label: 'Nhiệt độ', icon: '🌡️', unit: '°C', min: -50, max: 500 },
    { key: 'humi',  label: 'Độ ẩm',    icon: '💧', unit: '%',  min: 0,   max: 100 },
    { key: 'light', label: 'Ánh sáng', icon: '💡', unit: '%',  min: 0,   max: 100 },
  ];

  const [thresholds, setThresholds] = useState({ temp:{min:0,max:40}, humi:{min:20,max:80}, light:{min:0,max:90} });
  const [draft, setDraft]           = useState(null);
  const [saving, setSaving]         = useState(false);
  const [activeThumb, setActiveThumb] = useState(null);

  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
  const getNum = (v, fallback) => {
    const n = typeof v === 'string' ? parseFloat(v) : v;
    return Number.isFinite(n) ? n : fallback;
  };

  useEffect(() => {
    axios.get(`${API}/thresholds?houseid=HS001`)
      .then(r => { 
        setThresholds(r.data); 
        setDraft(JSON.parse(JSON.stringify(r.data))); 
      })
      .catch(() => setDraft(JSON.parse(JSON.stringify(thresholds))));
  }, []);

  const handleSave = async (sensor) => {
    setSaving(true);
    try {
      await axios.post(`${API}/thresholds`, {
        houseid: 'HS001', sensor,
        min: parseFloat(draft[sensor].min),
        max: parseFloat(draft[sensor].max),
      });
      setThresholds(prev => ({ ...prev, [sensor]: draft[sensor] }));
      addToast(`✅ Đã cập nhật ngưỡng ${SENSORS.find(s=>s.key===sensor)?.label}!`, 'success');
    } catch (e) {
      addToast(e.response?.data?.message || 'Lỗi cập nhật ngưỡng!', 'error');
    }
    setSaving(false);
  };

  const handleReset = async () => {
    try {
      const r = await axios.post(`${API}/thresholds/reset`, { houseid: 'HS001' });
      setThresholds(r.data.thresholds);
      setDraft(JSON.parse(JSON.stringify(r.data.thresholds)));
      addToast('✅ Đã reset ngưỡng về mặc định!', 'success');
    } catch { addToast('Lỗi reset ngưỡng!', 'error'); }
  };

  if (!draft) return <p style={{ color: 'var(--text-secondary)' }}>Đang tải...</p>;

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
        <button className="btn btn-danger" onClick={handleReset}>🔄 Reset về mặc định</button>
      </div>
      {SENSORS.map(s => (
        <Card key={s.key}>
          <SectionTitle>{s.icon} {s.label} (đơn vị: {s.unit})</SectionTitle>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
            {['min', 'max'].map(bound => (
              <div key={bound}>
                <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Ngưỡng {bound === 'min' ? 'dưới (Min)' : 'trên (Max)'}
                </label>
                <input type="number" style={{ ...inputStyle, width: '100%' }}
                  value={draft[s.key]?.[bound] ?? ''}
                  onChange={e => {
                    const val = e.target.value === '' ? '' : parseFloat(e.target.value);
                    setDraft(prev => ({
                      ...prev,
                      [s.key]: { ...prev[s.key], [bound]: val }
                    }));
                  }} 
                />
              </div>
            ))}
          </div>

          {/* Thanh trượt Dual Slider */}
          <DualThresholdSlider 
            sensor={s} 
            draft={draft} 
            setDraft={setDraft} 
            activeThumb={activeThumb}
            setActiveThumb={setActiveThumb}
            getNum={getNum}
            clamp={clamp}
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
            <button className="btn btn-primary" disabled={saving} onClick={() => handleSave(s.key)}>
              {saving ? 'Đang lưu...' : '💾 Lưu ngưỡng'}
            </button>
          </div>
        </Card>
      ))}
    </>
  );
}

// ── 3. Kênh thông báo ─────────────────────────────────────────
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
    } catch (e) {
      addToast(e.response?.data?.message || 'Lỗi cập nhật kênh!', 'error');
    }
    setSaving('');
  };

  const setField = (channel, field, value) =>
    setDraft(prev => ({ ...prev, [channel]: { ...prev[channel], [field]: value } }));

  if (!draft) return <p style={{ color: 'var(--text-secondary)' }}>Đang tải...</p>;

  return (
    <>
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', paddingBottom: '12px', borderBottom: '1px solid var(--border-color)' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            📲 Telegram Bot
            <StatusBadge ok={channels.telegram?.enabled} label={channels.telegram?.enabled ? 'Đang bật' : 'Tắt'} />
          </h3>
          <label className="toggle-switch">
            <input type="checkbox" checked={!!draft.telegram?.enabled}
              onChange={e => setField('telegram', 'enabled', e.target.checked)} />
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
            {saving === 'telegram' ? 'Đang lưu...' : '💾 Lưu cấu hình'}
          </button>
        </div>
      </Card>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', paddingBottom: '12px', borderBottom: '1px solid var(--border-color)' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            📧 Email (Gmail)
            <StatusBadge ok={channels.email?.enabled} label={channels.email?.enabled ? 'Đang bật' : 'Tắt'} />
          </h3>
          <label className="toggle-switch">
            <input type="checkbox" checked={!!draft.email?.enabled}
              onChange={e => setField('email', 'enabled', e.target.checked)} />
            <span className="slider"></span>
          </label>
        </div>
        <InputRow label="Email nhận">
          <input style={{ ...inputStyle, flex: 1, minWidth: '200px' }} type="email" placeholder="recipient@gmail.com"
            value={draft.email?.address || ''} onChange={e => setField('email', 'address', e.target.value)} />
        </InputRow>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-primary" disabled={saving === 'email'} onClick={() => handleSave('email')}>
            {saving === 'email' ? 'Đang lưu...' : '💾 Lưu cấu hình'}
          </button>
        </div>
      </Card>
    </>
  );
}

// ── 4. Kịch bản tự động ───────────────────────────────────────
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
const FAN_LEVELS = [70, 80, 90, 100]; 
const EMPTY_RULE = {
  name: '', enabled: true,
  condition: { sensor: 'temp', op: 'gt', value: 35 },
  actions: [{ numberdevice: 7, status: 100 }],
};

function AutoRuleTab({ addToast }) {
  const [rules, setRules]       = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft]       = useState(EMPTY_RULE);
  const [editName, setEditName] = useState(null);
  const [saving, setSaving]     = useState(false);

  const fetchRules = useCallback(async () => {
    try { const r = await axios.get(`${API}/automation-rules?houseid=HS001`); setRules(r.data || []); }
    catch { }
  }, []);

  useEffect(() => { fetchRules(); }, [fetchRules]);

  const openCreate = () => { setDraft(JSON.parse(JSON.stringify(EMPTY_RULE))); setEditName(null); setShowForm(true); };

  const openEdit = (rule) => {
    setDraft({
      name: rule.name, enabled: rule.enabled,
      condition: { ...rule.condition },
      actions: rule.actions.map(a => ({ numberdevice: parseInt(a.numberdevice), status: a.status })),
    });
    setEditName(rule.name);
    setShowForm(true);
  };

  const serializeStatus = (devId, status) => {
    const id = parseInt(devId);
    if (id >= 1 && id <= 5) {
      if (status === true  || status === 'true')  return true;
      if (status === false || status === 'false') return false;
      return Boolean(status);
    }
    return parseFloat(status) || 0;
  };

  const handleSave = async () => {
    if (!draft.name.trim()) { addToast('Tên kịch bản không được rỗng!', 'error'); return; }
    setSaving(true);
    try {
      await axios.post(`${API}/automation-rules`, {
        houseid: 'HS001', name: draft.name.trim(),
        condition: { ...draft.condition, value: parseFloat(draft.condition.value) },
        actions: draft.actions.map(a => ({
          numberdevice: parseInt(a.numberdevice),
          status: serializeStatus(a.numberdevice, a.status),
        })),
        enabled: draft.enabled,
      });
      addToast(`✅ Đã lưu kịch bản "${draft.name}"!`, 'success');
      setShowForm(false);
      fetchRules();
    } catch (e) {
      addToast(e.response?.data?.message || 'Lỗi lưu kịch bản!', 'error');
    }
    setSaving(false);
  };

  const handleDelete = async (name) => {
    if (!window.confirm(`Xóa kịch bản "${name}"?`)) return;
    try {
      await axios.delete(`${API}/automation-rules`, { params: { houseid: 'HS001', name } });
      addToast(`Đã xóa kịch bản "${name}".`, 'info');
      fetchRules();
    } catch { addToast('Lỗi xóa kịch bản!', 'error'); }
  };

  const handleToggle = async (rule) => {
    try {
      await axios.patch(`${API}/automation-rules/toggle`, { houseid: 'HS001', name: rule.name, enabled: !rule.enabled });
      fetchRules();
    } catch { addToast('Lỗi thay đổi trạng thái!', 'error'); }
  };

  const setAction = (i, field, val) =>
    setDraft(prev => { const acts = [...prev.actions]; acts[i] = { ...acts[i], [field]: val }; return { ...prev, actions: acts }; });

  const addAction    = () => setDraft(prev => ({ ...prev, actions: [...prev.actions, { numberdevice: 1, status: true }] }));
  const removeAction = (i) => setDraft(prev => ({ ...prev, actions: prev.actions.filter((_, j) => j !== i) }));

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
        <button className="btn-add" style={{ width: 'auto', padding: '10px 24px' }} onClick={openCreate}>
          + Tạo kịch bản mới
        </button>
      </div>

      {showForm && (
        <Card style={{ border: '1px solid var(--accent-blue)', boxShadow: '0 0 20px rgba(0,209,255,0.1)' }}>
          <SectionTitle>{editName ? `✏️ Sửa: ${editName}` : '➕ Tạo kịch bản mới'}</SectionTitle>

          <InputRow label="Tên kịch bản">
            <input style={{ ...inputStyle, flex: 1 }} placeholder="VD: Bật quạt khi nóng"
              value={draft.name} onChange={e => setDraft(p => ({ ...p, name: e.target.value }))} />
          </InputRow>

          <div style={{ background: 'var(--bg-card-inner)', borderRadius: '10px', padding: '16px', marginBottom: '16px' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-blue)', marginBottom: '12px' }}>🔍 Điều kiện kích hoạt</div>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Nếu</span>
              <select style={selectStyle} value={draft.condition.sensor}
                onChange={e => setDraft(p => ({ ...p, condition: { ...p.condition, sensor: e.target.value } }))}>
                {SENSOR_OPTS.map(s => <option key={s} value={s}>{SENSOR_LABEL[s]}</option>)}
              </select>
              <select style={selectStyle} value={draft.condition.op}
                onChange={e => setDraft(p => ({ ...p, condition: { ...p.condition, op: e.target.value } }))}>
                {OP_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
              <input type="number" style={{ ...inputStyle, width: '90px' }}
                value={draft.condition.value}
                onChange={e => setDraft(p => ({ ...p, condition: { ...p.condition, value: e.target.value } }))} />
            </div>
          </div>

          <div style={{ background: 'var(--bg-card-inner)', borderRadius: '10px', padding: '16px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#10b981' }}>⚡ Hành động phản hồi</span>
              <button className="btn btn-primary" style={{ padding: '4px 12px', fontSize: '0.8rem' }} onClick={addAction}>+ Thêm</button>
            </div>
            {draft.actions.map((act, i) => {
              const devId   = parseInt(act.numberdevice);
              const isLight = devId >= 1 && devId <= 5;
              const isServo = devId === 6;
              const isFan   = devId === 7;
              return (
                <div key={i} style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>→ Thiết bị</span>
                  <select style={selectStyle} value={act.numberdevice}
                    onChange={e => {
                      const newId = parseInt(e.target.value);
                      const def   = newId >= 1 && newId <= 5 ? true : 0;
                      setAction(i, 'numberdevice', e.target.value);
                      setAction(i, 'status', def);
                    }}>
                    {DEVICE_OPTS.map(d => <option key={d.id} value={d.id}>{d.label}</option>)}
                  </select>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Trạng thái</span>
                  {isLight && (
                    <select style={{ ...selectStyle, width: '130px' }} value={String(act.status)}
                      onChange={e => setAction(i, 'status', e.target.value === 'true')}>
                      <option value="true">✅ Bật (true)</option>
                      <option value="false">⭕ Tắt (false)</option>
                    </select>
                  )}
                  {isServo && (
                    <select style={{ ...selectStyle, width: '130px' }} value={String(act.status)}
                      onChange={e => setAction(i, 'status', parseFloat(e.target.value))}>
                      <option value="90">🔓 Mở (90°)</option>
                      <option value="0">🔒 Đóng (0°)</option>
                    </select>
                  )}
                  {isFan && (
                    <select
                      style={{ ...selectStyle, width: '130px' }}
                      value={act.status}
                      onChange={e => setAction(i, 'status', parseFloat(e.target.value))}
                    >
                      {FAN_LEVELS.map(level => (
                        <option key={level} value={level}>Mức {level}%</option>
                      ))}
                    </select>
                  )} 
                  {draft.actions.length > 1 && (
                    <button className="btn btn-danger" style={{ padding: '4px 10px', fontSize: '0.8rem' }} onClick={() => removeAction(i)}>✕</button>
                  )}
                </div>
              );
            })}
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
              💡 Đèn: Bật/Tắt &nbsp;|&nbsp; Servo: Mở/Đóng &nbsp;|&nbsp; Quạt: 0–100%
            </p>
          </div>

          <InputRow label="Kích hoạt">
            <label className="toggle-switch">
              <input type="checkbox" checked={draft.enabled}
                onChange={e => setDraft(p => ({ ...p, enabled: e.target.checked }))} />
              <span className="slider"></span>
            </label>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              {draft.enabled ? 'Bật ngay' : 'Tạm tắt'}
            </span>
          </InputRow>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
            <button className="btn btn-danger" onClick={() => setShowForm(false)}>Hủy</button>
            <button className="btn btn-success" disabled={saving} onClick={handleSave}>
              {saving ? 'Đang lưu...' : '💾 Lưu kịch bản'}
            </button>
          </div>
        </Card>
      )}

      {rules.length === 0 && !showForm && (
        <Card>
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '30px' }}>
            Chưa có kịch bản nào. Nhấn "+ Tạo kịch bản mới" để bắt đầu.
          </p>
        </Card>
      )}

      {rules.map(rule => {
        const cond    = rule.condition;
        const opLabel = OP_OPTS.find(o => o.value === cond?.op)?.label || cond?.op;
        return (
          <Card key={rule._id}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 600, fontSize: '1rem' }}>{rule.name}</span>
                  <StatusBadge ok={rule.enabled} label={rule.enabled ? 'Đang bật' : 'Tắt'} />
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  🔍 Nếu <strong style={{color:'var(--text-primary)'}}>{SENSOR_LABEL[cond?.sensor]}</strong>{' '}
                  <strong style={{color:'var(--accent-blue)'}}>{opLabel}</strong>{' '}
                  <strong style={{color:'var(--accent-orange)'}}>{cond?.value}</strong>
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  ⚡ {rule.actions?.map(a => {
                    const devLabel = DEVICE_OPTS.find(d => d.id === a.numberdevice)?.label || `Thiết bị ${a.numberdevice}`;
                    return `${devLabel} → ${fmtDeviceVal(a.status)}`;
                  }).join(', ')}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexShrink: 0 }}>
                <label className="toggle-switch">
                  <input type="checkbox" checked={rule.enabled} onChange={() => handleToggle(rule)} />
                  <span className="slider"></span>
                </label>
                <button className="btn btn-primary" style={{ padding: '6px 14px' }} onClick={() => openEdit(rule)}>Sửa</button>
                <button className="btn btn-danger"  style={{ padding: '6px 12px' }} onClick={() => handleDelete(rule.name)}>🗑</button>
              </div>
            </div>
          </Card>
        );
      })}
    </>
  );
}

// ── Main AlertTab ──────────────────────────────────────────────
const TABS = [
  { key: 'monitor',   label: 'Giám sát ngưỡng' },
  { key: 'threshold', label: 'Cấu hình ngưỡng' },
  { key: 'channel',   label: 'Kênh thông báo' },
  { key: 'rules',     label: 'Kịch bản tự động' },
];

export default function AlertTab({ addToast }) {
  const [sub, setSub] = useState('monitor');
  return (
    <div>
      <TabBar tabs={TABS} active={sub} onChange={setSub} />
      {sub === 'monitor'   && <MonitorTab   addToast={addToast} />}
      {sub === 'threshold' && <ThresholdTab addToast={addToast} />}
      {sub === 'channel'   && <ChannelTab   addToast={addToast} />}
      {sub === 'rules'     && <AutoRuleTab  addToast={addToast} />}
    </div>
  );
}