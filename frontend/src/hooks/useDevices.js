import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const FAN_LEVEL_TO_PERCENT = { 0: 0, 1: 70, 2: 80, 3: 90, 4: 100 };
const PERCENT_TO_FAN_LEVEL = { 0: 0, 70: 1, 80: 2, 90: 3, 100: 4 };

export default function useDevices(addToast) {
  const [deviceStates, setDeviceStates] = useState({});
  const [modes, setModes] = useState([]);
  
  // Dynamic Configuration Array from backend
  const [SCENE_DEVICE_KEYS, setSceneDeviceKeys] = useState([]);
  const [antiTheftId, setAntiTheftId] = useState(null); // The ID representing the anti-theft light (denchongtrom)

  // 2-Step Configuration State
  const [draftMode, setDraftMode] = useState(null);
  const [sceneStep, setSceneStep] = useState(1);
  const [checkedDeviceIds, setCheckedDeviceIds] = useState([]); 
  const [selectedDevices, setSelectedDevices] = useState([]); 

  const houseId = localStorage.getItem('houseid') || 'HS001';
  const modesRef = useRef(modes);
  modesRef.current = modes;
  const lastActionTime = useRef(0);

  const getDeviceConfig = useCallback((id) => {
      const parsedId = parseInt(id, 10);
      return SCENE_DEVICE_KEYS.find(d => d.id === parsedId) || (parsedId === antiTheftId ? {id: parsedId, typeRaw: 'denchongtrom'} : null);
  }, [SCENE_DEVICE_KEYS, antiTheftId]);

  const parseBEStatusToFE = useCallback((id, type, beStatus) => {
      let feVal = beStatus;
      if (type === 'servo') feVal = (beStatus >= 45) ? 'open' : 'close';
      else if (type === 'quat') {
          const l = PERCENT_TO_FAN_LEVEL[beStatus];
          feVal = l !== undefined ? l : 0;
      }
      else if (type === 'den' || type === 'denchongtrom') {
          feVal = { state: !!beStatus, brightness: 50 };
      }
      return feVal;
  }, []);

  const parseFEStateToBE = useCallback((type, feState) => {
      let beVal = feState;
      if (type === 'servo') beVal = (feState === 'open') ? 90 : 0;
      else if (type === 'quat') beVal = FAN_LEVEL_TO_PERCENT[feState] || 0;
      else if (type === 'den' || type === 'denchongtrom') {
          beVal = feState.state !== undefined ? feState.state : !!feState;
      }
      return beVal;
  }, []);

  const syncToBackend = useCallback(async (newState) => {
    try {
      const commands = [];
      for(const key of Object.keys(newState)) {
          const id = parseInt(key.replace('device_', ''), 10);
          const devConfig = getDeviceConfig(id);
          if(!devConfig) continue;
          
          const beVal = parseFEStateToBE(devConfig.typeRaw, newState[key]);
          commands.push([id, beVal]);
      }
      if(commands.length > 0) {
        await axios.post(`${API_BASE}/control`, { houseid: houseId, commands });
      }
    } catch (err) {
      console.error('Lỗi gửi lệnh điều khiển:', err);
      if (addToast) addToast('Lỗi gửi lệnh điều khiển đến thiết bị!', 'error');
    }
  }, [addToast, houseId, getDeviceConfig, parseFEStateToBE]);

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

  // Bootup Initial Data Loader
  useEffect(() => {
    const loadConfig = async () => {
        try {
            const configRes = await axios.get(`${API_BASE}/devices-info?houseid=${houseId}`);
            if(configRes.data && configRes.data.devices) {
                const devs = configRes.data.devices;
                const keys = [];
                let antiTheft = null;
                const defaultStates = {};
                
                devs.forEach(d => {
                    const id = d.numberdevice;
                    const typeRaw = d.type;
                    const name = d.name;
                    const status = d.status;
                    const feType = typeRaw === 'servo' ? 'servo' : (typeRaw === 'quat' ? 'fan' : 'switch');
                    
                    if(typeRaw === 'denchongtrom') {
                        antiTheft = id;
                    } else {
                        keys.push({ key: `device_${id}`, label: name, type: feType, id, typeRaw: typeRaw });
                    }
                    defaultStates[`device_${id}`] = parseBEStatusToFE(id, typeRaw, status);
                });
                
                setSceneDeviceKeys(keys);
                setAntiTheftId(antiTheft);
                setDeviceStates(prev => ({...defaultStates, ...prev})); // Preserve dynamic updates
            }
        } catch (e) {
            console.error("Lỗi lấy device config", e);
        }
    };
    loadConfig();
  }, [houseId, parseBEStatusToFE]);

  useEffect(() => {
    const loadModes = async () => {
      try {
        const res = await axios.get(`${API_BASE}/scenes?houseid=${houseId}`);
        if (Array.isArray(res.data)) {
          const loaded = res.data.map(m => ({
            id: m.modeid || m._id,
            name: m.name || 'Không tên',
            active: m.active !== undefined ? m.active : m.isactive,
            action: m.action || []
          }));
          setModes(loaded);
        }
      } catch (err) { }
    };

    const loadDeviceStatus = async () => {
      try {
        const res = await axios.get(`${API_BASE}/sensor-data?houseid=${houseId}`);
        if (res.data && res.data.numberdevice) {
          const beStatusList = res.data.numberdevice;
          setDeviceStates(prev => {
              const map = {...prev};
              beStatusList.forEach(item => {
                  const id = item[0];
                  const beStatus = item[1];
                  const devConfig = SCENE_DEVICE_KEYS.find(d => d.id === id) || (id === antiTheftId ? {typeRaw: 'denchongtrom'} : null);
                  if(devConfig) {
                     map[`device_${id}`] = parseBEStatusToFE(id, devConfig.typeRaw, beStatus);
                  }
              });
              return map;
          });
        }
      } catch (err) {}
    };

    loadModes();
    const timer = setInterval(loadDeviceStatus, 3000);
    return () => clearInterval(timer);
  }, [houseId, SCENE_DEVICE_KEYS, antiTheftId, parseBEStatusToFE]);

  // SCENE CREATION
  const startCreateMode = () => {
    setDraftMode({ name: '', isactive: false });
    setSceneStep(1);
    setCheckedDeviceIds([]);
    setSelectedDevices([]);
  };

  const toggleDeviceCheck = (deviceId) => {
    setCheckedDeviceIds(prev => prev.includes(deviceId) ? prev.filter(id => id !== deviceId) : [...prev, deviceId]);
  };

  const goToStep2 = () => {
    if (checkedDeviceIds.length === 0) {
      if (addToast) addToast('Vui lòng chọn ít nhất một thiết bị!', 'error');
      return;
    }
    const devices = SCENE_DEVICE_KEYS
      .filter(d => checkedDeviceIds.includes(d.id))
      .map(d => {
        let initialState = false;
        if (d.type === 'servo') initialState = 'close';
        if (d.type === 'fan') initialState = 0;
        if (d.type === 'switch') initialState = { state: true, brightness: 50 };
        return { ...d, state: initialState };
      });
    setSelectedDevices(devices);
    setSceneStep(2);
  };

  const goToStep1 = () => setSceneStep(1);

  const startEditMode = (mode) => {
    setDraftMode({ ...mode });
    const selectedIds = mode.action.map(a => a.numberdevice);
    setCheckedDeviceIds(selectedIds);
    setSelectedDevices(SCENE_DEVICE_KEYS.filter(d => selectedIds.includes(d.id)).map(d => {
      const act = mode.action.find(a => a.numberdevice === d.id);
      let value = act ? act.status : null;
      let state = parseBEStatusToFE(d.id, d.typeRaw, value);
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
    const trimmedName = draftMode.name.trim();
    const originalMode = draftMode.id ? modes.find(m => m.id === draftMode.id) : null;
    const isNameChanged = originalMode && originalMode.name.toLowerCase() !== trimmedName.toLowerCase();
    const existingModeWithSameName = modes.find(m => m.name.toLowerCase() === trimmedName.toLowerCase());
    
    if ((!originalMode || isNameChanged) && existingModeWithSameName) {
      const confirmOverwrite = window.confirm(`Đã tồn tại chế độ "${trimmedName}". Ghi đè?`);
      if (!confirmOverwrite) return;
    }

    const action = selectedDevices.map(d => {
      let status = parseFEStateToBE(d.typeRaw, d.state);
      return { numberdevice: d.id, status };
    });

    try {
      await axios.post(`${API_BASE}/scenes`, { houseid: houseId, name: trimmedName, action, isactive: false });
      if (originalMode && isNameChanged) await axios.delete(`${API_BASE}/scenes`, { params: { houseid: houseId, name: originalMode.name } });

      const res = await axios.get(`${API_BASE}/scenes?houseid=${houseId}`);
      if(Array.isArray(res.data)) {
        const activeIds = new Set(modesRef.current.filter(m => m.active).map(m => m.id));
        setModes(res.data.map(m => ({
          id: m.modeid || m._id, name: m.name || 'Không tên',
          active: activeIds.has(m.modeid || m._id), action: m.action || []
        })));
      }

      setDraftMode(null);
      setSceneStep(1);
      setCheckedDeviceIds([]);
      setSelectedDevices([]);
      if (addToast) addToast('Đã lưu chế độ!', 'success');
    } catch (err) {}
  };

  const deleteMode = async (id) => {
    const mode = modes.find(m => m.id === id);
    if (!mode) return;
    try {
      await axios.delete(`${API_BASE}/scenes`, { params: { houseid: houseId, name: mode.name } });
      setModes(prev => prev.filter(m => m.id !== id));
      if (addToast) addToast('Đã xóa chế độ!', 'info');
    } catch (err) {}
  };

  const toggleMode = async (id, active) => {
    const targetMode = modes.find(m => m.id === id);
    if (!targetMode) return;

    if (active) {
      const activeModes = modes.filter(m => m.active && m.id !== id);
      const deviceToModeMap = new Map(); 
      activeModes.forEach(m => m.action.forEach(a => deviceToModeMap.set(a.numberdevice, m.name)));

      const conflicts = targetMode.action.filter(a => deviceToModeMap.has(a.numberdevice));
      if (conflicts.length > 0) {
        if (addToast) addToast(`Từ chối do trùng lặp thiết bị với kịch bản khác!`, 'error');
        return;
      }

      try {
        setDeviceStates(prev => {
          let next = { ...prev };
          targetMode.action.forEach(act => {
             const dConf = getDeviceConfig(act.numberdevice);
             if(dConf) next[`device_${act.numberdevice}`] = parseBEStatusToFE(act.numberdevice, dConf.typeRaw, act.status);
          });
          syncToBackend(next);
          return next;
        });

        setModes(prev => prev.map(m => m.id === id ? { ...m, active: true } : m));
      } catch (err) {}
    } else {
      try {
        const activeModes = modes.filter(m => m.active && m.id !== id);
        const otherActiveIds = new Set();
        activeModes.forEach(m => m.action.forEach(a => otherActiveIds.add(a.numberdevice)));
        
        const actionsToReverse = targetMode.action.filter(a => !otherActiveIds.has(a.numberdevice));
        setDeviceStates(prev => {
          let next = { ...prev };
          actionsToReverse.forEach(act => {
             const dConf = getDeviceConfig(act.numberdevice);
             if(dConf) {
                  let feVal = false;
                  if (dConf.typeRaw === 'servo') feVal = 'close';
                  else if (dConf.typeRaw === 'quat') feVal = 0;
                  else if (dConf.typeRaw === 'den' || dConf.typeRaw === 'denchongtrom') feVal = { state: false, brightness: 50 };
                  next[`device_${act.numberdevice}`] = feVal;
             }
          });
          syncToBackend(next);
          return next;
        });
        setModes(prev => prev.map(m => m.id === id ? { ...m, active: false } : m));
      } catch (err) {}
    }
  };

  const updateDraftDevice = (id, field, value) => {
    setSelectedDevices(prev => prev.map(d => d.id === id ? { ...d, state: field ? { ...d.state, [field]: value } : value } : d));
  };

  return {
    deviceStates, modes, draftMode, setDraftMode, updateDevice,
    startCreateMode, startEditMode, cancelEditMode, saveMode, deleteMode, toggleMode,
    sceneStep, checkedDeviceIds, toggleDeviceCheck, goToStep1, goToStep2,
    selectedDevices, updateDraftDevice, SCENE_DEVICE_KEYS, antiTheftId
  };
}
