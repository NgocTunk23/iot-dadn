import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const DEFAULT_DEVICE_STATES = {
  light1: { state: false, brightness: 50 },
  light2: { state: false, brightness: 50 },
  light3: { state: false, brightness: 50 },
  light4: { state: false, brightness: 50 },
  light5: { state: false, brightness: 50 },
  servo: 'close', // 'open' | 'close'
  fan: 0, // 0..4
};

// ===== CHUYỂN ĐỔI FE ↔ BE =====

const FAN_LEVEL_TO_PERCENT = { 0: 0, 1: 70, 2: 80, 3: 90, 4: 100 };
const PERCENT_TO_FAN_LEVEL = { 0: 0, 70: 1, 80: 2, 90: 3, 100: 4 };

function feStateToBECommands(feState) {
  return [
    [1, feState.light1.state],
    [2, feState.light2.state],
    [3, feState.light3.state],
    [4, feState.light4.state],
    [5, feState.light5.state],
    [6, feState.servo === 'open' ? 90 : 0],
    [7, FAN_LEVEL_TO_PERCENT[feState.fan] || 0],
  ];
}

function beStatusToFEState(beStatus) {
  const map = {};
  for (const [id, val] of beStatus) {
    map[id] = val;
  }
  return {
    light1: { state: !!map[1], brightness: 50 },
    light2: { state: !!map[2], brightness: 50 },
    light3: { state: !!map[3], brightness: 50 },
    light4: { state: !!map[4], brightness: 50 },
    light5: { state: !!map[5], brightness: 50 },
    servo: (map[6] && map[6] >= 45) ? 'open' : 'close',
    fan: PERCENT_TO_FAN_LEVEL[map[7]] !== undefined ? PERCENT_TO_FAN_LEVEL[map[7]] : 0,
  };
}

function feStateToSceneActions(feState) {
  return [
    { device_id: 1, value: feState.light1.state },
    { device_id: 2, value: feState.light2.state },
    { device_id: 3, value: feState.light3.state },
    { device_id: 4, value: feState.light4.state },
    { device_id: 5, value: feState.light5.state },
    { device_id: 6, value: feState.servo === 'open' ? 90 : 0 },
    { device_id: 7, value: FAN_LEVEL_TO_PERCENT[feState.fan] || 0 },
  ];
}

function sceneActionsToFEState(actions) {
  const map = {};
  for (const act of actions) {
    map[act.device_id] = act.value;
  }
  return {
    light1: { state: !!map[1], brightness: 50 },
    light2: { state: !!map[2], brightness: 50 },
    light3: { state: !!map[3], brightness: 50 },
    light4: { state: !!map[4], brightness: 50 },
    light5: { state: !!map[5], brightness: 50 },
    servo: (map[6] && map[6] >= 45) ? 'open' : 'close',
    fan: PERCENT_TO_FAN_LEVEL[map[7]] !== undefined ? PERCENT_TO_FAN_LEVEL[map[7]] : 0,
  };
}

/** Đếm số thiết bị đang bật */
function countActiveDevices(devState) {
  let count = 0;
  ['light1', 'light2', 'light3', 'light4', 'light5'].forEach(k => {
    if (devState[k]?.state) count++;
  });
  if (devState.servo === 'open') count++;
  if (devState.fan > 0) count++;
  return count;
}

/** Retry wrapper: thử lại tối đa maxRetries lần */
async function withRetry(fn, maxRetries = 5, delayMs = 1000) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (attempt === maxRetries) throw err;
      console.warn(`Thử lại lần ${attempt}/${maxRetries}...`);
      await new Promise(r => setTimeout(r, delayMs));
    }
  }
}

// ===== HOOK =====

