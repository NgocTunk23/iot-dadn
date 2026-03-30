import React, { useState, useEffect, useRef } from 'react';
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import axios from 'axios';

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend, Filler);

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

/* ======================== SVG ICONS ======================== */
const TempIcon = () => (
  <svg className="stat-svg-icon stat-svg-icon--temp" viewBox="0 0 40 58" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="12" y="2" width="16" height="38" rx="8" stroke="url(#tempGrad)" strokeWidth="2.5"/>
    <circle cx="20" cy="46" r="10" stroke="url(#tempGrad)" strokeWidth="2.5"/>
    <rect className="thermo-fill" x="17" y="14" width="6" height="28" rx="3" fill="url(#tempGrad)"/>
    <circle cx="20" cy="46" r="6" fill="url(#tempGrad)"/>
    <defs>
      <linearGradient id="tempGrad" x1="20" y1="0" x2="20" y2="58" gradientUnits="userSpaceOnUse">
        <stop stopColor="#FF9F43"/><stop offset="1" stopColor="#FF6B6B"/>
      </linearGradient>
    </defs>
  </svg>
);

const HumiIcon = () => (
  <svg className="stat-svg-icon stat-svg-icon--humi" viewBox="0 0 44 58" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M22 4C22 4 6 24 6 36C6 44.837 13.163 52 22 52C30.837 52 38 44.837 38 36C38 24 22 4 22 4Z"
      stroke="url(#humiGrad)" strokeWidth="2.5" fill="url(#humiFill)" />
    <ellipse className="humi-shine" cx="16" cy="34" rx="5" ry="8" fill="rgba(255,255,255,0.15)" />
    <defs>
      <linearGradient id="humiGrad" x1="22" y1="4" x2="22" y2="52" gradientUnits="userSpaceOnUse">
        <stop stopColor="#00D1FF"/><stop offset="1" stopColor="#0077FF"/>
      </linearGradient>
      <linearGradient id="humiFill" x1="22" y1="4" x2="22" y2="52" gradientUnits="userSpaceOnUse">
        <stop stopColor="rgba(0,209,255,0.1)"/><stop offset="1" stopColor="rgba(0,119,255,0.2)"/>
      </linearGradient>
    </defs>
  </svg>
);

const LightIcon = () => (
  <svg className="stat-svg-icon stat-svg-icon--light" viewBox="0 0 58 58" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="29" cy="29" r="12" stroke="url(#lightGrad)" strokeWidth="2.5" fill="rgba(255,193,7,0.12)"/>
    <circle className="light-glow-ring" cx="29" cy="29" r="18" stroke="url(#lightGrad)" strokeWidth="1" opacity="0.4"/>
    {[0,45,90,135,180,225,270,315].map((angle, i) => {
      const rad = (angle * Math.PI) / 180;
      const x1 = 29 + 22 * Math.cos(rad);
      const y1 = 29 + 22 * Math.sin(rad);
      const x2 = 29 + 27 * Math.cos(rad);
      const y2 = 29 + 27 * Math.sin(rad);
      return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="url(#lightGrad)" strokeWidth="2" strokeLinecap="round"/>;
    })}
    <defs>
      <linearGradient id="lightGrad" x1="29" y1="0" x2="29" y2="58" gradientUnits="userSpaceOnUse">
        <stop stopColor="#FFC107"/><stop offset="1" stopColor="#FF9F43"/>
      </linearGradient>
    </defs>
  </svg>
);

/* ======================== SUB-COMPONENTS ======================== */
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

