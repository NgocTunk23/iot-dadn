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
  
  // --- STATE CHO DRAG & DROP ---
  const [draftMode, setDraftMode] = useState(null);
  const [availableDevices, setAvailableDevices] = useState([]);
  const [selectedDevices, setSelectedDevices] = useState([]);

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

  // --- Load danh sách modes từ BE khi mount ---
  useEffect(() => {
    const loadModes = async () => {
      try {
        const res = await axios.get(`${API_BASE}/scenes`);
        if (Array.isArray(res.data)) {
          const loaded = res.data.map(m => ({
            id: m.modeid || m._id,
            name: m.name || 'Không tên',
            active: m.isactive || false,
            action: m.action || []
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
    loadModes();
  }, []);

  // --- LOGIC DRAG & DROP ---

  const ALL_DEVICE_KEYS = [
    { key: 'light1', label: 'Đèn 1', type: 'switch', id: 1 },
    { key: 'light2', label: 'Đèn 2', type: 'switch', id: 2 },
    { key: 'light3', label: 'Đèn 3', type: 'switch', id: 3 },
    { key: 'light4', label: 'Đèn 4', type: 'switch', id: 4 },
    { key: 'light5', label: 'Đèn 5', type: 'switch', id: 5 },
    { key: 'servo', label: 'Cửa (Servo)', type: 'servo', id: 6 },
    { key: 'fan', label: 'Quạt', type: 'fan', id: 7 },
  ];

  const startCreateMode = () => {
    setDraftMode({ name: '', isactive: false });
    setAvailableDevices([...ALL_DEVICE_KEYS]);
    setSelectedDevices([]);
  };

  const startEditMode = (mode) => {
    setDraftMode({ ...mode });
    const selectedIds = mode.action.map(a => a.numberdevice);
    setSelectedDevices(ALL_DEVICE_KEYS.filter(d => selectedIds.includes(d.id)).map(d => {
      const act = mode.action.find(a => a.numberdevice === d.id);
      let value = act.status;
      // Convert value to internal FE state format
      let state = value;
      if (d.key === 'servo') state = value >= 45 ? 'open' : 'close';
      if (d.key === 'fan') state = PERCENT_TO_FAN_LEVEL[value] || 0;
      if (d.key.startsWith('light')) state = { state: !!value, brightness: 50 };
      
      return { ...d, state };
    }));
    setAvailableDevices(ALL_DEVICE_KEYS.filter(d => !selectedIds.includes(d.id)));
  };

  const cancelEditMode = () => {
    setDraftMode(null);
  };

  const saveMode = async () => {
    if (!draftMode || !draftMode.name.trim()) {
      if (addToast) addToast('Vui lòng nhập tên chế độ!', 'error');
      return;
    }

    if (selectedDevices.length === 0) {
      if (addToast) addToast('Vui lòng chọn ít nhất một thiết bị!', 'error');
      return;
    }

    // Chuyển đổi selectedDevices sang mảng action cho Backend
    const action = selectedDevices.map(d => {
      let status = d.state;
      if (d.key === 'servo') status = d.state === 'open' ? 90 : 0;
      if (d.key === 'fan') status = FAN_LEVEL_TO_PERCENT[d.state] || 0;
      if (d.key.startsWith('light')) status = d.state.state;
      
      return { numberdevice: d.id, status };
    });

    try {
      await axios.post(`${API_BASE}/scenes`, {
        name: draftMode.name.trim(),
        action,
        isactive: false
      });

      // Reload danh sách
      const res = await axios.get(`${API_BASE}/scenes`);
      setModes(res.data.map(m => ({
        id: m.modeid || m._id,
        name: m.name || 'Không tên',
        active: m.isactive || false,
        action: m.action || []
      })));

      setDraftMode(null);
      if (addToast) addToast('Đã lưu chế độ thành công!', 'success');
    } catch (err) {
      console.error('Lỗi lưu chế độ:', err);
      if (addToast) addToast('Lỗi khi lưu chế độ!', 'error');
    }
  };

  const deleteMode = async (id) => {
    const mode = modes.find(m => m.id === id);
    if (!mode) return;
    try {
      await axios.delete(`${API_BASE}/scenes`, { params: { name: mode.name } });
      setModes(prev => prev.filter(m => m.id !== id));
      if (addToast) addToast('Đã xóa chế độ!', 'info');
    } catch (err) {
      console.error('Lỗi xóa chế độ:', err);
    }
  };

  // --- KÍCH HOẠT CHẾ ĐỘ + VALIDATION TRÙNG THIẾT BỊ ---
  const toggleMode = async (id, active) => {
    const targetMode = modes.find(m => m.id === id);
    if (!targetMode) return;

    if (active) {
      // KIỂM TRA TRÙNG THIẾT BỊ (Conflict Detection)
      const targetDeviceIds = targetMode.action.map(a => a.numberdevice);
      const activeModes = modes.filter(m => m.active && m.id !== id);
      
      const conflicts = [];
      activeModes.forEach(m => {
        const mDeviceIds = m.action.map(a => a.numberdevice);
        const overlap = targetDeviceIds.filter(id => mDeviceIds.includes(id));
        if (overlap.length > 0) {
          conflicts.push(m.name);
        }
      });

      if (conflicts.length > 0) {
        if (addToast) addToast(`⚠️ Không thể bật vì thiết bị bị trùng với các chế độ: ${conflicts.join(', ')}`, 'warning');
        return;
      }

      try {
        await axios.post(`${API_BASE}/activate-scene`, { name: targetMode.name });
        setModes(prev => prev.map(m => m.id === id ? { ...m, active: true } : m));
        // Cập nhật state thiết bị cục bộ cho UI mượt
        setDeviceStates(prev => {
          let next = { ...prev };
          targetMode.action.forEach(act => {
            const beVal = act.status;
            let feVal = beVal;
            if (act.numberdevice === 6) feVal = beVal >= 45 ? 'open' : 'close';
            if (act.numberdevice === 7) feVal = PERCENT_TO_FAN_LEVEL[beVal] || 0;
            if (act.numberdevice <= 5) feVal = { state: !!beVal, brightness: 50 };
            
            const keys = ['light1', 'light2', 'light3', 'light4', 'light5', 'servo', 'fan'];
            next[keys[act.numberdevice - 1]] = feVal;
          });
          return next;
        });
      } catch (err) {
        console.error('Lỗi kích hoạt:', err);
      }
    } else {
      try {
        await axios.post(`${API_BASE}/deactivate-scene`, { name: targetMode.name });
        setModes(prev => prev.map(m => m.id === id ? { ...m, active: false } : m));
      } catch (err) {
        console.error('Lỗi tắt chế độ:', err);
      }
    }
  };

  const onDragStart = (e, device) => {
    e.dataTransfer.setData('device', JSON.stringify(device));
  };

  const onDropToSelected = (e) => {
    e.preventDefault();
    const device = JSON.parse(e.dataTransfer.getData('device'));
    if (selectedDevices.find(d => d.id === device.id)) return;

    // Khởi tạo trạng thái mặc định cho thiết bị khi được chọn vào kịch bản
    let initialState = false;
    if (device.key === 'servo') initialState = 'close';
    if (device.key === 'fan') initialState = 0;
    if (device.key.startsWith('light')) initialState = { state: false, brightness: 50 };

    setSelectedDevices(prev => [...prev, { ...device, state: initialState }]);
    setAvailableDevices(prev => prev.filter(d => d.id !== device.id));
  };

  const onDropToAvailable = (e) => {
    e.preventDefault();
    const device = JSON.parse(e.dataTransfer.getData('device'));
    if (availableDevices.find(d => d.id === device.id)) return;

    setAvailableDevices(prev => [...prev, device]);
    setSelectedDevices(prev => prev.filter(d => d.id !== device.id));
  };

  const updateDraftDevice = (id, field, value) => {
    setSelectedDevices(prev => prev.map(d => {
      if (d.id === id) {
        return {
          ...d,
          state: field ? { ...d.state, [field]: value } : value
        };
      }
      return d;
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
    availableDevices,
    selectedDevices,
    onDragStart,
    onDropToSelected,
    onDropToAvailable,
    updateDraftDevice
  };
}
