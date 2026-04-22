import { useState, useEffect } from "react";

const API_BASE = "http://localhost:5000/api";

const FILTER_OPTIONS = {
    danger: ["Tất cả", "Nguy hiểm", "Cảnh báo"],
    sensor: ["Tất cả", "Bình thường", "Cảnh báo", "Nguy hiểm"],
    device: ["Tất cả", "Hệ thống", "Người dùng"],
    update: null,
};

const TAB_CONFIG = {
    danger: {
        label: "Cảnh báo vượt ngưỡng",
        subtitle: "Danh sách các cảnh báo khi vượt ngưỡng cho phép",
        endpoint: `${API_BASE}/logging/danger-history?houseid=HS001`,
    },
    sensor: {
        label: "Dữ liệu cảm biến",
        subtitle: "Lịch sử ghi nhận dữ liệu từ các cảm biến (mỗi 5 phút)",
        endpoint: `${API_BASE}/logging/sensor-history?houseid=HS001`,
    },
    device: {
        label: "Trạng thái thiết bị",
        subtitle: "Theo dõi các thay đổi của thiết bị trong hệ thống",
        endpoint: `${API_BASE}/logging/device-history`,
    },
    update: {
        label: "Cập nhật hệ thống",
        subtitle: "Theo dõi các cập nhật và thay đổi hệ thống",
        endpoint: `${API_BASE}/logging/system-updates`,
    },
};

