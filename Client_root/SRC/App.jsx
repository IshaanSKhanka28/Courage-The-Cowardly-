import React, { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
import { Info, Sun, MessageSquare, Wind, Droplets, AlertTriangle, RefreshCw, Eye, Sunrise } from "lucide-react";
import ChatPage from "./ChatPage";
import logoImg from "./logo 1.png";

// Hand-Crafted Organic Animated Weather SVG Icons
function AnimatedWeatherIcon({ type, size = 70 }) {
  return (
    <div style={{ width: `${size}px`, height: `${size}px`, display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
      <style>{`
        @keyframes sunRotate {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes sunPeek {
          0%, 100% { transform: translate(-4px, 4px) scale(0.9); opacity: 0.8; }
          40%, 60% { transform: translate(2px, -2px) scale(1.05); opacity: 1; }
        }
        @keyframes organicDrift {
          0%, 100% { transform: translateX(0px); }
          50% { transform: translateX(3px); }
        }
        @keyframes softRain {
          0% { transform: translateY(-8px); opacity: 0; }
          40% { opacity: 0.8; }
          100% { transform: translateY(10px); opacity: 0; }
        }
        @keyframes softPulse {
          0%, 100% { opacity: 0.9; transform: scale(0.98); }
          50% { opacity: 1; transform: scale(1.02); }
        }
        .sun-rotate-anim { animation: sunRotate 20s linear infinite; transform-origin: center; }
        .sun-peek-anim { animation: sunPeek 4.5s ease-in-out infinite; transform-origin: center; }
        .organic-cloud { animation: organicDrift 7s cubic-bezier(0.37, 0, 0.63, 1) infinite; }
        .drop-1 { animation: softRain 1.4s ease-in-out infinite; }
        .drop-2 { animation: softRain 1.4s ease-in-out infinite 0.45s; }
        .organic-moon { animation: softPulse 4s ease-in-out infinite; transform-origin: center; }
      `}</style>

      {(type === "clearSun" || type === "clear") && (
        <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
          <circle cx="32" cy="32" r="12" fill="url(#warmSunGrad)" />
          <g stroke="#FCD34D" strokeWidth="2.5" strokeLinecap="round" className="sun-rotate-anim" style={{ transformOrigin: "32px 32px" }}>
            <path d="M32 4V9" />
            <path d="M32 55V60" />
            <path d="M4 32H9" />
            <path d="M55 32H60" />
            <path d="M12.2 12.2L15.7 15.7" />
            <path d="M48.3 48.3L51.8 51.8" />
            <path d="M12.2 51.8L15.7 48.3" />
            <path d="M48.3 15.7L51.8 12.2" />
          </g>
          <defs>
            <linearGradient id="warmSunGrad" x1="20" y1="20" x2="44" y2="44" gradientUnits="userSpaceOnUse">
              <stop stopColor="#FEF08A" />
              <stop offset="1" stopColor="#F59E0B" />
            </linearGradient>
          </defs>
        </svg>
      )}

      {type === "partlyCloudy" && (
        <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
          <circle cx="21" cy="20" r="10" fill="#FBBF24" className="sun-peek-anim" />
          <path d="M48 44H18C12.4772 44 8 39.5228 8 34C8 29.153 11.4589 25.129 16.0371 24.234C18.6756 18.5714 24.5126 14.5 31.5 14.5C39.7843 14.5 46.6436 20.6973 47.7479 28.7188C50.2872 29.5855 52 31.9961 52 34.8C52 39.8717 47.8717 44 42.8 44H48Z" fill="url(#smoothCloudGrad)" className="organic-cloud" />
          <defs>
            <linearGradient id="smoothCloudGrad" x1="8" y1="14.5" x2="52" y2="44" gradientUnits="userSpaceOnUse">
              <stop stopColor="#FFFFFF" stopOpacity="0.95" />
              <stop offset="1" stopColor="#94A3B8" stopOpacity="0.85" />
            </linearGradient>
          </defs>
        </svg>
      )}

      {(type === "thunderSun" || type === "nightRain") && (
        <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
          <path d="M48 42H18C12.4772 42 8 37.5228 8 32C8 27.153 11.4589 23.129 16.0371 22.234C18.6756 16.5714 24.5126 12.5 31.5 12.5C39.7843 12.5 46.6436 18.6973 47.7479 26.7188C50.2872 27.5855 52 29.9961 52 32.8C52 37.8717 47.8717 42 42.8 42H48Z" fill="#64748B" className="organic-cloud" />
          <path d="M30 42L24.5 50H31L26.5 58" stroke="#38BDF8" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
          <g stroke="#38BDF8" strokeWidth="2.2" strokeLinecap="round">
            <line x1="18" y1="44" x2="18" y2="50" className="drop-1" />
            <line x1="38" y1="44" x2="38" y2="50" className="drop-2" />
          </g>
        </svg>
      )}

      {(type === "clearMoon" || type === "cloudNight") && (
        <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className="organic-moon">
          <path d="M35 14C24.5 14 16 22.5 16 33C16 43.5 24.5 52 35 52C38.2 52 41.2 51.2 43.8 49.8C35.2 48.2 28.8 40.7 28.8 31.8C28.8 24.3 33.1 17.8 39.4 14.8C38 14.3 36.5 14 35 14Z" fill="url(#moonGrad)" />
          <path d="M43 17C43 17 44.5 21 47 22.5C49.5 24 53 24 53 24C53 24 49.5 25.5 47 27C44.5 28.5 43 32.5 43 32.5C43 32.5 41.5 28.5 39 27C36.5 25.5 33 24 33 24C33 24 36.5 22.5 39 21C41.5 19.5 43 17 43 17Z" fill="#FDE047" opacity="0.95" />
          <defs>
            <linearGradient id="moonGrad" x1="16" y1="14" x2="48" y2="52" gradientUnits="userSpaceOnUse">
              <stop stopColor="#E0F2FE" />
              <stop offset="1" stopColor="#38BDF8" />
            </linearGradient>
          </defs>
        </svg>
      )}

      {type === "cloud" && (
        <svg width={size} height={size} viewBox="0 0 64 64" fill="none">
          <path d="M48 45H18C12.4772 45 8 40.5228 8 35C8 30.153 11.4589 26.129 16.0371 25.234C18.6756 19.5714 24.5126 15.5 31.5 15.5C39.7843 15.5 46.6436 21.6973 47.7479 29.7188C50.2872 30.5855 52 32.9961 52 35.8C52 40.8717 47.8717 45 42.8 45H48Z" fill="url(#defaultCloudGrad)" className="organic-cloud" />
          <defs>
            <linearGradient id="defaultCloudGrad" x1="8" y1="15.5" x2="52" y2="45" gradientUnits="userSpaceOnUse">
              <stop stopColor="#F8FAFC" stopOpacity="0.95" />
              <stop offset="1" stopColor="#64748B" stopOpacity="0.85" />
            </linearGradient>
          </defs>
        </svg>
      )}
    </div>
  );
}

function CustomCloud({ width = 140, height = 90 }) {
  return (
    <svg width={width} height={height} viewBox="0 0 200 120" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ mixBlendMode: "overlay" }}>
      <path
        d="M45 105C25.67 105 10 89.33 10 70C10 53.84 21.05 40.1 36.03 36.21C40.64 21.2 54.67 10 71.5 10C91.11 10 107.28 23.95 110.66 42.19C116.51 39.53 123.14 38 130 38C155.95 38 177 59.05 177 85C177 100.46 164.46 113 149 113H45C37.27 113 31 106.73 31 99C31 91.27 37.27 85 45 85H149"
        fill="#ffffff"
        fillOpacity="0.75"
      />
    </svg>
  );
}

// Custom Animated SVG Line Chart Component
function AnimatedLineChart({ data, color = "#38bdf8", height = 110 }) {
  const max = Math.max(...data.values);
  const min = Math.min(...data.values);
  const range = max - min || 1;
  const width = 320;
  
  const points = data.values.map((val, idx) => {
    const x = (idx / (data.values.length - 1)) * (width - 20) + 10;
    const y = height - 20 - ((val - min) / range) * (height - 40);
    return { x, y, label: data.labels[idx], val };
  });

  const pathD = points.reduce((acc, pt, idx) => idx === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`, "");
  const fillD = `${pathD} L ${points[points.length - 1].x} ${height} L ${points[0].x} ${height} Z`;

  return (
    <div style={{ width: "100%", height: `${height}px`, position: "relative" }}>
      <style>{`
        @keyframes drawLine {
          0% { stroke-dashoffset: 400; }
          100% { stroke-dashoffset: 0; }
        }
        @keyframes fadeInArea {
          0% { opacity: 0; transform: translateY(5px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .animated-path {
          stroke-dasharray: 400;
          animation: drawLine 2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .animated-area {
          animation: fadeInArea 1.5s ease-out forwards;
        }
      `}</style>
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} style={{ overflow: "visible" }}>
        <defs>
          <linearGradient id={`grad-${color.replace('#','')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.4" />
            <stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </linearGradient>
        </defs>
        <path d={fillD} fill={`url(#grad-${color.replace('#','')})`} className="animated-area" />
        <path d={pathD} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="animated-path" />
        {points.map((pt, i) => (
          <g key={i}>
            <text x={pt.x} y={height - 2} fill="#94a3b8" fontSize="10" textAnchor="middle" fontFamily="Inter, sans-serif">{pt.label}</text>
          </g>
        ))}
      </svg>
    </div>
  );
}

// Custom Animated SVG Bar Chart Component
function AnimatedBarChart({ data, color = "#38bdf8", height = 75 }) {
  const max = Math.max(...data.values) || 1;
  const width = 320;
  const barWidth = 28;
  const gap = (width - barWidth * data.values.length) / (data.values.length + 1);

  return (
    <div style={{ width: "100%", height: `${height}px`, position: "relative" }}>
      <style>{`
        @keyframes growBar {
          0% { transform: scaleY(0); }
          100% { transform: scaleY(1); }
        }
        .animated-bar {
          animation: growBar 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          transform-origin: bottom;
        }
      `}</style>
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} style={{ overflow: "visible" }}>
        {data.values.map((val, i) => {
          const barH = Math.max((val / max) * (height - 22), 6);
          const x = gap + i * (barWidth + gap);
          const y = height - barH - 16;
          return (
            <g key={i}>
              <rect x={x} y={y} width={barWidth} height={barH} rx="6" fill={color} fillOpacity="0.75" stroke={color} strokeWidth="1" className="animated-bar" style={{ animationDelay: `${i * 0.15}s` }} />
              <text x={x + barWidth / 2} y={height - 2} fill="#94a3b8" fontSize="10" textAnchor="middle" fontFamily="Inter, sans-serif">{data.labels[i]}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// 1. Weather & Risks Website Dashboard Page
function WeatherPage() {
  const [loading, setLoading] = useState(false);
  
  const weatherStates = [
    { 
      location: "San Francisco",
      country: "California",
      temp: "63°", 
      unit: "F",
      condition: "Partly Cloudy", 
      heroIcon: "clearSun",
      windSpeedNum: 10,
      wind: "10 mph NE", 
      humidity: 58, 
      uvIndexNum: 5,
      uvIndex: "5 (Moderate)",
      visibility: 10,
      visibilityStr: "10 mi",
      sunrise: "06:42 AM",
      sunset: "07:55 PM",
      status: "Optimal Atmospheric Conditions",
      bgGradient: "linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%)",
      cardBg: "linear-gradient(135deg, rgba(30, 27, 75, 0.75) 0%, rgba(49, 46, 129, 0.65) 100%)",
      hourly: [
        { time: "Now", temp: "63°", icon: "clearSun", precip: "0%" }, 
        { time: "18:00", temp: "64°", icon: "partlyCloudy", precip: "5%" }, 
        { time: "19:00", temp: "65°", icon: "partlyCloudy", precip: "10%" },
        { time: "20:00", temp: "64°", icon: "cloud", precip: "15%" },
        { time: "21:00", temp: "62°", icon: "clearMoon", precip: "0%" },
        { time: "22:00", temp: "60°", icon: "clearMoon", precip: "0%" }
      ],
      humidityData: { labels: ['16:00', '17:00', '18:00', '19:00', '20:00', '21:00'], values: [53, 55, 56, 57, 58, 58] },
      windData: { labels: ['16:00', '17:00', '18:00', '19:00', '20:00', '21:00'], values: [8, 9, 12, 10, 7, 10] },
      sunData: { labels: ['04:00', '07:00', '10:00', '13:00', '16:00', '19:00', '22:00'], values: [0, 25, 80, 100, 80, 25, 0] }
    },
    { 
      location: "Minsk",
      country: "Belarus",
      temp: "59°", 
      unit: "F",
      condition: "Stormy & Heavy Rain", 
      heroIcon: "thunderSun",
      windSpeedNum: 32,
      wind: "32 mph SW", 
      humidity: 92, 
      uvIndexNum: 1,
      uvIndex: "1 (Low)",
      visibility: 2,
      visibilityStr: "2 mi",
      sunrise: "05:15 AM",
      sunset: "09:10 PM",
      status: "Severe Weather Warning: High Wind & Storms",
      bgGradient: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)",
      cardBg: "linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.7) 100%)",
      hourly: [
        { time: "Now", temp: "59°", icon: "thunderSun", precip: "90%" },
        { time: "18:00", temp: "58°", icon: "nightRain", precip: "95%" },
        { time: "19:00", temp: "57°", icon: "nightRain", precip: "80%" },
        { time: "20:00", temp: "56°", icon: "cloudNight", precip: "40%" },
        { time: "21:00", temp: "55°", icon: "clearMoon", precip: "20%" },
        { time: "22:00", temp: "54°", icon: "clearMoon", precip: "10%" }
      ],
      humidityData: { labels: ['16:00', '17:00', '18:00', '19:00', '20:00', '21:00'], values: [88, 90, 91, 92, 92, 90] },
      windData: { labels: ['16:00', '17:00', '18:00', '19:00', '20:00', '21:00'], values: [26, 28, 35, 32, 30, 32] },
      sunData: { labels: ['04:00', '07:00', '10:00', '13:00', '16:00', '19:00', '22:00'], values: [0, 15, 50, 70, 50, 15, 0] }
    }
  ];
  
  const [metrics, setMetrics] = useState(weatherStates[0]);

  const baseSpeedFactor = 300;
  const animDuration1 = Math.max(3, (baseSpeedFactor / metrics.windSpeedNum) * 0.8).toFixed(1);
  const animDuration2 = Math.max(4, (baseSpeedFactor / metrics.windSpeedNum) * 1.1).toFixed(1);
  const animDuration3 = Math.max(2.5, (baseSpeedFactor / metrics.windSpeedNum) * 0.65).toFixed(1);
  const animDuration4 = Math.max(3.5, (baseSpeedFactor / metrics.windSpeedNum) * 0.95).toFixed(1);

  const refreshData = () => {
    setLoading(true);
    setTimeout(() => {
      const currentIndex = weatherStates.findIndex(w => w.location === metrics.location);
      const nextIndex = (currentIndex + 1) % weatherStates.length;
      setMetrics(weatherStates[nextIndex]);
      setLoading(false);
    }, 300);
  };

  return (
    <div style={{ fontFamily: "'Inter', 'Plus Jakarta Sans', sans-serif", color: "#f8fafc" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700&display=swap');

        @keyframes cloudDriftFromMatrix {
          0% { transform: translateX(100px); opacity: 0; }
          20% { opacity: 0.85; }
          80% { opacity: 0.85; }
          100% { transform: translateX(580px); opacity: 0; }
        }
        .cloud-anim-1 { position: absolute; top: -10px; left: 80px; animation: cloudDriftFromMatrix ${animDuration1}s linear infinite; }
        .cloud-anim-2 { position: absolute; bottom: -20px; left: 180px; animation: cloudDriftFromMatrix ${animDuration2}s linear infinite; animation-delay: -4s; }
        .cloud-anim-3 { position: absolute; top: 20px; left: 320px; animation: cloudDriftFromMatrix ${animDuration3}s linear infinite; animation-delay: -2s; }
        .cloud-anim-4 { position: absolute; bottom: 10px; left: 420px; animation: cloudDriftFromMatrix ${animDuration4}s linear infinite; animation-delay: -7s; }
      `}</style>

      {/* Hero Header Banner */}
      <div style={{
        background: metrics.bgGradient,
        borderRadius: "28px",
        padding: "40px",
        boxShadow: "0 20px 35px -5px rgba(0,0,0,0.4)",
        marginBottom: "28px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "24px",
        position: "relative",
        overflow: "hidden",
        border: "1px solid rgba(255,255,255,0.12)",
        transition: "background 0.5s ease"
      }}>
        <div className="cloud-anim-1" style={{ pointerEvents: "none" }}><CustomCloud width={110} height={75} /></div>
        <div className="cloud-anim-2" style={{ pointerEvents: "none" }}><CustomCloud width={150} height={95} /></div>
        <div className="cloud-anim-3" style={{ pointerEvents: "none" }}><CustomCloud width={90} height={60} /></div>
        <div className="cloud-anim-4" style={{ pointerEvents: "none" }}><CustomCloud width={130} height={85} /></div>

        <div style={{ position: "relative", zIndex: 2 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <span style={{ fontSize: "11px", fontWeight: "600", letterSpacing: "0.08em", textTransform: "uppercase", background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", padding: "5px 12px", borderRadius: "999px", border: "1px solid rgba(56, 189, 248, 0.3)" }}>Live Telemetry</span>
          </div>
          <h1 style={{ fontFamily: "'Outfit', sans-serif", fontSize: "38px", fontWeight: "700", margin: "0 0 6px 0", letterSpacing: "-0.02em" }}>{metrics.location}</h1>
          <p style={{ fontSize: "15px", opacity: 0.8, margin: 0, fontWeight: "500" }}>{metrics.country} • {metrics.condition}</p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "24px", position: "relative", zIndex: 2 }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontFamily: "'Helvetica Neue', sans-serif", fontSize: "48px", fontWeight: 500, lineHeight: "1" }}>{metrics.temp}</div>
            <div style={{ fontSize: "12px", opacity: 0.7, marginTop: "6px", fontWeight: "500" }}>Wind: {metrics.wind}</div>
          </div>
          <button onClick={refreshData} disabled={loading} style={{ background: "rgba(255,255,255,0.12)", color: "white", border: "1px solid rgba(255,255,255,0.2)", padding: "12px 18px", borderRadius: "14px", fontWeight: "600", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", backdropFilter: "blur(6px)" }}>
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} /> {loading ? "Switching..." : "Simulate City"}
          </button>
        </div>
      </div>

      {/* Hourly Forecast Strip */}
      <div style={{ background: metrics.cardBg, backdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "24px", padding: "24px", marginBottom: "28px", boxShadow: "0 10px 25px rgba(0,0,0,0.3)" }}>
        <h3 style={{ fontSize: "11px", fontWeight: "600", color: "#38bdf8", textTransform: "uppercase", margin: "0 0 16px 0", letterSpacing: "0.1em" }}>Hourly Forecast & Precipitation Curve</h3>
        <div style={{ display: "flex", gap: "16px", overflowX: "auto", paddingBottom: "6px" }}>
          {metrics.hourly.map((hr, idx) => (
            <div key={idx} style={{ flex: "0 0 135px", background: idx === 0 ? "rgba(56, 189, 248, 0.12)" : "rgba(255, 255, 255, 0.03)", border: idx === 0 ? "1px solid rgba(56, 189, 248, 0.35)" : "1px solid rgba(255, 255, 255, 0.06)", borderRadius: "18px", padding: "18px 12px", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "12px", fontWeight: "500", color: "#94a3b8" }}>{hr.time}</span>
              <AnimatedWeatherIcon type={hr.icon} size={70} />
              <span style={{ fontFamily: "'Helvetica Neue', sans-serif", fontSize: "17px", fontWeight: 500, color: "#f8fafc" }}>{hr.temp}</span>
              <span style={{ fontSize: "11px", fontWeight: 500, color: "#38bdf8", background: "rgba(56, 189, 248, 0.15)", padding: "3px 8px", borderRadius: "999px", fontFamily: "'Helvetica Neue', sans-serif" }}>{hr.precip}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Grid Layout Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1.2fr", gap: "24px", marginBottom: "28px" }}>
        
        {/* Left Column Stack */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          
          {/* 1. HUMIDITY CARD */}
          <div style={{ background: metrics.cardBg, backdropFilter: "blur(12px)", border: "1px solid rgba(56, 189, 248, 0.25)", borderRadius: "28px", padding: "28px", display: "flex", flexDirection: "column", justifyContent: "space-between", boxShadow: "0 15px 35px rgba(0, 0, 0, 0.3)" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{ width: "36px", height: "36px", borderRadius: "50%", background: "radial-gradient(circle, rgba(56, 189, 248, 0.3) 0%, rgba(56, 189, 248, 0) 70%)", display: "flex", alignItems: "center", justifyContent: "center", color: "#38bdf8" }}>
                    <Droplets size={18} />
                  </div>
                  <span style={{ fontSize: "0.9rem", fontWeight: 600, color: "#38bdf8", textTransform: "uppercase", letterSpacing: "0.06em" }}>Humidity</span>
                </div>
                <span style={{ fontSize: "1.7rem", fontWeight: 500, fontFamily: "'Helvetica Neue', sans-serif" }}>{metrics.humidity}%</span>
              </div>
              <p style={{ fontSize: "0.85rem", color: "#94a3b8", margin: "0 0 16px 0", lineHeight: "1.5" }}>Moisture saturation is high. Atmospheric stability is maintained.</p>
            </div>
            <AnimatedLineChart data={metrics.humidityData} color="#38bdf8" height={100} />
          </div>

          {/* Lower Left Split Row: Visibility & Wind Speed */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
            
            {/* VISIBILITY CARD */}
            <div style={{ background: metrics.cardBg, backdropFilter: "blur(12px)", border: "1px solid rgba(168, 85, 247, 0.25)", borderRadius: "28px", padding: "24px", display: "flex", flexDirection: "column", justifyContent: "space-between", boxShadow: "0 15px 35px rgba(0, 0, 0, 0.3)" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
                  <div style={{ width: "34px", height: "34px", borderRadius: "50%", background: "radial-gradient(circle, rgba(168, 85, 247, 0.3) 0%, rgba(168, 85, 247, 0) 70%)", display: "flex", alignItems: "center", justifyContent: "center", color: "#c084fc" }}>
                    <Eye size={17} />
                  </div>
                  <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "#c084fc", textTransform: "uppercase", letterSpacing: "0.06em" }}>Visibility</span>
                </div>
                <div style={{ fontSize: "1.8rem", fontWeight: 500, fontFamily: "'Helvetica Neue', sans-serif", marginBottom: "4px" }}>{metrics.visibility} mi</div>
                <div style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Clear path line of sight.</div>
              </div>
            </div>

            {/* WIND SPEED CARD */}
            <div style={{ background: metrics.cardBg, backdropFilter: "blur(12px)", border: "1px solid rgba(56, 189, 248, 0.25)", borderRadius: "28px", padding: "24px", display: "flex", flexDirection: "column", justifyContent: "space-between", boxShadow: "0 15px 35px rgba(0, 0, 0, 0.3)" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
                  <div style={{ width: "34px", height: "34px", borderRadius: "50%", background: "radial-gradient(circle, rgba(56, 189, 248, 0.3) 0%, rgba(56, 189, 248, 0) 70%)", display: "flex", alignItems: "center", justifyContent: "center", color: "#38bdf8" }}>
                    <Wind size={17} />
                  </div>
                  <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "#38bdf8", textTransform: "uppercase", letterSpacing: "0.06em" }}>Wind Speed</span>
                </div>
                <div style={{ fontSize: "1.6rem", fontWeight: 500, fontFamily: "'Helvetica Neue', sans-serif", marginBottom: "4px" }}>{metrics.windSpeedNum} <span style={{ fontSize: "1rem", color: "#94a3b8" }}>mph</span></div>
              </div>
              <AnimatedBarChart data={metrics.windData} color="#38bdf8" height={65} />
            </div>

          </div>

        </div>

        {/* Right Column Stack */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          
          {/* UV INDEX CARD */}
          <div style={{ background: metrics.cardBg, backdropFilter: "blur(12px)", border: "1px solid rgba(251, 191, 36, 0.25)", borderRadius: "28px", padding: "28px", display: "flex", flexDirection: "column", justifyContent: "space-between", boxShadow: "0 15px 35px rgba(0, 0, 0, 0.3)" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                <div style={{ width: "36px", height: "36px", borderRadius: "50%", background: "radial-gradient(circle, rgba(251, 191, 36, 0.3) 0%, rgba(251, 191, 36, 0) 70%)", display: "flex", alignItems: "center", justifyContent: "center", color: "#fbbf24" }}>
                  <Sun size={18} />
                </div>
                <span style={{ fontSize: "0.9rem", fontWeight: 600, color: "#fbbf24", textTransform: "uppercase", letterSpacing: "0.06em" }}>UV Index</span>
              </div>
              <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginBottom: "12px" }}>
                <span style={{ fontSize: "2.4rem", fontWeight: 500, fontFamily: "'Helvetica Neue', sans-serif" }}>{metrics.uvIndex.split(" ")[0]}</span>
                <span style={{ fontSize: "1.1rem", fontWeight: 600, color: "#4ade80" }}>{metrics.uvIndex.split("(")[1] || "Low)"}</span>
              </div>
              <p style={{ fontSize: "0.85rem", color: "#94a3b8", margin: 0, lineHeight: "1.5" }}>Sun protection recommended during midday hours.</p>
            </div>
            <div style={{ marginTop: "24px" }}>
              <div style={{ width: "100%", height: "8px", background: "rgba(255, 255, 255, 0.08)", borderRadius: "4px", overflow: "hidden" }}>
                <div style={{ height: "100%", background: "linear-gradient(135deg, #4ade80 0%, #fbbf24 50%, #f43f5e 100%)", borderRadius: "4px", width: `${Math.min(metrics.uvIndexNum * 12, 100)}%`, transition: "width 1s ease" }}></div>
              </div>
            </div>
          </div>

          {/* SUNRISE & SUNSET CARD */}
          <div style={{ background: metrics.cardBg, backdropFilter: "blur(12px)", border: "1px solid rgba(251, 191, 36, 0.3)", borderRadius: "28px", padding: "28px", display: "flex", flexDirection: "column", justifyContent: "space-between", boxShadow: "0 15px 35px rgba(0, 0, 0, 0.3)", flex: 1 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                <div style={{ width: "36px", height: "36px", borderRadius: "50%", background: "radial-gradient(circle, rgba(251, 191, 36, 0.3) 0%, rgba(251, 191, 36, 0) 70%)", display: "flex", alignItems: "center", justifyContent: "center", color: "#fbbf24" }}>
                  <Sunrise size={18} />
                </div>
                <span style={{ fontSize: "0.9rem", fontWeight: 600, color: "#fbbf24", textTransform: "uppercase", letterSpacing: "0.06em" }}>Sunrise & Sunset</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "16px", background: "rgba(255, 255, 255, 0.04)", padding: "14px 18px", borderRadius: "16px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                <div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8", textTransform: "uppercase", marginBottom: "4px" }}>Sunrise</div>
                  <div style={{ fontSize: "1.2rem", fontWeight: 500, fontFamily: "'Helvetica Neue', sans-serif", color: "#fef08a" }}>{metrics.sunrise}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8", textTransform: "uppercase", marginBottom: "4px" }}>Sunset</div>
                  <div style={{ fontSize: "1.2rem", fontWeight: 500, fontFamily: "'Helvetica Neue', sans-serif", color: "#fde047" }}>{metrics.sunset}</div>
                </div>
              </div>
            </div>
            <AnimatedLineChart data={metrics.sunData} color="#fbbf24" height={85} />
          </div>

        </div>

      </div>

     {/* Alert Banner wrapped cleanly */}
      <div style={{ marginTop: "24px" }}>
        {(() => {
          const isSevere = metrics.windSpeedNum > 25 || metrics.humidity > 85;
          const alertBg = isSevere ? "rgba(239, 68, 68, 0.1)" : "rgba(34, 197, 94, 0.1)";
          const alertBorder = isSevere ? "rgba(239, 68, 68, 0.3)" : "rgba(34, 197, 94, 0.3)";
          const alertColor = isSevere ? "#ef4444" : "#4ade80";
          const alertText = isSevere ? "#fca5a5" : "#86efac";

          return (
            <div style={{ background: alertBg, border: `1px solid ${alertBorder}`, padding: "20px 24px", borderRadius: "20px", display: "flex", alignItems: "center", gap: "16px" }}>
              <AlertTriangle size={22} style={{ color: alertColor, flexShrink: 0 }} />
              <div>
                <h4 style={{ fontSize: "14px", fontWeight: "600", color: alertColor, margin: "0 0 2px 0" }}>Advisory Notice</h4>
                <p style={{ fontSize: "13px", color: alertText, margin: 0, opacity: 0.9, fontWeight: "500" }}>{metrics.status}</p>
              </div>
            </div>
          );
        })()}
      </div>

    </div>
  );
}

// 2. About Page Component
function AboutPage() {
  return (
    <div style={{ fontFamily: "'Inter', sans-serif", color: "#f8fafc" }}>
      <div style={{ background: "linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)", border: "1px solid rgba(56, 189, 248, 0.25)", padding: "36px", borderRadius: "28px", boxShadow: "0 20px 35px rgba(0,0,0,0.3)" }}>
        <span style={{ fontSize: "11px", fontWeight: "600", letterSpacing: "0.08em", color: "#38bdf8", background: "rgba(56, 189, 248, 0.15)", padding: "5px 12px", borderRadius: "999px", textTransform: "uppercase" }}>Project Aeris</span>
        <h1 style={{ fontFamily: "'Outfit', sans-serif", fontSize: "32px", fontWeight: "700", color: "#f8fafc", margin: "16px 0 8px 0", letterSpacing: "-0.02em" }}>Grounding Weather in Real-World Impact</h1>
        <p style={{ fontSize: "16px", color: "#cbd5e1", margin: "0 0 24px 0", fontWeight: "500", lineHeight: "1.6" }}>
          Aeris bridges live telemetry forecasts with official municipal advisories to provide safe, verified guidance. By integrating real-time atmospheric indices, precipitation curves, and dynamic risk assessments, our platform empowers users to make informed daily travel and safety decisions.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px", marginTop: "24px" }}>
          <div style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "20px", borderRadius: "16px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: "600", color: "#38bdf8", margin: "0 0 8px 0" }}>Live Telemetry</h3>
            <p style={{ fontSize: "13px", color: "#94a3b8", margin: 0, lineHeight: "1.5" }}>High-precision meteorological data streams across multiple global regions.</p>
          </div>
          <div style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "20px", borderRadius: "16px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: "600", color: "#38bdf8", margin: "0 0 8px 0" }}>AI Risk Assistant</h3>
            <p style={{ fontSize: "13px", color: "#94a3b8", margin: 0, lineHeight: "1.5" }}>Context-aware intelligent responses tailored to localized safety hazards.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Sidebar Navigation Item Component
function SidebarItem({ to, icon: Icon, label, isExpanded }) {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "14px",
        padding: "12px 14px",
        borderRadius: "12px",
        textDecoration: "none",
        fontWeight: "500",
        fontSize: "13px",
        backgroundColor: isActive ? "rgba(56, 189, 248, 0.15)" : "transparent",
        color: isActive ? "#38bdf8" : "#94a3b8",
        border: isActive ? "1px solid rgba(56, 189, 248, 0.3)" : "1px solid transparent",
        transition: "all 0.2s ease"
      }}
    >
      <Icon size={18} style={{ flexShrink: "0", color: isActive ? "#38bdf8" : "#94a3b8" }} />
      <span style={{ whiteSpace: "nowrap", opacity: isExpanded ? 1 : 0, transition: "opacity 0.2s" }}>
        {label}
      </span>
    </Link>
  );
}

// Main App Layout Shell
export default function App() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div style={{ display: "flex", height: "100vh", width: "100vw", overflow: "hidden", backgroundColor: "#090d16", fontFamily: "'Inter', sans-serif" }}>
      <aside
        onMouseEnter={() => setIsExpanded(true)}
        onMouseLeave={() => setIsExpanded(false)}
        style={{
          height: "100%",
          width: isExpanded ? "250px" : "76px",
          backgroundColor: "#0f172a",
          borderRight: "1px solid rgba(255,255,255,0.06)",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "36px 14px 24px 14px",
          transition: "width 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
          zIndex: 30,
          boxShadow: "10px 0 30px rgba(0, 0, 0, 0.3)",
          userSelect: "none",
          flexShrink: 0,
          boxSizing: "border-box"
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "4px", marginBottom: "32px" }}>
            <div style={{ width: "38px", height: "38px", borderRadius: "10px", overflow: "hidden", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <img src={logoImg} alt="Aeris Logo" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>
            <div style={{ overflow: "hidden", whiteSpace: "nowrap", opacity: isExpanded ? 1 : 0, transition: "opacity 0.2s" }}>
              <h1 style={{ fontFamily: "'Outfit', sans-serif", fontSize: "16px", fontWeight: "700", color: "#f8fafc", margin: 0, letterSpacing: "0.03em" }}>AERIS</h1>
              <p style={{ fontSize: "9px", fontWeight: "600", color: "#38bdf8", margin: 0, textTransform: "uppercase", letterSpacing: "0.12em" }}>Risk System</p>
            </div>
          </div>

          <nav style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <SidebarItem to="/about" icon={Info} label="About Project" isExpanded={isExpanded} />
            <SidebarItem to="/weather" icon={Sun} label="Weather & Risks" isExpanded={isExpanded} />
            <SidebarItem to="/chat" icon={MessageSquare} label="Chatbot AI" isExpanded={isExpanded} />
          </nav>
        </div>

        <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "16px", display: "flex", alignItems: "center", gap: "12px", paddingLeft: "6px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#38bdf8", flexShrink: "0", boxShadow: "0 0 10px #38bdf8" }} />
          <div style={{ overflow: "hidden", whiteSpace: "nowrap", opacity: isExpanded ? 1 : 0, transition: "opacity 0.2s" }}>
            <span style={{ fontSize: "10px", fontWeight: "600", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em" }}>System Live</span>
          </div>
        </div>
      </aside>

      <main style={{ flex: 1, minHeight: 0, height: "100%", overflowY: "auto", background: "radial-gradient(circle at top right, #1e1b4b 0%, #090d16 60%)", boxSizing: "border-box" }}>
        <div style={{ maxWidth: "1140px", margin: "0 auto", width: "100%", padding: "56px 40px 40px 40px", boxSizing: "border-box" }}>
          <Routes>
            <Route path="/" element={<Navigate to="/about" replace />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/weather" element={<WeatherPage />} />
            <Route path="/chat" element={<ChatPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