function StatComparison({ delta, unit, label }) {
  if (delta === null || delta === undefined) return null;
  const isUp = delta > 0;
  const isDown = delta < 0;
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

/* ======================== TREND CHART ======================== */
function TrendChart({ title, subtitle, data, gradientColors, unit, suggestedMin, suggestedMax }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    // 1. Kiểm tra data hợp lệ
    if (!data || data.length === 0) return;
    
    // 2. CHÚ Ý: Kiểm tra canvas đã được mount vào DOM chưa
    if (!canvasRef.current) return; 

    if (!chartRef.current) {
      const ctx = canvasRef.current.getContext('2d');

      // Line gradient (left to right)
      const lineGrad = ctx.createLinearGradient(0, 0, ctx.canvas.width, 0);
      lineGrad.addColorStop(0, gradientColors[0]);
      lineGrad.addColorStop(1, gradientColors[1]);

      // Fill gradient (top to bottom, transparent)
      const fillGrad = ctx.createLinearGradient(0, 0, 0, 240);
      fillGrad.addColorStop(0, gradientColors[0].replace(')', ', 0.25)').replace('rgb', 'rgba'));
      fillGrad.addColorStop(1, gradientColors[1].replace(')', ', 0.02)').replace('rgb', 'rgba'));

      chartRef.current = new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.map(d => d.label), // LƯU Ý BƯỚC 3 BÊN DƯỚI
          datasets: [{
            label: title,
            data: data.map(d => d.value),
            borderColor: lineGrad,
            backgroundColor: fillGrad,
            fill: true,
            tension: 0.4,
            pointRadius: 5,
            pointBackgroundColor: gradientColors[1],
            pointBorderColor: gradientColors[0],
            pointHoverRadius: 8,
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: gradientColors[1],
            pointHoverBorderWidth: 3,
            borderWidth: 3,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false, // YÊU CẦU CSS CỦA THẺ CHA PHẢI CÓ HEIGHT
          animation: { duration: 600, easing: 'easeInOutQuart' },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: 'rgba(13, 17, 23, 0.95)',
              titleColor: '#fff',
              bodyColor: gradientColors[1],
              bodyFont: { size: 14, weight: 'bold' },
              titleFont: { size: 13 },
              padding: 12,
              cornerRadius: 8,
              displayColors: false,
              callbacks: {
                title: (items) => `${items[0].label} phút trước`,
                label: (item) => `${item.raw}${unit ? ' ' + unit : ''}`,
              },
            },
          },
          scales: {
            x: {
              title: {
                display: true,
                text: 'Thời gian (Phút trước)',
                color: '#8B949E',
                font: { size: 11, family: 'Inter, sans-serif', weight: '500' }
              },
              ticks: { color: '#8B949E', font: { size: 12, family: 'Inter, sans-serif' } },
              grid: { color: 'rgba(48, 54, 61, 0.3)', drawBorder: false },
            },
            y: {
              title: {
                display: true,
                text: `Đơn vị (${unit})`,
                color: '#8B949E',
                font: { size: 11, family: 'Inter, sans-serif', weight: '500' }
              },
              suggestedMin,
              suggestedMax,
              ticks: { 
                color: '#8B949E', 
                font: { size: 11, family: 'Inter, sans-serif' },
              },
              grid: { color: 'rgba(48, 54, 61, 0.3)', drawBorder: false },
            },
          },
          interaction: { mode: 'index', intersect: false },
        }
      });
    } else {
      // Cập nhật data
      chartRef.current.data.labels = data.map(d => d.label);
      chartRef.current.data.datasets[0].data = data.map(d => d.value);
      chartRef.current.update();
    }
  }, [data, gradientColors, title, unit, suggestedMin, suggestedMax]);

  useEffect(() => {
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, []);

  return (
    <div className="trend-chart-card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="trend-chart-header">
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      {/* Sửa lại CSS nội tuyến ở đây để ép cứng chiều cao nếu bạn chưa viết trong file CSS */}
      <div className="trend-chart-body" style={{ position: 'relative', height: '250px', width: '100%' }}>
        <canvas ref={canvasRef}></canvas>
      </div>
    </div>
  );
}