export default function LoggingTables({ houseid = "HS001" }) {
    const [activeTab, setActiveTab] = useState("danger");
    const [currentPage, setCurrentPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState([]);
    const [filter, setFilter] = useState("Tất cả");
    const itemsPerPage = 10;

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setData([]);
            try {
                const res = await fetch(TAB_CONFIG[activeTab].endpoint);
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const json = await res.json();
                setData(json);
            } catch (err) {
                console.error("Failed to fetch logging data:", err);
                setData([]);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [activeTab]);

    const handleTabChange = (tab) => {
        setActiveTab(tab);
        setCurrentPage(1);
        setFilter("Tất cả");
    };

    // Filter logic
    const filteredData = data.filter((item) => {
        if (filter === "Tất cả") return true;
        if (activeTab === "danger") return item.level === filter;
        if (activeTab === "sensor") return item.status === filter;
        if (activeTab === "device") return item.actor === filter;
        return true;
    });

    const totalPages = Math.max(1, Math.ceil(filteredData.length / itemsPerPage));
    const startIndex = (currentPage - 1) * itemsPerPage;
    const paginatedData = filteredData.slice(startIndex, startIndex + itemsPerPage);

    useEffect(() => { setCurrentPage(1); }, [filter]);

    // Shared styles
    const thStyle = { textAlign: "left", padding: "12px 8px", color: "#99a1af", fontSize: "14px", fontWeight: "500" };
    const tdStyle = { padding: "12px 8px", color: "#d1d5dc", fontSize: "14px" };
    const tdBold = { ...tdStyle, color: "white", fontWeight: "600" };
    const tdMuted = { ...tdStyle, color: "#99a1af", fontWeight: "600" };

    const badge = (bg, color, border, label) => (
        <span style={{ padding: "2px 8px", borderRadius: "8px", fontSize: "12px", fontWeight: "500", background: bg, color, border: `0.8px solid ${border}` }}>
            {label}
        </span>
    );

    const getLevelBadge = (level) => {
        const isDanger = level === "Nguy hiểm";
        return badge(
            isDanger ? "rgba(239,68,68,0.2)" : "rgba(240,177,0,0.2)",
            isDanger ? "#EF4444" : "#F0B100",
            isDanger ? "rgba(239,68,68,0.3)" : "rgba(240,177,0,0.3)",
            level
        );
    };

    const getStatusBadge = (status) => {
        const map = {
            "Bình thường": { bg: "rgba(0,188,125,0.2)", color: "#00d492", border: "rgba(0,188,125,0.3)" },
            "Cảnh báo": { bg: "rgba(240,177,0,0.2)", color: "#F0B100", border: "rgba(240,177,0,0.3)" },
            "Nguy hiểm": { bg: "rgba(239,68,68,0.2)", color: "#EF4444", border: "rgba(239,68,68,0.3)" },
        };
        const s = map[status] || map["Bình thường"];
        return badge(s.bg, s.color, s.border, status || "Bình thường");
    };

    const TAB_CONFIG = {
        danger: { 
            label: "Cảnh báo vượt ngưỡng",
            subtitle: "Danh sách các cảnh báo khi vượt ngưỡng cho phép",
            endpoint: `${API_BASE}/logging/danger-history?houseid=${houseid}&limit=50` 
        },
        sensor: { 
            label: "Dữ liệu cảm biến",
            subtitle: "Lịch sử ghi nhận dữ liệu từ các cảm biến (mỗi 5 phút)",
            endpoint: `${API_BASE}/logging/sensor-history?houseid=${houseid}&limit=50` 
        },
        device: { 
            label: "Trạng thái thiết bị",
            subtitle: "Theo dõi các thay đổi của thiết bị trong hệ thống",
            endpoint: `${API_BASE}/logging/device-history?houseid=${houseid}&limit=50` 
        },
        update: { 
            label: "Cập nhật hệ thống",
            subtitle: "Theo dõi các cập nhật và thay đổi hệ thống",
            endpoint: `${API_BASE}/logging/system-updates?houseid=${houseid}&limit=50` 
        },
    };

    // Filter dropdown
    const renderFilter = () => {
        const options = FILTER_OPTIONS[activeTab];
        if (!options) return null;
        return (
            <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                style={{
                    background: "#0f1419",
                    border: "0.8px solid #364153",
                    borderRadius: "8px",
                    padding: "6px 12px",
                    color: filter === "Tất cả" ? "#99a1af" : "#00b8db",
                    fontSize: "13px",
                    cursor: "pointer",
                    outline: "none",
                    height: "34px",
                }}
            >
                {options.map((opt) => (
                    <option key={opt} value={opt} style={{ background: "#1a1f2e", color: "white" }}>
                        {opt}
                    </option>
                ))}
            </select>
        );
    };

    const renderTableHead = () => {
        switch (activeTab) {
            case "danger": return (
                <tr style={{ borderBottom: "1px solid #1e2939" }}>
                    <th style={thStyle}>Thời gian</th><th style={thStyle}>Cảm biến</th>
                    <th style={thStyle}>Ngưỡng</th><th style={thStyle}>Giá trị thực</th>
                    <th style={thStyle}>Mức độ</th>
                </tr>
            );
            case "sensor": return (
                <tr style={{ borderBottom: "1px solid #1e2939" }}>
                    <th style={thStyle}>Thời gian</th><th style={thStyle}>Nhiệt độ</th>
                    <th style={thStyle}>Độ ẩm</th><th style={thStyle}>Ánh sáng</th>
                    <th style={thStyle}>Trạng thái</th>
                </tr>
            );
            case "device": return (
                <tr style={{ borderBottom: "1px solid #1e2939" }}>
                    <th style={thStyle}>Thời gian</th><th style={thStyle}>Thiết bị</th>
                    <th style={thStyle}>Giá trị cũ</th><th style={thStyle}>Giá trị mới</th>
                    <th style={thStyle}>Người thực hiện</th>
                </tr>
            );
            case "update": return (
                <tr style={{ borderBottom: "1px solid #1e2939" }}>
                    <th style={thStyle}>Thời gian</th><th style={thStyle}>Trường dữ liệu</th>
                    <th style={thStyle}>Giá trị cũ</th><th style={thStyle}>Giá trị mới</th>
                </tr>
            );
            default: return null;
        }
    };

    const renderRow = (item, index) => {
        const rowStyle = { borderBottom: "1px solid #1e2939" };
        switch (activeTab) {
            case "danger": return (
                <tr key={index} style={rowStyle}>
                    <td style={tdStyle}>{item.time}</td>
                    <td style={tdStyle}>{item.sensor}</td>
                    <td style={tdMuted}>{item.threshold}</td>
                    <td style={tdBold}>{item.actual}</td>
                    <td style={{ padding: "12px 8px" }}>{getLevelBadge(item.level)}</td>
                </tr>
            );
            case "sensor": return (
                <tr key={index} style={rowStyle}>
                    <td style={tdStyle}>{item.time}</td>
                    <td style={tdBold}>{item.temp}°C</td>
                    <td style={tdBold}>{item.humi}%</td>
                    <td style={tdBold}>{item.light}%</td>
                    <td style={{ padding: "12px 8px" }}>{getStatusBadge(item.status)}</td>
                </tr>
            );
            case "device": return (
                <tr key={index} style={rowStyle}>
                    <td style={tdStyle}>{item.time}</td>
                    <td style={tdStyle}>{item.device}</td>
                    <td style={tdMuted}>{item.old_value}</td>
                    <td style={tdBold}>{item.new_value}</td>
                    <td style={tdStyle}>{item.actor}</td>
                </tr>
            );
            case "update": return (
                <tr key={index} style={rowStyle}>
                    <td style={tdStyle}>{item.time}</td>
                    <td style={{ ...tdStyle, color: "#00b8db", fontWeight: "500" }}>{item.field}</td>
                    <td style={tdMuted}>{item.old_value}</td>
                    <td style={tdBold}>{item.new_value}</td>
                </tr>
            );
            default: return null;
        }
    };

    return (
        <div className="w-full">
            {/* Tabs */}
            <div style={{ background: "#1a1f2e", borderRadius: "14px", marginBottom: "24px", border: "0.8px solid #1e2939" }}>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "4px", padding: "4px" }}>
                    {Object.entries(TAB_CONFIG).map(([key, cfg]) => (
                        <button key={key}
                            style={{
                                height: "36px", padding: "0 16px", borderRadius: "10px",
                                background: activeTab === key ? "#00b8db" : "transparent",
                                color: activeTab === key ? "white" : "#99a1af",
                                border: "none", cursor: "pointer",
                                fontSize: "14px", fontWeight: "500", transition: "all 0.2s",
                            }}
                            onClick={() => handleTabChange(key)}
                        >
                            {cfg.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Table Container */}
            <div style={{ background: "#1a1f2e", borderRadius: "14px", padding: "24px", border: "0.8px solid #1e2939" }}>

                {/* Title + filter */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
                    <div>
                        <h3 style={{ color: "white", fontSize: "16px", fontWeight: "500", marginBottom: "4px" }}>
                            {TAB_CONFIG[activeTab].label}
                        </h3>
                        <p style={{ color: "#99a1af", fontSize: "14px" }}>
                            {TAB_CONFIG[activeTab].subtitle}
                        </p>
                    </div>
                    {renderFilter()}
                </div>

                {loading ? (
                    <div style={{ textAlign: "center", padding: "40px 0", color: "#99a1af", fontSize: "14px" }}>
                        Đang tải dữ liệu...
                    </div>
                ) : filteredData.length === 0 ? (
                    <div style={{ textAlign: "center", padding: "40px 0", color: "#99a1af", fontSize: "14px" }}>
                        {filter !== "Tất cả" ? `Không có dữ liệu "${filter}"` : "Không có dữ liệu"}
                    </div>
                ) : (
                    <div style={{ overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead>{renderTableHead()}</thead>
                            <tbody>{paginatedData.map((item, i) => renderRow(item, i))}</tbody>
                        </table>
                    </div>
                )}

                {!loading && filteredData.length > 0 && (
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "16px" }}>
                        <button
                            style={{
                                background: "#0f1419", border: "0.8px solid #364153", borderRadius: "8px",
                                padding: "8px 12px", height: "36px", display: "flex", alignItems: "center",
                                gap: "8px", color: "white", fontSize: "14px",
                                cursor: currentPage === 1 ? "not-allowed" : "pointer",
                                opacity: currentPage === 1 ? 0.5 : 1,
                            }}
                            onClick={() => setCurrentPage(p => p - 1)}
                            disabled={currentPage === 1}
                        >
                            <span>←</span><span>Trước</span>
                        </button>

                        <p style={{ color: "#99a1af", fontSize: "14px" }}>
                            Trang {currentPage} / {totalPages}
                            <span style={{ marginLeft: "12px", color: "#364153" }}>
                                ({filteredData.length} bản ghi)
                            </span>
                        </p>

                        <button
                            style={{
                                background: "#0f1419", border: "0.8px solid #364153", borderRadius: "8px",
                                padding: "8px 12px", height: "36px", display: "flex", alignItems: "center",
                                gap: "8px", color: "white", fontSize: "14px",
                                cursor: currentPage === totalPages ? "not-allowed" : "pointer",
                                opacity: currentPage === totalPages ? 0.5 : 1,
                            }}
                            onClick={() => setCurrentPage(p => p + 1)}
                            disabled={currentPage === totalPages}
                        >
                            <span>Tiếp theo</span><span>→</span>
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}