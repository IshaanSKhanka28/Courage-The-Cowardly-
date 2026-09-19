import React, { useState } from "react";
import { Sun, Wind, Droplets, RefreshCw, AlertTriangle, Cloud, CloudRain, Zap, Eye, Gauge } from "lucide-react";

// Reusable SVG Weather Icon Component (using your custom SVG logic)
function WeatherIcon({ type }) {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {type === "sun" && (
        <>
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41" />
        </>
      )}
      {type === "cloud" && (
        <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" />
      )}
      {type === "rain" && (
        <>
          <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" />
          <path d="M8 16l-1 2m4-2l-1 2m4-2l-1 2" />
        </>
      )}
      {type === "thunder" && (
        <>
          <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" />
          <path d="M13 13l-3 5h4l-3 5" />
        </>
      )}
    </svg>
  );
}

export default function WeatherPage() {
  const [loading, setLoading] = useState(false);
  
  const weatherConditions = [
    { 
      temp: "32°C", 
      condition: "Clear Blue Skies", 
      wind: "8 km/h NE", 
      humidity: "65%", 
      uvIndex: "6 (High)",
      visibility: "10 km",
      pressure: "1013 hPa",
      status: "Optimal Conditions",
      bgGradient: "linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)",
      cloudOpacity: 0.4,
      cloudSpeed: "25s",
      hourly: [
        { time: "Now", temp: "32°", icon: "sun", precip: "0%" },
        { time: "5 PM", temp: "31°", icon: "sun", precip: "0%" },
        { time: "6 PM", temp: "29°", icon: "cloud", precip: "5%" },
        { time: "7 PM", temp: "28°", icon: "cloud", precip: "10%" },
        { time: "8 PM", temp: "27°", icon: "cloud", precip: "10%" },
        { time: "9 PM", temp: "26°", icon: "sun", precip: "0%" },
        { time: "10 PM", temp: "25°", icon: "sun", precip: "0%" }
      ]
    },
    { 
      temp: "28°C", 
      condition: "Overcast and Gloomy", 
      wind: "15 km/h N", 
      humidity: "88%", 
      uvIndex: "2 (Low)",
      visibility: "4 km",
      pressure: "1008 hPa",
      status: "Low Visibility Alert",
      bgGradient: "linear-gradient(135deg, #475569 0%, #64748b 100%)",
      cloudOpacity: 0.7,
      cloudSpeed: "15s",
      hourly: [
        { time: "Now", temp: "28°", icon: "cloud", precip: "40%" },
        { time: "5 PM", temp: "28°", icon: "cloud", precip: "45%" },
        { time: "6 PM", temp: "27°", icon: "rain", precip: "65%" },
        { time: "7 PM", temp: "26°", icon: "rain", precip: "80%" },
        { time: "8 PM", temp: "26°", icon: "cloud", precip: "50%" },
        { time: "9 PM", temp: "25°", icon: "cloud", precip: "30%" },
        { time: "10 PM", temp: "25°", icon: "cloud", precip: "20%" }
      ]
    },
    { 
      temp: "24°C", 
      condition: "Heavy Thunderstorm", 
      wind: "35 km/h SW", 
      humidity: "98%", 
      uvIndex: "1 (Very Low)",
      visibility: "1.5 km",
      pressure: "995 hPa",
      status: "Severe Weather Warning: Seek Shelter",
      bgGradient: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
      cloudOpacity: 0.9,
      cloudSpeed: "8s",
      hourly: [
        { time: "Now", temp: "24°", icon: "thunder", precip: "95%" },
        { time: "5 PM", temp: "23°", icon: "thunder", precip: "100%" },
        { time: "6 PM", temp: "23°", icon: "rain", precip: "90%" },
        { time: "7 PM", temp: "24°", icon: "rain", precip: "75%" },
        { time: "8 PM", temp: "25°", icon: "cloud", precip: "40%" },
        { time: "9 PM", temp: "25°", icon: "cloud", precip: "20%" },
        { time: "10 PM", temp: "26°", icon: "sun", precip: "10%" }
      ]
    }
  ];
  
  const [metrics, setMetrics] = useState(weatherConditions[0]);

  const refreshData = () => {
    setLoading(true);
    setTimeout(() => {
      const currentIndex = weatherConditions.findIndex(w => w.condition === metrics.condition);
      const nextIndex = (currentIndex + 1) % weatherConditions.length;
      setMetrics(weatherConditions[nextIndex]);
      setLoading(false);
    }, 600);
  };

  return (
    <div style={{ padding: "40px", fontFamily: "system-ui, sans-serif" }}>
      
      {/* CSS Animation for Infinite Marquee Clouds */}
      <style>{`
        @keyframes seamlessMarquee {
          0% { transform: translateX(0%); }
          100% { transform: translateX(-50%); }
        }
        .cloud-marquee-track {
          display: flex;
          width: 200%;
          animation: seamlessMarquee ${metrics.cloudSpeed} linear infinite;
          will-change: transform;
        }
      `}</style>

      {/* Weather Banner */}
      <div style={{
        position: "relative",
        background: metrics.bgGradient,
        borderRadius: "28px",
        padding: "40px",
        color: "white",
        overflow: "hidden",
        boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
        transition: "background 0.6s ease-in-out",
        marginBottom: "24px",
        height: "200px",
        display: "flex",
        alignItems: "center"
      }}>
        
        {/* Vector Animated Clouds Container */}
        <div style={{
          position: "absolute",
          top: 0,
          right: 0,
          width: "55%",
          height: "100%",
          overflow: "hidden",
          pointerEvents: "none",
          opacity: metrics.cloudOpacity,
          transition: "opacity 0.5s ease",
          maskImage: "linear-gradient(to right, transparent 0%, black 15%, black 85%, transparent 100%)",
          WebkitMaskImage: "linear-gradient(to right, transparent 0%, black 15%, black 85%, transparent 100%)"
        }}>
          <div className="cloud-marquee-track" style={{ height: "100%", position: "relative" }}>
            
            {/* Cloud Loop Segment 1 */}
            <div style={{ display: "flex", width: "50%", height: "100%", position: "relative", alignItems: "center" }}>
              <div style={{ position: "absolute", top: "15px", left: "10%" }}>
                <svg width="120" height="70" viewBox="0 0 200 120" fill="currentColor">
                  <path d="M55 110C31.804 110 13 91.196 13 68C13 47.74 27.53 30.73 46.85 26.62C55.44 11.23 71.86 1 91 1C122.538 1 148 26.462 148 58C148 60.15 147.83 62.27 147.5 64.35C158.42 66.33 166.5 75.87 166.5 87.25C166.5 100.1 156.1 110 143.25 110H55Z" />
                </svg>
              </div>
            </div>

            {/* Cloud Loop Segment 2 */}
            <div style={{ display: "flex", width: "50%", height: "100%", position: "relative", alignItems: "center" }}>
              <div style={{ position: "absolute", top: "15px", left: "10%" }}>
                <svg width="120" height="70" viewBox="0 0 200 120" fill="currentColor">
                  <path d="M55 110C31.804 110 13 91.196 13 68C13 47.74 27.53 30.73 46.85 26.62C55.44 11.23 71.86 1 91 1C122.538 1 148 26.462 148 58C148 60.15 147.83 62.27 147.5 64.35C158.42 66.33 166.5 75.87 166.5 87.25C166.5 100.1 156.1 110 143.25 110H55Z" />
                </svg>
              </div>
            </div>

          </div>
        </div>

        {/* Card Text & Button */}
        <div style={{ position: "relative", zIndex: 2, display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%", gap: "20px" }}>
          <div>
            <span style={{ fontSize: "11px", fontWeight: "700", textTransform: "uppercase", letterSpacing: "0.08em", background: "rgba(255,255,255,0.2)", padding: "4px 12px", borderRadius: "999px" }}>
              Custom Simulation
            </span>
            <h1 style={{ fontSize: "36px", fontWeight: "900", margin: "12px 0 6px 0", letterSpacing: "-0.02em" }}>
              Atmospheric Risk Matrix
            </h1>
            <p style={{ fontSize: "15px", opacity: 0.9, margin: 0 }}>
              {metrics.temp} • {metrics.condition}
            </p>
          </div>

          <button 
            onClick={refreshData} 
            disabled={loading} 
            style={{ 
              background: "rgba(255, 255, 255, 0.2)", 
              color: "white", 
              border: "1px solid rgba(255, 255, 255, 0.4)", 
              padding: "12px 20px", 
              borderRadius: "14px", 
              fontWeight: "600", 
              cursor: "pointer", 
              display: "flex", 
              alignItems: "center", 
              gap: "8px",
              backdropFilter: "blur(6px)"
            }}
          >
            <RefreshCw size={18} className={loading ? "animate-spin" : ""} /> 
            {loading ? "Updating..." : "Simulate Shift"}
          </button>
        </div>
      </div>

      {/* Google Weather Hourly Forecast Strip */}
      <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: "24px", padding: "20px 24px", marginBottom: "24px", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.02)" }}>
        <h3 style={{ fontSize: "13px", fontWeight: "700", color: "#64748b", textTransform: "uppercase", margin: "0 0 16px 0", letterSpacing: "0.5px" }}>Hourly Forecast & Precipitation</h3>
        <div style={{ display: "flex", gap: "16px", overflowX: "auto", paddingBottom: "4px" }}>
          {metrics.hourly.map((hr, idx) => (
            <div key={idx} style={{ flex: "0 0 85px", background: idx === 0 ? "#f0fdf4" : "#f8fafc", border: idx === 0 ? "1px solid #bbf7d0" : "1px solid #f1f5f9", borderRadius: "16px", padding: "14px 10px", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "12px", fontWeight: "600", color: "#64748b" }}>{hr.time}</span>
              
              <div style={{ color: idx === 0 ? "#0d9488" : "#3b82f6", display: "flex", alignItems: "center", justifyContent: "center", height: "32px" }}>
                <WeatherIcon type={hr.icon} />
              </div>

              <span style={{ fontSize: "16px", fontWeight: "800", color: "#1e293b" }}>{hr.temp}</span>
              <span style={{ fontSize: "11px", fontWeight: "600", color: "#0284c7", background: "#e0f2fe", padding: "2px 6px", borderRadius: "999px" }}>{hr.precip}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Metrics Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "20px", marginBottom: "28px" }}>
        <MetricCard icon={Sun} label="TEMPERATURE" value={metrics.temp} subtext="Current condition reading" color="#0d9488" />
        <MetricCard icon={Wind} label="WIND SPEED" value={metrics.wind} subtext="Steady direction with light gusts" color="#3b82f6" />
        <MetricCard icon={Droplets} label="HUMIDITY" value={metrics.humidity} subtext="Moisture content in air" color="#06b6d4" />
        <MetricCard icon={Sun} label="UV INDEX" value={metrics.uvIndex} subtext="Protection recommended" color="#eab308" />
        <MetricCard icon={Eye} label="VISIBILITY" value={metrics.visibility} subtext="Clear line of sight" color="#8b5cf6" />
        <MetricCard icon={Gauge} label="PRESSURE" value={metrics.pressure} subtext="Standard atmospheric level" color="#64748b" />
      </div>

      {/* Risk Alert */}
      <div style={{ background: "#fffbeb", border: "1px solid #fde68a", padding: "20px 24px", borderRadius: "20px", display: "flex", alignItems: "center", gap: "16px" }}>
        <AlertTriangle size={24} style={{ color: "#d97706", flexShrink: 0 }} />
        <div>
          <h4 style={{ fontSize: "15px", fontWeight: "700", color: "#92400e", margin: "0 0 2px 0" }}>{metrics.condition}</h4>
          <p style={{ fontSize: "13px", color: "#b45309", margin: 0 }}>{metrics.status}</p>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, subtext, color }) {
  return (
    <div style={{ background: "white", padding: "24px", borderRadius: "24px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.02)", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", color, marginBottom: "10px", fontWeight: "700", fontSize: "13px", letterSpacing: "0.05em" }}>
          <Icon size={18} /> {label}
        </div>
        <div style={{ fontSize: "32px", fontWeight: "800", color: "#1e293b", marginBottom: "8px" }}>{value}</div>
      </div>
      {subtext && <div style={{ fontSize: "12px", color: "#64748b", fontWeight: "500" }}>{subtext}</div>}
    </div>
  );
}