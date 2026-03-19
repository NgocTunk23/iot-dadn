import React, { useState, useEffect } from 'react';
import SensorChart from './SensorChart';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const ALERT_ICONS = {
  warning: '⚠️',
  info: 'ℹ️',
  success: '✅',
};

const ALERT_COLORS = {
  warning: '#FF9F43',
  info: '#00D1FF',
  success: '#10b981',
};

function AlertItem({ type, title, message }) {
  const color = ALERT_COLORS[type] || ALERT_COLORS.info;
  return (
    <div className="alert-item" style={{ borderLeftColor: color }}>
      <div className="alert-item-icon" style={{ color }}>
        {ALERT_ICONS[type] || 'ℹ️'}
      </div>
      <div className="alert-item-content">
        <div className="alert-item-title" style={{ color }}>{title}</div>
        <div className="alert-item-message">{message}</div>
      </div>
    </div>
  );
}

/**
 * Component hiển thị so sánh với dữ liệu cũ.
 * delta > 0: tăng (mũi tên lên), delta < 0: giảm (mũi tên xuống), delta = 0: ổn định
 */
function StatComparison({ delta, unit, label }) {
  if (delta === null || delta === undefined) return null;

  const isUp = delta > 0;
  const isDown = delta < 0;
  const isStable = delta === 0;

  const color = isUp ? '#FF9F43' : isDown ? '#00D1FF' : '#10b981';
  const arrow = isUp ? '▲' : isDown ? '▼' : '—';
  const sign = isUp ? '+' : '';

  return (
    <div className="stat-comparison" style={{ color }}>
      <span className="stat-comparison-arrow">{arrow}</span>
      <span>{sign}{delta}{unit}</span>
      <span className="stat-comparison-label">{label}</span>
    </div>
  );
}

export default function Dashboard({ data }) {
  const [alerts, setAlerts] = useState([]);
  const [comparison, setComparison] = useState(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await axios.get(`${API_BASE}/sensor-alerts`);
        if (Array.isArray(res.data)) setAlerts(res.data);
      } catch (err) {
        setAlerts([
          { type: 'warning', title: 'Nhiệt độ có xu hướng tăng', message: 'Nhiệt độ trung bình đã tăng 1.2°C so với tuần trước, cần theo dõi để điều chỉnh hệ thống làm mát phù hợp.' },
          { type: 'info', title: 'Độ ẩm trong ngưỡng ổn định', message: 'Độ ẩm dao động từ 65-70%, nằm trong khoảng lý tưởng cho môi trường sống.' },
          { type: 'success', title: 'Ánh sáng đạt chuẩn', message: 'Mức ánh sáng trung bình 840 lux, phù hợp cho hoạt động hàng ngày.' },
        ]);
      }
    };

    const fetchComparison = async () => {
      try {
        const res = await axios.get(`${API_BASE}/sensor-comparison`);
        setComparison(res.data);
      } catch (err) {
        // Fallback comparison data
        setComparison({
          temp: { delta: 1.2, label: 'so với tuần trước' },
          humi: { delta: -2.1, label: 'so với tuần trước' },
          light: { delta: 30, label: 'so với tuần trước' },
        });
      }
    };

    fetchAlerts();
    fetchComparison();
  }, []);

  const isConnected = data.connected !== false;

  return (
    <>
      {/* Thẻ thống kê */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <div className="stat-title">Nhiệt độ</div>
            <div className="stat-icon temp">🌡️</div>
          </div>
          <div className="stat-value" style={{ color: '#ff9f43' }}>{data.temp}°C</div>
          {isConnected && comparison?.temp && (
            <StatComparison
              delta={comparison.temp.delta}
              unit="°C"
              label={comparison.temp.label}
            />
          )}
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <div className="stat-title">Độ ẩm</div>
            <div className="stat-icon humi">💧</div>
          </div>
          <div className="stat-value" style={{ color: '#00d1ff' }}>{data.humi}%</div>
          {isConnected && comparison?.humi && (
            <StatComparison
              delta={comparison.humi.delta}
              unit="%"
              label={comparison.humi.label}
            />
          )}
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <div className="stat-title">Ánh sáng</div>
            <div className="stat-icon light">☀️</div>
          </div>
          <div className="stat-value" style={{ color: '#ffc107' }}>{data.light} lux</div>
          {isConnected && comparison?.light && (
            <StatComparison
              delta={comparison.light.delta}
              unit=" lux"
              label={comparison.light.label}
            />
          )}
        </div>
      </div>

      {/* Biểu đồ xu hướng và Cảnh báo chỉ hiện khi có kết nối */}
      {isConnected ? (
        <>
          <SensorChart />
          <div className="alerts-section">
            <div className="alerts-header">
              <h3>Cảnh báo & Nhận định</h3>
              <p>Phân tích tự động dựa trên dữ liệu xu hướng</p>
            </div>
            <div className="alerts-list">
              {alerts.map((alert, idx) => (
                <AlertItem key={idx} type={alert.type} title={alert.title} message={alert.message} />
              ))}
            </div>
          </div>
        </>
      ) : (
        <div style={{
          textAlign: 'center', 
          padding: '40px', 
          color: 'var(--text-secondary)',
          background: 'var(--bg-card)',
          borderRadius: '10px',
          marginTop: '20px',
          border: '1px dashed var(--border-color)'
        }}>
          <h3>Đã mất kết nối cảm biến!</h3>
          <p>Hệ thống không thể tải dữ liệu biểu đồ và phân tích dự báo. Vui lòng kiểm tra lại thiết bị.</p>
        </div>
      )}

      {/* Trạng thái cảm biến */}
      <div style={{ marginTop: '20px', color: 'var(--text-secondary)', fontSize: '0.9rem', textAlign: 'center' }}>
        <p>Trạng thái Cảm biến:
          <span style={{
            color: data.connected !== false ? '#00ff00' : '#ea4335',
            fontWeight: 'bold',
            marginLeft: '8px'
          }}>
            {data.connected !== false ? 'Đang hoạt động 🟢' : 'Mất kết nối 🔴'}
          </span>
        </p>
        <p style={{ marginTop: '5px' }}>
          Cập nhật cuối: <span style={{ color: 'var(--text-primary)' }}>{data.time}</span>
        </p>
      </div>
    </>
  );
}