export default function useDevices(addToast) {
  const [deviceStates, setDeviceStates] = useState(DEFAULT_DEVICE_STATES);
  const [modes, setModes] = useState([]);
  const [draftMode, setDraftMode] = useState(null);
  const modesRef = useRef(modes);
  modesRef.current = modes;

  // --- Gửi lệnh điều khiển xuống BE ---
  const syncToBackend = useCallback(async (newState) => {
    try {
      const commands = feStateToBECommands(newState);
      await axios.post(`${API_BASE}/control`, { commands });
    } catch (err) {
      console.error('Lỗi gửi lệnh điều khiển:', err);
      if (addToast) addToast('Lỗi gửi lệnh điều khiển đến thiết bị!', 'error');
    }
  }, [addToast]);

  // --- Cập nhật thiết bị + đồng bộ BE ---
  const updateDevice = useCallback((key, field, value) => {
    setDeviceStates(prev => {
      const next = {
        ...prev,
        [key]: field ? { ...prev[key], [field]: value } : value,
      };
      syncToBackend(next);
      return next;
    });
  }, [syncToBackend]);

  // --- Load danh sách scenes từ BE khi mount ---
  useEffect(() => {
    const loadScenes = async () => {
      try {
        const res = await axios.get(`${API_BASE}/scenes`);
        if (Array.isArray(res.data)) {
          const loaded = res.data.map(scene => ({
            id: scene._id || scene.scene_name,
            name: scene.scene_name,
            active: false,
            triggerType: scene.trigger_type || 'manual',
            triggerTime: scene.trigger_time || '',
            devices: sceneActionsToFEState(scene.actions || []),
          }));
          setModes(loaded);
        }
      } catch (err) {
        console.error('Lỗi tải danh sách chế độ:', err);
      }
    };

    const loadDeviceStatus = async () => {
      try {
        const res = await axios.get(`${API_BASE}/sensor-data`);
        if (res.data && res.data.numberdevice) {
          const feState = beStatusToFEState(res.data.numberdevice);
          setDeviceStates(feState);
        }
      } catch (err) {
        console.error('Lỗi tải trạng thái thiết bị:', err);
      }
    };

    loadDeviceStatus();
    const timer = setInterval(loadDeviceStatus, 3000);
    return () => clearInterval(timer);
    loadScenes();
  }, []);

  // --- Tạo chế độ mới ---
  const startCreateMode = () => {
    setDraftMode({
      id: Date.now(),
      name: '',
      active: false,
      triggerType: 'manual',
      triggerTime: '',
      devices: JSON.parse(JSON.stringify(deviceStates)),
    });
  };

  const startEditMode = (mode) => {
    setDraftMode(JSON.parse(JSON.stringify(mode)));
  };

  const cancelEditMode = () => {
    setDraftMode(null);
  };

  // --- Lưu chế độ → POST /api/scenes (có validation) ---
  const saveMode = async () => {
    if (!draftMode) return;

    // UC003.2: Kiểm tra tên rỗng
    if (!draftMode.name.trim()) {
      if (addToast) addToast('Tên chế độ không được để trống!', 'error');
      return;
    }

    // Kiểm tra giờ hợp lệ nếu hẹn giờ
    if (draftMode.triggerType === 'timer' && !draftMode.triggerTime) {
      if (addToast) addToast('Vui lòng chọn thời gian hẹn giờ!', 'error');
      return;
    }

    // UC003.2: Kiểm tra trùng tên (chỉ khi tạo mới, không phải chỉnh sửa)
    const isNewMode = !modesRef.current.find(m => m.id === draftMode.id);
    if (isNewMode) {
      const duplicateName = modesRef.current.find(m => m.name.toLowerCase() === draftMode.name.trim().toLowerCase());
      if (duplicateName) {
        if (addToast) addToast(`Chế độ "${draftMode.name}" đã tồn tại! Vui lòng đổi tên khác.`, 'error');
        return;
      }
    }

    // UC003.2: Kiểm tra ít nhất 1 thiết bị phải bật
    if (countActiveDevices(draftMode.devices) === 0) {
      if (addToast) addToast('Phải bật ít nhất 1 thiết bị trong chế độ!', 'error');
      return;
    }

    try {
      const actions = feStateToSceneActions(draftMode.devices);
      await axios.post(`${API_BASE}/scenes`, {
        scene_name: draftMode.name.trim(),
        trigger_type: draftMode.triggerType,
        trigger_time: draftMode.triggerType === 'timer' ? draftMode.triggerTime : '',
        actions,
      });

      setModes(prev => {
        const existing = prev.find(m => m.name === draftMode.name || m.id === draftMode.id);
        if (existing) {
          return prev.map(m => (m.name === draftMode.name || m.id === draftMode.id) ? { ...draftMode, id: existing.id } : m);
        } else {
          return [...prev, draftMode];
        }
      });
      setDraftMode(null);
      if (addToast) addToast(`Đã lưu chế độ "${draftMode.name}" thành công!`, 'success');
    } catch (err) {
      console.error('Lỗi lưu chế độ:', err);
      if (addToast) addToast('Không thể lưu chế độ. Kiểm tra kết nối Backend.', 'error');
    }
  };

  // --- Xóa chế độ → DELETE /api/scenes ---
  const deleteMode = async (id) => {
    const mode = modesRef.current.find(m => m.id === id);
    if (!mode) return;

    try {
      await axios.delete(`${API_BASE}/scenes`, { params: { scene_name: mode.name } });
      if (addToast) addToast(`Đã xóa chế độ "${mode.name}".`, 'info');
    } catch (err) {
      console.error('Lỗi xóa chế độ:', err);
      if (addToast) addToast('Không thể xóa chế độ. Kiểm tra kết nối Backend.', 'error');
    }

    setModes(prev => prev.filter(m => m.id !== id));
    if (draftMode && draftMode.id === id) setDraftMode(null);
  };

  // --- Bật/tắt chế độ → POST /api/activate-scene (có retry UC003.3) ---
  const toggleMode = async (id, active) => {
    // Nếu active = true, bật chế độ id này và tắt tất cả các chế độ khác
    setModes(prev => prev.map(m => {
      if (m.id === id) return { ...m, active };
      if (active) return { ...m, active: false };
      return m;
    }));

    if (active) {
      const mode = modesRef.current.find(m => m.id === id);
      if (mode) {
        try {
          // UC003.3: Retry tối đa 5 lần
          await withRetry(async () => {
            await axios.post(`${API_BASE}/activate-scene`, { scene_name: mode.name });
          }, 5, 1000);

          setDeviceStates(JSON.parse(JSON.stringify(mode.devices)));
          if (addToast) addToast(`✅ Kích hoạt chế độ "${mode.name}" thành công!`, 'success');
        } catch (err) {
          console.error('Lỗi kích hoạt chế độ:', err);
          // UC003.3: Sau 5 lần thất bại → cảnh báo mất kết nối
          if (addToast) addToast(`❌ Không thể kích hoạt "${mode.name}" sau 5 lần thử. Kiểm tra kết nối!`, 'error');
          // Vẫn cập nhật FE state
          setDeviceStates(JSON.parse(JSON.stringify(mode.devices)));
        }
      }
    }
  };

  const updateDraftDevice = (key, field, value) => {
    if (!draftMode) return;
    setDraftMode(prev => ({
      ...prev,
      devices: {
        ...prev.devices,
        [key]: field ? { ...prev.devices[key], [field]: value } : value,
      },
    }));
  };

  return {
    deviceStates,
    modes,
    draftMode,
    setDraftMode,
    updateDevice,
    startCreateMode,
    startEditMode,
    cancelEditMode,
    saveMode,
    deleteMode,
    toggleMode,
    updateDraftDevice,
  };
}