/* ======================== MAIN DASHBOARD ======================== */
export default function Dashboard({ data }) {
  const [alerts, setAlerts] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [trendData, setTrendData] = useState(null);

  // Fetch alerts & comparison once
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await axios.get(`${API_BASE}/sensor-alerts`);
        if (Array.isArray(res.data)) setAlerts(res.data);
      } catch {
        setAlerts([
          { type: 'warning', title: 'Nhiệt độ có xu hướng tăng', message: 'Nhiệt độ trung bình đã tăng 1.2°C so với tuần trước.' },
          { type: 'info', title: 'Độ ẩm trong ngưỡng ổn định', message: 'Độ ẩm dao động từ 65-70%.' },
          { type: 'success', title: 'Ánh sáng đạt chuẩn', message: 'Mức ánh sáng trung bình 840 lux.' },
        ]);
      }
    };
    fetchAlerts();
  }, []);

  // Poll comparison every 5 seconds
  useEffect(() => {
    const fetchComparison = async () => {
      try {
        const res = await axios.get(`${API_BASE}/sensor-comparison`);
        setComparison(res.data);
      } catch {
        setComparison({
          temp: { delta: 1.2, label: 'So với trung bình ngày' },
          humi: { delta: -2.1, label: 'So với trung bình ngày' },
          light: { delta: 30, label: 'So với trung bình ngày' },
        });
      }
    };
    fetchComparison();
    const timer = setInterval(fetchComparison, 5000);
    return () => clearInterval(timer);
  }, []);

  // Poll realtime trend every 5 seconds
  useEffect(() => {
    const fetchTrend = async () => {
      try {
        const res = await axios.get(`${API_BASE}/realtime-trend`);
        setTrendData(res.data);
      } catch {
        console.error('Lỗi tải dữ liệu xu hướng realtime');
      }
    };
    fetchTrend();
    const timer = setInterval(fetchTrend, 5000);
    return () => clearInterval(timer);
  }, []);

  const isConnected = data.connected !== false;

  return (
    <>
      {/* Thẻ thống kê */}
      <div className="stats-grid">
        <div className="stat-card stat-card--temp">
          <div className="stat-header">
            <div className="stat-title">Nhiệt độ</div>
            <div className="stat-icon-wrap">
              <TempIcon />
            </div>
          </div>
          <div className="stat-value" style={{ color: '#ff9f43' }}>{data.temp}°C</div>
          {isConnected && comparison?.temp && (
            <StatComparison delta={comparison.temp.delta} unit="°C" label={comparison.temp.label} />
          )}
        </div>

        <div className="stat-card stat-card--humi">
          <div className="stat-header">
            <div className="stat-title">Độ ẩm</div>
            <div className="stat-icon-wrap">
              <HumiIcon />
            </div>
          </div>
          <div className="stat-value" style={{ color: '#00d1ff' }}>{data.humi}%</div>
          {isConnected && comparison?.humi && (
            <StatComparison delta={comparison.humi.delta} unit="%" label={comparison.humi.label} />
          )}
        </div>

        <div className="stat-card stat-card--light">
          <div className="stat-header">
            <div className="stat-title">Ánh sáng</div>
            <div className="stat-icon-wrap">
              <LightIcon />
            </div>
          </div>
          <div className="stat-value" style={{ color: '#ffc107' }}>{data.light} % </div>
          {isConnected && comparison?.light && (
            <StatComparison delta={comparison.light.delta} unit=" %" label={comparison.light.label} />
          )}
        </div>
      </div>

      {/* Biểu đồ xu hướng realtime & Cảnh báo */}
      {isConnected ? (
        <>
          {trendData && (
            <div className="trend-charts-grid">
              <TrendChart
                title="Xu hướng nhiệt độ"
                subtitle="Dữ liệu 30 phút gần nhất"
                data={trendData.temp}
                gradientColors={['rgb(255, 159, 67)', 'rgb(255, 107, 107)']}
                unit="°C"
                suggestedMin={0}
                suggestedMax={50}
              />
              <TrendChart
                title="Xu hướng độ ẩm"
                subtitle="Dữ liệu 30 phút gần nhất"
                data={trendData.humi}
                gradientColors={['rgb(0, 209, 255)', 'rgb(0, 119, 255)']}
                unit="%"
                suggestedMin={0}
                suggestedMax={100}
              />
              <TrendChart
                title="Xu hướng ánh sáng"
                subtitle="Dữ liệu 30 phút gần nhất"
                data={trendData.light}
                gradientColors={['rgb(255, 193, 7)', 'rgb(255, 159, 67)']}
                unit="%"
                suggestedMin={0}
                suggestedMax={100}
              />
            </div>
          )}


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
