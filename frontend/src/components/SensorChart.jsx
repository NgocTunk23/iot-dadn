import React, { useEffect, useRef, useState } from 'react';
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

// Các chu kỳ theo dõi
const PERIODS = [
  { key: 'week', label: 'Tuần' },
  { key: 'month', label: 'Tháng' },
  { key: 'year', label: 'Năm' },
];

/**
 * Tạo 1 biểu đồ xu hướng riêng biệt.
 */
function TrendChart({ title, subtitle, data, color, unit }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!data || data.length === 0) return;

    if (chartRef.current) chartRef.current.destroy();

    const ctx = canvasRef.current.getContext('2d');

    // Tạo gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, 220);
    gradient.addColorStop(0, color.replace(')', ', 0.25)').replace('rgb', 'rgba'));
    gradient.addColorStop(1, color.replace(')', ', 0.02)').replace('rgb', 'rgba'));

    chartRef.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map(d => d.day),
        datasets: [{
          label: title,
          data: data.map(d => d.value),
          borderColor: color,
          backgroundColor: gradient,
          fill: true,
          tension: 0.4,
          pointRadius: 5,
          pointBackgroundColor: color,
          pointBorderColor: color,
          pointHoverRadius: 7,
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: color,
          pointHoverBorderWidth: 3,
          borderWidth: 2.5,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(13, 17, 23, 0.95)',
            titleColor: '#fff',
            bodyColor: color,
            bodyFont: { size: 14, weight: 'bold' },
            titleFont: { size: 13 },
            padding: 12,
            cornerRadius: 8,
            displayColors: false,
            callbacks: {
              title: (items) => items[0].label,
              label: (item) => `value : ${item.raw}${unit ? ' ' + unit : ''}`,
            },
          },
        },
        scales: {
          x: {
            ticks: { color: '#8B949E', font: { size: 12 } },
            grid: { color: 'rgba(48, 54, 61, 0.3)', drawBorder: false },
          },
          y: {
            ticks: { color: '#8B949E', font: { size: 11 } },
            grid: { color: 'rgba(48, 54, 61, 0.3)', drawBorder: false },
            beginAtZero: true,
          },
        },
        interaction: { mode: 'index', intersect: false },
      },
    });

    return () => {
      if (chartRef.current) chartRef.current.destroy();
    };
  }, [data, color, title, unit]);

  return (
    <div className="trend-chart-card">
      <div className="trend-chart-header">
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <div className="trend-chart-body">
        <canvas ref={canvasRef}></canvas>
      </div>
    </div>
  );
}

// Subtitle tương ứng theo chu kỳ
const SUBTITLES = {
  week: 'trung bình trong tuần',
  month: 'trung bình trong tháng',
  year: 'trung bình trong năm',
};

/**
 * Container cho 3 biểu đồ xu hướng + bộ chọn chu kỳ.
 */
export default function SensorChart() {
  const [trendData, setTrendData] = useState(null);
  const [period, setPeriod] = useState('week');

  useEffect(() => {
    const fetchTrend = async () => {
      try {
        const res = await axios.get(`${API_BASE}/weekly-trend`, { params: { period } });
        setTrendData(res.data);
      } catch (err) {
        console.error('Lỗi tải dữ liệu xu hướng:', err);
        // Dữ liệu fallback
        if (period === 'month') {
          setTrendData({
            temp: [1, 2, 3, 4].map(i => ({ day: `Tuần ${i}`, value: 28.0 + Math.random() })),
            humi: [1, 2, 3, 4].map(i => ({ day: `Tuần ${i}`, value: 65.0 + Math.random() * 5 })),
            light: [1, 2, 3, 4].map(i => ({ day: `Tuần ${i}`, value: 800 + Math.floor(Math.random() * 100) })),
          });
        } else if (period === 'year') {
          setTrendData({
            temp: Array.from({ length: 12 }, (_, i) => ({ day: `Tháng ${i+1}`, value: 27.0 + Math.random() * 5 })),
            humi: Array.from({ length: 12 }, (_, i) => ({ day: `Tháng ${i+1}`, value: 60.0 + Math.random() * 10 })),
            light: Array.from({ length: 12 }, (_, i) => ({ day: `Tháng ${i+1}`, value: 750 + Math.floor(Math.random() * 200) })),
          });
        } else {
          setTrendData({
            temp: [
              { day: 'T2', value: 28.0 }, { day: 'T3', value: 28.5 },
              { day: 'T4', value: 29.0 }, { day: 'T5', value: 28.8 },
              { day: 'T6', value: 28.2 }, { day: 'T7', value: 27.5 },
              { day: 'CN', value: 27.8 },
            ],
            humi: [
              { day: 'T2', value: 65 }, { day: 'T3', value: 68 },
              { day: 'T4', value: 67 }, { day: 'T5', value: 69 },
              { day: 'T6', value: 71 }, { day: 'T7', value: 66 },
              { day: 'CN', value: 65.5 },
            ],
            light: [
              { day: 'T2', value: 810 }, { day: 'T3', value: 860 },
              { day: 'T4', value: 850 }, { day: 'T5', value: 880 },
              { day: 'T6', value: 870 }, { day: 'T7', value: 840 },
              { day: 'CN', value: 820 },
            ],
          });
        }
      }
    };

    fetchTrend();
  }, [period]);

  if (!trendData) return null;

  const sub = SUBTITLES[period] || SUBTITLES.week;

  return (
    <>
      {/* Bộ chọn chu kỳ theo dõi */}
      <div className="period-selector">
        <span className="period-label">Chu kỳ theo dõi:</span>
        <div className="period-buttons">
          {PERIODS.map(p => (
            <button
              key={p.key}
              className={`period-btn ${period === p.key ? 'active' : ''}`}
              onClick={() => setPeriod(p.key)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="trend-charts-grid">
        <TrendChart
          title="Xu hướng nhiệt độ"
          subtitle={`Nhiệt độ ${sub}`}
          data={trendData.temp}
          color="rgb(255, 159, 67)"
          unit="°C"
        />
        <TrendChart
          title="Xu hướng độ ẩm"
          subtitle={`Độ ẩm ${sub}`}
          data={trendData.humi}
          color="rgb(0, 209, 255)"
          unit="%"
        />
        <TrendChart
          title="Xu hướng ánh sáng"
          subtitle={`Ánh sáng ${sub}`}
          data={trendData.light}
          color="rgb(255, 193, 7)"
          unit="lux"
        />
      </div>
    </>
  );
}
