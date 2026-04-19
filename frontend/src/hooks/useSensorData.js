import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api/sensor-data';

export default function useSensorData() {
  const [data, setData] = useState({
    temp: '--', humi: '--', light: '--', time: '--', connected: true,
  });
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSensorData = async () => {
      try {
        const houseid = localStorage.getItem('houseid') || 'HS001';
        const response = await axios.get(`${API_URL}?houseid=${houseid}`);
        if (response.status === 200) {
          setData({ ...response.data, connected: response.data.connected !== false });
          setError(null);
        }
      } catch (err) {
        console.error("Lỗi kết nối Backend:", err);
        setData(prev => ({ ...prev, connected: false }));
        setError("Mất kết nối với Server");
      }
    };

    fetchSensorData();
    const timer = setInterval(fetchSensorData, 3000);
    return () => clearInterval(timer);
  }, []);

  return { data, error };
}
