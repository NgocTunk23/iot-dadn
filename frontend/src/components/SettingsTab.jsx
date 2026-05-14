import React, { useState, useEffect } from 'react';
import { User, Home, Shield, Settings, Key, LogOut, ChevronDown, ChevronUp, Thermometer, Droplets, Sun, Zap, CheckCircle, XCircle } from 'lucide-react';

export default function SettingsTab({ onLogout }) {
  const [houseInfo, setHouseInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [localCreds, setLocalCreds] = useState({ houseid: '', username: '' });
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [changePasswordData, setChangePasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [changePasswordMessage, setChangePasswordMessage] = useState('');

  useEffect(() => {
    // 1. Đọc dữ liệu từ Local Storage
    let houseid = localStorage.getItem('houseid') || '';
    let userRaw = localStorage.getItem('username') || '';
    
    let username = "";
    try {
      const userObj = JSON.parse(userRaw);
      username = userObj.username || userRaw; 
    } catch {
      username = userRaw;
    }

    // Xóa sạch dấu nháy kép/nháy đơn ở 2 đầu chuỗi để gửi lên Backend chuẩn xác
    if (typeof username === 'string') username = username.replace(/^["']|["']$/g, '');
    if (typeof houseid === 'string') houseid = houseid.replace(/^["']|["']$/g, '');

    setLocalCreds({ houseid, username });

    // 2. Gọi API tra cứu thông tin
    if (houseid && username) {
      fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/house-info?houseid=${houseid}&username=${username}`)
        .then(res => res.json())
        .then(data => {
          if (!data.error) {
            setHouseInfo(data);
          }
          setLoading(false);
        })
        .catch(err => {
          console.error("[SettingsTab] Lỗi lấy thông tin nhà:", err);
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('houseid');
    localStorage.removeItem('user');
    sessionStorage.removeItem('user');

    if (onLogout) {
      onLogout();
    } else {
      window.location.reload(); 
    }
  };

  const handleChangePassword = async () => {
    setChangePasswordMessage('');
    const { oldPassword, newPassword, confirmPassword } = changePasswordData;
    if (!oldPassword || !newPassword || !confirmPassword) {
      setChangePasswordMessage('Vui lòng điền đầy đủ thông tin');
      return;
    }
    if (newPassword !== confirmPassword) {
      setChangePasswordMessage('Mật khẩu mới không khớp');
      return;
    }
    const token = localStorage.getItem('token');
    if (!token) {
      setChangePasswordMessage('Không tìm thấy token');
      return;
    }
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/api/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword
        })
      });
      const result = await response.json();
      if (result.success) {
        setChangePasswordMessage('Đổi mật khẩu thành công. Vui lòng đăng nhập lại.');
        setTimeout(() => {
          handleLogout();
        }, 2000);
      } else {
        setChangePasswordMessage(result.message || 'Đổi mật khẩu thất bại');
      }
    } catch (error) {
      setChangePasswordMessage('Lỗi kết nối server');
    }
  };

  return (
    <div className="settings-container" style={{
      padding: '20px',
      maxWidth: '800px',
      margin: '0 auto',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
    }}>
      {/* Header Section */}
      <div className="settings-header" style={{
        textAlign: 'center',
        marginBottom: '32px',
        padding: '24px',
        background: 'linear-gradient(135deg, rgba(0, 204, 255, 0.1) 0%, rgba(102, 126, 234, 0.1) 100%)',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{
          width: '80px',
          height: '80px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #00ccff 0%, #667eea 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 16px',
          boxShadow: '0 8px 32px rgba(0, 204, 255, 0.3)'
        }}>
          <User size={36} color="white" />
        </div>
        <h2 style={{
          color: '#ffffff',
          margin: '0',
          fontSize: '28px',
          fontWeight: '700',
          background: 'linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}>
          Tài khoản & Cài đặt
        </h2>
        <p style={{ color: 'rgba(255, 255, 255, 0.7)', margin: '8px 0 0 0', fontSize: '16px' }}>
          Quản lý thông tin và bảo mật tài khoản của bạn
        </p>
      </div>
      {/* User Profile Card */}
      <div className="profile-card" style={{
        background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '24px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{
            width: '60px',
            height: '60px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginRight: '16px',
            boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)'
          }}>
            <User size={28} color="white" />
          </div>
          <div>
            <h3 style={{ color: '#ffffff', margin: '0 0 4px 0', fontSize: '20px', fontWeight: '600' }}>
              {houseInfo?._id?.username || localCreds.username}
            </h3>
            <p style={{ color: 'rgba(255, 255, 255, 0.6)', margin: '0', fontSize: '14px' }}>
              Mã nhà: {houseInfo?._id?.houseid || localCreds.houseid}
            </p>
          </div>
        </div>
      </div>

      {/* House Information Card */}
      {loading ? (
        <div style={{
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '16px',
          padding: '40px',
          textAlign: 'center',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '3px solid rgba(0, 204, 255, 0.3)',
            borderTop: '3px solid #00ccff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <p style={{ color: '#ffffff', margin: '0', fontSize: '16px' }}>Đang tải thông tin ngôi nhà...</p>
        </div>
      ) : houseInfo ? (
        <div className="house-info-card" style={{
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '24px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px' }}>
            <Home size={24} color="#00ccff" />
            <h3 style={{ color: '#ffffff', margin: '0 0 0 12px', fontSize: '20px', fontWeight: '600' }}>
              Thông tin ngôi nhà
            </h3>
          </div>

          {/* Safety Thresholds */}
          <div style={{ marginBottom: '24px' }}>
            <h4 style={{
              color: '#ffffff',
              margin: '0 0 16px 0',
              fontSize: '16px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center'
            }}>
              <Shield size={18} color="#52c41a" style={{ marginRight: '8px' }} />
              Ngưỡng an toàn
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px' }}>
              <div style={{
                background: 'rgba(255, 0, 0, 0.1)',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid rgba(255, 0, 0, 0.2)',
                textAlign: 'center'
              }}>
                <Thermometer size={20} color="#ff2400" style={{ marginBottom: '4px' }} />
                <p style={{ color: '#ffffff', margin: '0', fontSize: '12px', fontWeight: '500' }}>Nhiệt độ</p>
                <p style={{ color: '#ff2400', margin: '4px 0 0 0', fontSize: '14px', fontWeight: '600' }}>
                  {houseInfo.tempmin}°C - {houseInfo.tempmax}°C
                </p>
              </div>
              <div style={{
                background: 'rgba(24, 144, 255, 0.1)',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid rgba(24, 144, 255, 0.2)',
                textAlign: 'center'
              }}>
                <Droplets size={20} color="#1890ff" style={{ marginBottom: '4px' }} />
                <p style={{ color: '#ffffff', margin: '0', fontSize: '12px', fontWeight: '500' }}>Độ ẩm</p>
                <p style={{ color: '#1890ff', margin: '4px 0 0 0', fontSize: '14px', fontWeight: '600' }}>
                  {houseInfo.humimin}% - {houseInfo.humimax}%
                </p>
              </div>
              <div style={{
                background: 'rgba(250, 173, 20, 0.1)',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid rgba(250, 173, 20, 0.2)',
                textAlign: 'center'
              }}>
                <Sun size={20} color="#faad14" style={{ marginBottom: '4px' }} />
                <p style={{ color: '#ffffff', margin: '0', fontSize: '12px', fontWeight: '500' }}>Ánh sáng</p>
                <p style={{ color: '#faad14', margin: '4px 0 0 0', fontSize: '14px', fontWeight: '600' }}>
                  {houseInfo.lightmin}% - {houseInfo.lightmax}%
                </p>
              </div>
            </div>
          </div>

          {/* Devices List */}
          <div>
            <h4 style={{
              color: '#ffffff',
              margin: '0 0 16px 0',
              fontSize: '16px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center'
            }}>
              <Zap size={18} color="#00ccff" style={{ marginRight: '8px' }} />
              Thiết bị ({houseInfo.numberdevices?.length || 0})
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
              {[...(houseInfo.numberdevices || [])]
                .sort((a, b) => a.numberdevice - b.numberdevice)
                .map((dev, index) => {
                  let statusDisplay = '';
                  let statusColor = '#ff4d4f';
                  let StatusIcon = XCircle;

                  if (dev.type === 'quat') {
                    if (dev.status === 0) {
                      statusDisplay = 'Tắt';
                      statusColor = '#ff4d4f';
                      StatusIcon = XCircle;
                    } else {
                      statusDisplay = `Mức ${(dev.status - 60) / 10}`;
                      statusColor = '#52c41a';
                      StatusIcon = CheckCircle;
                    }
                  } else if (dev.type === 'servo') {
                    statusDisplay = dev.status === 0 ? 'Đóng' : `Mở (${dev.status}°)`;
                    statusColor = dev.status === 0 ? '#ff4d4f' : '#52c41a';
                    StatusIcon = dev.status === 0 ? XCircle : CheckCircle;
                  } else {
                    statusDisplay = dev.status ? 'Bật' : 'Tắt';
                    statusColor = dev.status ? '#52c41a' : '#ff4d4f';
                    StatusIcon = dev.status ? CheckCircle : XCircle;
                  }

                  return (
                    <div key={index} style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      padding: '12px',
                      borderRadius: '8px',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}>
                      <div>
                        <p style={{ color: '#ffffff', margin: '0 0 4px 0', fontSize: '14px', fontWeight: '500' }}>
                          Thiết bị {dev.numberdevice}
                        </p>
                        <p style={{ color: 'rgba(255, 255, 255, 0.6)', margin: '0', fontSize: '12px' }}>
                          {dev.type}
                        </p>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center' }}>
                        <span style={{
                          color: statusColor,
                          fontSize: '12px',
                          fontWeight: '600',
                          marginRight: '8px'
                        }}>
                          {statusDisplay}
                        </span>
                        <StatusIcon size={16} color={statusColor} />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>
      ) : (
        <div style={{ marginBottom: '24px', padding: '16px', backgroundColor: '#fff2f0', border: '1px solid #ffccc7', borderRadius: '8px' }}>
          <p style={{ color: '#ff4d4f', margin: 0 }}>Không tìm thấy thông tin ngôi nhà hoặc kết nối bị lỗi.</p>
          <p style={{ color: '#666', margin: '8px 0 0 0', fontSize: '13px' }}>User: {localCreds.username} | House: {localCreds.houseid}</p>
        </div>
      )}

      {/* Change Password Section */}
      <div className="change-password-card" style={{
        background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        overflow: 'hidden'
      }}>
        <button
          onClick={() => setShowChangePassword(!showChangePassword)}
          style={{
            width: '100%',
            padding: '20px',
            background: 'transparent',
            border: 'none',
            color: '#ffffff',
            fontSize: '18px',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            transition: 'all 0.3s ease'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Key size={20} color="#00ccff" style={{ marginRight: '12px' }} />
            Đổi mật khẩu
          </div>
          {showChangePassword ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>

        {showChangePassword && (
          <div style={{
            padding: '0 20px 20px 20px',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            animation: 'slideDown 0.3s ease'
          }}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{
                display: 'block',
                color: '#ffffff',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '500'
              }}>
                Mật khẩu hiện tại
              </label>
              <input
                type="password"
                value={changePasswordData.oldPassword}
                onChange={(e) => setChangePasswordData({...changePasswordData, oldPassword: e.target.value})}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: '#ffffff',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.3s ease'
                }}
                placeholder="Nhập mật khẩu hiện tại"
              />
            </div>
            <div style={{ marginBottom: '16px' }}>
              <label style={{
                display: 'block',
                color: '#ffffff',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '500'
              }}>
                Mật khẩu mới
              </label>
              <input
                type="password"
                value={changePasswordData.newPassword}
                onChange={(e) => setChangePasswordData({...changePasswordData, newPassword: e.target.value})}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: '#ffffff',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.3s ease'
                }}
                placeholder="Nhập mật khẩu mới"
              />
            </div>
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block',
                color: '#ffffff',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '500'
              }}>
                Xác nhận mật khẩu mới
              </label>
              <input
                type="password"
                value={changePasswordData.confirmPassword}
                onChange={(e) => setChangePasswordData({...changePasswordData, confirmPassword: e.target.value})}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: '#ffffff',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.3s ease'
                }}
                placeholder="Nhập lại mật khẩu mới"
              />
            </div>
            <button
              onClick={handleChangePassword}
              style={{
                width: '100%',
                padding: '14px',
                background: 'linear-gradient(135deg, #00ccff 0%, #667eea 100%)',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                marginBottom: '12px',
                boxShadow: '0 4px 16px rgba(0, 204, 255, 0.3)'
              }}
              onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
              onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
            >
              Đổi mật khẩu
            </button>
            {changePasswordMessage && (
              <div style={{
                padding: '12px',
                borderRadius: '8px',
                background: changePasswordMessage.includes('thành công')
                  ? 'rgba(82, 196, 26, 0.1)'
                  : 'rgba(255, 77, 79, 0.1)',
                border: `1px solid ${changePasswordMessage.includes('thành công') ? '#52c41a' : '#ff4d4f'}`,
                color: changePasswordMessage.includes('thành công') ? '#52c41a' : '#ff4d4f',
                fontSize: '14px',
                textAlign: 'center'
              }}>
                {changePasswordMessage}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Logout Button */}
      <button
        onClick={handleLogout}
        style={{
          width: '100%',
          padding: '16px',
          background: 'linear-gradient(135deg, rgba(255, 77, 79, 0.1) 0%, rgba(255, 77, 79, 0.05) 100%)',
          color: '#ff4d4f',
          border: '1px solid rgba(255, 77, 79, 0.3)',
          borderRadius: '12px',
          fontSize: '16px',
          fontWeight: '600',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          marginTop: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 4px 16px rgba(255, 77, 79, 0.1)'
        }}
        onMouseOver={(e) => {
          e.target.style.transform = 'translateY(-2px)';
          e.target.style.boxShadow = '0 8px 32px rgba(255, 77, 79, 0.2)';
        }}
        onMouseOut={(e) => {
          e.target.style.transform = 'translateY(0)';
          e.target.style.boxShadow = '0 4px 16px rgba(255, 77, 79, 0.1)';
        }}
      >
        <LogOut size={18} style={{ marginRight: '8px' }} />
        Đăng xuất
      </button>

      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}