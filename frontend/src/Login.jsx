import React, { useState } from 'react';
import { Home, Mail, Lock, Hash, Eye, EyeOff } from 'lucide-react';

export default function Login({ onLoginSubmit }) {
  const [houseId, setHouseId] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const [houseIdFocused, setHouseIdFocused] = useState(false);
  const [emailFocused, setEmailFocused] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    if (onLoginSubmit) {
      onLoginSubmit({ houseId, email, password });
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ backgroundColor: "#0B0E14", fontFamily: "Manrope, sans-serif" }}>
      {/* Background Effects */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0" style={{
            backgroundImage: "linear-gradient(rgba(0, 204, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 204, 255, 0.03) 1px, transparent 1px)",
            backgroundSize: "50px 50px",
            animation: "gridPulse 8s ease-in-out infinite"
        }} />
      </div>
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-[120px] animate-pulse" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-[120px] animate-pulse" />

      <div className="relative z-10 min-h-screen flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md animate-fadeIn">
          
          {/* Tiêu đề */}
          <div className="text-center animate-slideDown" style={{ marginBottom: '20px' }}>
            <div className="inline-flex items-center justify-center mb-6 relative group">
              <div className="absolute inset-0 bg-cyan-500/20 rounded-full blur-xl group-hover:bg-cyan-500/30 transition-all duration-500" />
              <div className="relative bg-linear-to-br from-[#1A1F26] to-[#0B0E14] p-4 rounded-2xl border border-[#2D333B]">
                <Home className="w-10 h-10 text-cyan-400" strokeWidth={1.5} />
              </div>
            </div>
            <h1 className="text-4xl mb-2 tracking-wider font-bold text-white uppercase">Hệ Thống Quản Lý Nhà THÔNG MINH</h1>
          </div>

          {/* Phần bao quanh Form - Đã xóa khung, chỉ giữ lại hiệu ứng xuất hiện */}
          <div className="relative animate-slideUp">
            <form onSubmit={handleLogin} className="flex flex-col items-center w-full">
              
              {/* HOUSE ID */}
              <div className="w-full max-w-[320px]" style={{ marginBottom: '20px' }}>
                <label className="block text-gray-400 mb-3 text-base uppercase tracking-widest text-left">
                  House ID
                </label>
                <div className="relative">
                  {!houseId && (
                    <Hash className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" size={18} />
                  )}
                  <input
                    type="text" value={houseId} onChange={(e) => setHouseId(e.target.value)}
                    onFocus={() => setHouseIdFocused(true)} onBlur={() => setHouseIdFocused(false)}
                    placeholder="e.g. HS001" required
                    className={`w-full ${houseId ? 'pl-4' : 'pl-12'} py-4 rounded-lg border bg-[#1A1F26] text-white outline-none text-xl transition-all duration-300`}
                    style={{ borderColor: houseIdFocused ? "#00CCFF" : "#2D333B" }}
                  />
                </div>
              </div>

              {/* EMAIL */}
              <div className="w-full max-w-[320px]" style={{ marginBottom: '20px' }}>
                <label className="block text-gray-400 mb-3 text-base uppercase tracking-widest text-left">
                  Username/Email
                </label>
                <div className="relative">
                  {!email && (
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" size={18} />
                  )}
                  <input
                    type="text" value={email} onChange={(e) => setEmail(e.target.value)}
                    onFocus={() => setEmailFocused(true)} onBlur={() => setEmailFocused(false)}
                    placeholder="Username or email" required
                    className={`w-full ${email ? 'pl-4' : 'pl-12'} py-4 rounded-lg border bg-[#1A1F26] text-white outline-none text-xl transition-all duration-300 focus:bg-[#1A1F26]`}
                    style={{ borderColor: emailFocused ? "#00CCFF" : "#2D333B" }}
                  />
                </div>
              </div>

              {/* PASSWORD */}
              <div className="w-full max-w-[320px]" style={{ marginBottom: '30px' }}>
                <label className="block text-gray-400 mb-3 text-base uppercase tracking-widest text-left">
                  Password
                </label>
                <div className="relative">
                  {!password && (
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" size={18} />
                  )}
                  <input
                    type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setPasswordFocused(true)} onBlur={() => setPasswordFocused(false)}
                    placeholder="••••••••" required
                    className={`w-full ${password ? 'pl-4' : 'pl-12'} pr-12 py-4 rounded-lg border bg-[#1A1F26] text-white outline-none text-xl transition-all duration-300 focus:bg-[#1A1F26]`}
                    style={{ borderColor: passwordFocused ? "#00CCFF" : "#2D333B" }}
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>

              {/* NÚT BẤM */}
              <div className="w-full max-w-[320px]">
                <button
                  type="submit"
                  className="w-full py-5 rounded-lg bg-linear-to-r from-[#00CCFF] to-[#0099CC] text-[#ffffff] font-black tracking-widest text-3xl hover:scale-[1.03] active:scale-95 transition-all shadow-[0_0_25px_rgba(0,204,255,0.4)]"
                >
                  SIGN IN
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes gridPulse { 0%, 100% { opacity: 0.2; } 50% { opacity: 0.4; } }
        .animate-fadeIn { animation: fadeIn 0.8s ease-out forwards; }
        .animate-slideDown { animation: slideDown 0.6s ease-out forwards; }
        .animate-slideUp { animation: slideUp 0.6s ease-out forwards; }
        input:-webkit-autofill,
        input:-webkit-autofill:hover, 
        input:-webkit-autofill:focus {
          -webkit-text-fill-color: white;
          -webkit-box-shadow: 0 0 0px 1000px #1A1F26 inset;
          transition: background-color 5000s ease-in-out 0s;
        }
      `}</style>
    </div>
  );
}