import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const DEFAULT_DEVICE_STATES = {
  light1: { state: false, brightness: 50 },
  light2: { state: false, brightness: 50 },
  light3: { state: false, brightness: 50 },
  light4: { state: false, brightness: 50 },
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
    servo: map[6] === 90 ? 'open' : 'close',
    fan: PERCENT_TO_FAN_LEVEL[map[7]] !== undefined ? PERCENT_TO_FAN_LEVEL[map[7]] : 0,
  };
}

// ===== HOOK =====

export default function useDevices(addToast) {
  const [deviceStates, setDeviceStates] = useState(DEFAULT_DEVICE_STATES);
  const [modes, setModes] = useState([]);

  // --- STATE CHO 2-STEP SCENE CREATION ---
  const [draftMode, setDraftMode] = useState(null);
  const [sceneStep, setSceneStep] = useState(1); // 1 = chọn thiết bị, 2 = cấu hình
  const [checkedDeviceIds, setCheckedDeviceIds] = useState([]); // Bước 1: IDs đã check
  const [selectedDevices, setSelectedDevices] = useState([]); // Bước 2: devices + state

  const modesRef = useRef(modes);
  modesRef.current = modes;
  const lastActionTime = useRef(0);

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
    lastActionTime.current = Date.now();
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
            active: false,
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
    const timer = setInterval(loadDeviceStatus, 2000);
    return () => clearInterval(timer);
  }, []);

  // --- DANH SÁCH THIẾT BỊ CHO SCENE (loại trừ Đèn 1 - chống trộm) ---
  const SCENE_DEVICE_KEYS = [
    { key: 'light2', label: 'Đèn 2', type: 'switch', id: 2 },
    { key: 'light3', label: 'Đèn 3', type: 'switch', id: 3 },
    { key: 'light4', label: 'Đèn 4', type: 'switch', id: 4 },
    { key: 'servo', label: 'Servo (Cửa)', type: 'servo', id: 6 },
    { key: 'fan', label: 'Quạt', type: 'fan', id: 7 },
  ];

  // --- BƯỚC 1: Bắt đầu tạo kịch bản mới ---
  const startCreateMode = () => {
    setDraftMode({ name: '', isactive: false });
    setSceneStep(1);
    setCheckedDeviceIds([]);
    setSelectedDevices([]);
  };

  // --- BƯỚC 1: Toggle checkbox thiết bị ---
  const toggleDeviceCheck = (deviceId) => {
    setCheckedDeviceIds(prev => {
      if (prev.includes(deviceId)) {
        return prev.filter(id => id !== deviceId);
      }
      return [...prev, deviceId];
    });
  };

  // --- BƯỚC 1 → 2: Chuyển sang cấu hình ---
  const goToStep2 = () => {
    if (checkedDeviceIds.length === 0) {
      if (addToast) addToast('Vui lòng chọn ít nhất một thiết bị!', 'error');
      return;
    }
    // Tạo selectedDevices từ checkedDeviceIds với state mặc định
    const devices = SCENE_DEVICE_KEYS
      .filter(d => checkedDeviceIds.includes(d.id))
      .map(d => {
        let initialState = false;
        if (d.key === 'servo') initialState = 'close';
        if (d.key === 'fan') initialState = 0;
        if (d.key.startsWith('light')) initialState = { state: true, brightness: 50 };
        return { ...d, state: initialState };
      });
    setSelectedDevices(devices);
    setSceneStep(2);
  };

  // --- BƯỚC 2 ← 1: Quay lại bước chọn ---
  const goToStep1 = () => {
    setSceneStep(1);
  };

  // --- Chỉnh sửa kịch bản đã có → nhảy thẳng step 2 ---
  const startEditMode = (mode) => {
    setDraftMode({ ...mode });
    const selectedIds = mode.action.map(a => a.numberdevice);
    setCheckedDeviceIds(selectedIds);
    setSelectedDevices(SCENE_DEVICE_KEYS.filter(d => selectedIds.includes(d.id)).map(d => {
      const act = mode.action.find(a => a.numberdevice === d.id);
      let value = act ? act.status : null;
      let state = value;
      if (d.key === 'servo') state = value >= 45 ? 'open' : 'close';
      if (d.key === 'fan') state = PERCENT_TO_FAN_LEVEL[value] || 0;
      if (d.key.startsWith('light')) state = { state: !!value, brightness: 50 };
      return { ...d, state };
    }));
    setSceneStep(2);
  };

  const cancelEditMode = () => {
    setDraftMode(null);
    setSceneStep(1);
    setCheckedDeviceIds([]);
    setSelectedDevices([]);
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

    const trimmedName = draftMode.name.trim();

    // Lấy tên cũ nếu đang ở chế độ Edit
    const originalMode = draftMode.id ? modes.find(m => m.id === draftMode.id) : null;
    const isNameChanged = originalMode && originalMode.name.toLowerCase() !== trimmedName.toLowerCase();
    
    // Kiểm tra xem tên mới đã có trong danh sách chưa
    const existingModeWithSameName = modes.find(m => m.name.toLowerCase() === trimmedName.toLowerCase());
    
    // NẾU: Tạo mới mode bị trùng tên HOẶC Đổi tên mode thành tên bị trùng
    if ((!originalMode || isNameChanged) && existingModeWithSameName) {
      const confirmOverwrite = window.confirm(
        `Cảnh báo: Chế độ mang tên "${existingModeWithSameName.name}" đã tồn tại!\n\nBạn có muốn GHI ĐÈ thiết lập của chế độ đã có không?\n\n- Nhấn [OK] để Ghi đè\n- Nhấn [Cancel] để Đổi tên chế độ mới`
      );
      if (!confirmOverwrite) {
        return; // Dừng lại ở Bước 2 để người dùng đổi tên
      }
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
        name: trimmedName,
        action,
        isactive: false
      });

      // Nếu đang Edit và người dùng đã ĐỔI TÊN, cần xóa bản ghi mang tên cũ trên DB
      if (originalMode && isNameChanged) {
        await axios.delete(`${API_BASE}/scenes`, { params: { name: originalMode.name } });
      }

      // Reload danh sách
      const res = await axios.get(`${API_BASE}/scenes`);
      setModes(prevModes => {
        const activeIds = new Set(prevModes.filter(m => m.active).map(m => m.id));
        return res.data.map(m => ({
          id: m.modeid || m._id,
          name: m.name || 'Không tên',
          active: activeIds.has(m.modeid || m._id),
          action: m.action || []
        }));
      });

      setDraftMode(null);
      setSceneStep(1);
      setCheckedDeviceIds([]);
      setSelectedDevices([]);
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

    // Helper: Map device id to string name
    const DEVICE_NAMES = { 2: 'Đèn 2', 3: 'Đèn 3', 4: 'Đèn 4', 6: 'Servo (Cửa)', 7: 'Quạt' };

    if (active) {
      // KIỂM TRA TRÙNG THIẾT BỊ TẤT CẢ CÁC THIẾT BỊ
      const activeModes = modes.filter(m => m.active && m.id !== id);
      
      // Dùng Map để lưu trữ xem thiết bị nào đang bị chiếm bởi chế độ nào
      const deviceToModeMap = new Map(); 
      
      activeModes.forEach(m => {
        m.action.forEach(a => {
          deviceToModeMap.set(a.numberdevice, m.name); // Ánh xạ: ID thiết bị -> Tên chế độ
        });
      });

      const conflicts = targetMode.action.filter(a => deviceToModeMap.has(a.numberdevice));

      if (conflicts.length > 0) {
        // Tạo câu thông báo chi tiết, VD: "Đèn 2 (tại chế độ Ban đêm), Quạt (tại chế độ Mùa hè)"
        const conflictDetails = conflicts.map(a => {
          const devName = DEVICE_NAMES[a.numberdevice] || `TB ${a.numberdevice}`;
          const conflictingModeName = deviceToModeMap.get(a.numberdevice);
          return `${devName}" thuộc chế độ "${conflictingModeName}"`; 
        }).join(', ');

        if (addToast) {
          addToast(`⚠️ Cảnh báo:  Chế độ không được bật do trùng thiết bị "${conflictDetails}`, 'error');
        }
        return; // Dừng kích hoạt chế độ này
      }

      const actionsToApply = targetMode.action;

      try {
        setDeviceStates(prev => {
          let next = { ...prev };
          actionsToApply.forEach(act => {
            const beVal = act.status;
            let feVal = beVal;
            if (act.numberdevice === 6) feVal = beVal >= 45 ? 'open' : 'close';
            if (act.numberdevice === 7) feVal = PERCENT_TO_FAN_LEVEL[beVal] || 0;
            if (act.numberdevice <= 5) feVal = { state: !!beVal, brightness: 50 };
            
            const ID_TO_KEY = { 1: 'light1', 2: 'light2', 3: 'light3', 4: 'light4', 6: 'servo', 7: 'fan' };
            const key = ID_TO_KEY[act.numberdevice];
            if (key) {
              next[key] = feVal;
            }
          });
          syncToBackend(next);
          return next;
        });

        setModes(prev => prev.map(m => m.id === id ? { ...m, active: true } : m));
        if (addToast) addToast(`✅ Kích hoạt chế độ "${targetMode.name}" thành công!`, 'success');
      } catch (err) {
        console.error('Lỗi kích hoạt:', err);
      }
    } else {
      // Khi TẮT chế độ
      try {
        const activeModes = modes.filter(m => m.active && m.id !== id);
        const otherActiveIds = new Set();
        // Giữ nguyên thiết bị nếu có GIÁ TRỊ TỪ BẤT KỲ active mode NÀO KHÁC đang tham chiếu
        activeModes.forEach(m => m.action.forEach(a => otherActiveIds.add(a.numberdevice)));
        
        const actionsToReverse = targetMode.action.filter(a => !otherActiveIds.has(a.numberdevice));

        setDeviceStates(prev => {
          let next = { ...prev };
          actionsToReverse.forEach(act => {
            let feVal = false;
            if (act.numberdevice === 6) feVal = 'close';
            if (act.numberdevice === 7) feVal = 0;
            if (act.numberdevice <= 4) feVal = { state: false, brightness: 50 };
            
            const ID_TO_KEY = { 1: 'light1', 2: 'light2', 3: 'light3', 4: 'light4', 6: 'servo', 7: 'fan' };
            const key = ID_TO_KEY[act.numberdevice];
            if (key) {
              next[key] = feVal;
            }
          });
          syncToBackend(next);
          return next;
        });

        setModes(prev => prev.map(m => m.id === id ? { ...m, active: false } : m));
      } catch (err) {
        console.error('Lỗi tắt chế độ:', err);
      }
    }
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
    // 2-step scene creation
    sceneStep,
    checkedDeviceIds,
    toggleDeviceCheck,
    goToStep1,
    goToStep2,
    selectedDevices,
    updateDraftDevice,
    SCENE_DEVICE_KEYS,
  };
}
