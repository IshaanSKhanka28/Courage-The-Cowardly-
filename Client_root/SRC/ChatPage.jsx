import { useState, useRef, useEffect } from 'react';
import { Send, ChevronDown, ChevronUp, Sparkles, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const NIMIT_API_URL = 'http://localhost:8000/ask';

const LOCATIONS = ['Mumbai', 'Pune', 'Bengaluru', 'Delhi', 'Ludhiana', 'Amritsar'];

const SECTORS = [
  { value: 'traffic', label: 'Traffic' },
  { value: 'health', label: 'Health' },
  { value: 'agriculture', label: 'Agriculture' },
];

const RISK_STYLES = {
  LOW: { bg: 'rgba(34,197,94,0.12)', text: '#4ade80', border: 'rgba(34,197,94,0.4)' },
  MODERATE: { bg: 'rgba(234,179,8,0.12)', text: '#facc15', border: 'rgba(234,179,8,0.4)' },
  HIGH: { bg: 'rgba(249,115,22,0.12)', text: '#fb923c', border: 'rgba(249,115,22,0.4)' },
  SEVERE: { bg: 'rgba(239,68,68,0.12)', text: '#f87171', border: 'rgba(239,68,68,0.4)' },
};

export default function ChatPage() {
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('Mumbai');
  const [sector, setSector] = useState('traffic');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [expandedTraces, setExpandedTraces] = useState({});
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e, customText, overrides = {}) => {
    if (e) e.preventDefault();
    const textToSend = customText || query;
    if (!textToSend.trim()) return;

    const effectiveLocation = overrides.location || location;
    const effectiveSector = overrides.sector || sector;

    // Keep the visible controls in sync when a shortcut button drives the request.
    if (overrides.location && overrides.location !== location) setLocation(overrides.location);
    if (overrides.sector && overrides.sector !== sector) setSector(overrides.sector);

    const userMessage = { id: Date.now(), sender: 'user', text: textToSend };
    setMessages((prev) => [...prev, userMessage]);
    if (!customText) setQuery('');
    setLoading(true);

    try {
      const response = await fetch(NIMIT_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: textToSend, location: effectiveLocation, sector: effectiveSector }),
      });

      if (!response.ok) {
        let detail = `Request failed (HTTP ${response.status}).`;
        try {
          const errorBody = await response.json();
          if (errorBody && errorBody.detail) detail = errorBody.detail;
        } catch {
          // Response body wasn't JSON - fall back to the generic status message above.
        }
        setMessages((prev) => [
          ...prev,
          { id: Date.now() + 1, sender: 'bot', isError: true, answer: detail },
        ]);
        return;
      }

      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          answer: data.answer,
          sources: Array.isArray(data.sources) ? data.sources : [],
          riskLevel: data.risk_level,
          trace: Array.isArray(data.reasoning_trace) ? data.reasoning_trace : [],
          fallbackUsed: !!data.fallback_used,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          isError: true,
          answer: "Couldn't reach the Nimit backend at localhost:8000. Make sure the server is running and try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleTrace = (id) => {
    setExpandedTraces((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, maxWidth: "48rem", width: "100%", margin: "0 auto", padding: "1.5rem", display: "flex", flexDirection: "column", boxSizing: "border-box", overflow: "hidden" }}>

      {/* Scrollable chat body with minHeight: 0 to fix flex collapse */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", overflowY: "auto", paddingRight: "0.5rem", flex: 1, minHeight: 0 }}>

        {messages.length === 0 && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            style={{ textAlign: "center", margin: "auto", padding: "3rem 0" }}
          >
            <h1 style={{ fontSize: "1.875rem", fontWeight: 800, color: "#f8fafc", letterSpacing: "-0.025em", marginBottom: "0.75rem" }}>What would you like to check?</h1>
            <p style={{ fontSize: "0.875rem", color: "#94a3b8", marginBottom: "1rem" }}>Ask about commute flooding or heatwave safety grounded in official guidelines.</p>
            <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0.5rem", paddingTop: "1rem" }}>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={(e) => handleSend(e, "Will my commute via the Andheri Subway in Mumbai be flooded tomorrow morning?", { location: 'Mumbai', sector: 'traffic' })}
                style={{ fontSize: "0.75rem", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#f8fafc", padding: "0.5rem 0.875rem", borderRadius: "0.75rem", cursor: "pointer" }}
              >
                🌧️ Andheri Subway Flooding
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={(e) => handleSend(e, "Is tomorrow's Delhi heat safe for outdoor children's sports?", { location: 'Delhi', sector: 'health' })}
                style={{ fontSize: "0.75rem", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#f8fafc", padding: "0.5rem 0.875rem", borderRadius: "0.75rem", cursor: "pointer" }}
              >
                ☀️ Delhi Heat Safety
              </motion.button>
            </div>
          </motion.div>
        )}

        {/* Message History Feed */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <AnimatePresence mode="popLayout">
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 30, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                style={{ display: "flex", justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start', width: "100%" }}
              >
                {msg.sender === 'user' ? (
                  <div style={{ background: "#0ea5e9", color: "#ffffff", borderRadius: "1rem", padding: "0.75rem 1.25rem", maxWidth: "36rem", fontSize: "0.875rem", fontWeight: 500, boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)" }}>
                    {msg.text}
                  </div>
                ) : msg.isError ? (
                  <div style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.35)", borderRadius: "1rem", padding: "1rem 1.25rem", display: "flex", alignItems: "flex-start", gap: "0.625rem", maxWidth: "36rem", width: "100%", boxSizing: "border-box" }}>
                    <AlertTriangle size={18} style={{ color: "#f87171", flexShrink: 0, marginTop: "0.125rem" }} />
                    <span style={{ color: "#fca5a5", fontSize: "0.875rem", lineHeight: "1.5" }}>{msg.answer}</span>
                  </div>
                ) : (
                  <div style={{ background: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "1rem", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem", boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.2)", maxWidth: "42rem", width: "100%" }}>
                    {msg.riskLevel && (
                      <div
                        style={{
                          alignSelf: "flex-start",
                          fontSize: "0.7rem",
                          fontWeight: 700,
                          letterSpacing: "0.05em",
                          padding: "0.25rem 0.625rem",
                          borderRadius: "999px",
                          background: (RISK_STYLES[msg.riskLevel] || RISK_STYLES.MODERATE).bg,
                          color: (RISK_STYLES[msg.riskLevel] || RISK_STYLES.MODERATE).text,
                          border: `1px solid ${(RISK_STYLES[msg.riskLevel] || RISK_STYLES.MODERATE).border}`,
                        }}
                      >
                        {msg.riskLevel} RISK
                      </div>
                    )}

                    <div style={{ color: "#f8fafc", lineHeight: "1.625", fontSize: "1rem" }}>
                      "{msg.answer}"
                    </div>

                    {msg.fallbackUsed && (
                      <div
                        style={{
                          fontSize: "0.75rem",
                          color: "#facc15",
                          background: "rgba(234,179,8,0.08)",
                          border: "1px solid rgba(234,179,8,0.3)",
                          borderRadius: "0.5rem",
                          padding: "0.5rem 0.75rem",
                          display: "flex",
                          alignItems: "center",
                          gap: "0.5rem",
                          width: "fit-content",
                        }}
                      >
                        <AlertTriangle size={14} style={{ flexShrink: 0 }} />
                        Using cached forecast data - live weather temporarily unavailable
                      </div>
                    )}

                    <div style={{ fontSize: "0.75rem", color: "#94a3b8", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "0.75rem", display: "flex", flexDirection: "column", gap: "0.625rem" }}>
                      {msg.sources && msg.sources.length > 0 && (
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                          <span style={{ fontWeight: 600 }}>Sources</span>
                          {msg.sources.map((url, i) => (
                            <a
                              key={i}
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ color: "#38bdf8", wordBreak: "break-all", textDecoration: "none" }}
                            >
                              {url}
                            </a>
                          ))}
                        </div>
                      )}

                      <div style={{ display: "flex", justifyContent: "flex-end" }}>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => toggleTrace(msg.id)}
                          style={{ display: "flex", alignItems: "center", gap: "0.25rem", color: "#38bdf8", fontWeight: 600, background: "none", border: "none", cursor: "pointer", fontSize: "0.75rem" }}
                        >
                          Why? {expandedTraces[msg.id] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </motion.button>
                      </div>
                    </div>

                    <AnimatePresence>
                      {expandedTraces[msg.id] && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.2 }}
                          style={{ overflow: "hidden" }}
                        >
                          <div style={{ background: "#1e293b", padding: "1rem", borderRadius: "0.75rem", border: "1px solid rgba(255,255,255,0.06)", fontSize: "0.75rem", display: "flex", flexDirection: "column", gap: "0.5rem", color: "#cbd5e1", marginTop: "0.5rem" }}>
                            <div style={{ fontWeight: 600, color: "#38bdf8", marginBottom: "0.25rem" }}>Deterministic Verification Trace:</div>
                            {msg.trace && msg.trace.length > 0 ? (
                              msg.trace.map((step, i) => (
                                <div key={i}>• {step}</div>
                              ))
                            ) : (
                              <div style={{ color: "#94a3b8" }}>No reasoning trace available.</div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ textAlign: "center", padding: "1.5rem 0", color: "#94a3b8", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}
            >
              <Sparkles size={18} style={{ color: "#38bdf8", animation: "spin 1s linear infinite" }} /> Analyzing live weather and official policy rules...
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Controls + Input pinned cleanly to the bottom */}
      <div style={{ paddingTop: "1rem", paddingBottom: "0.5rem", flexShrink: 0, background: "transparent" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.625rem", marginBottom: "0.625rem", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
            <span style={{ fontSize: "0.7rem", color: "#94a3b8" }}>Location</span>
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              style={{
                fontSize: "0.75rem",
                fontWeight: 500,
                color: "#f8fafc",
                background: "#0f172a",
                border: "1px solid rgba(255,255,255,0.15)",
                borderRadius: "0.5rem",
                padding: "0.375rem 0.5rem",
                outline: "none",
                cursor: "pointer",
              }}
            >
              {LOCATIONS.map((loc) => {
                // When Agriculture is selected, only Ludhiana and Amritsar are valid
                const isAgriculture = sector === 'agriculture';
                const enabled = isAgriculture
                  ? loc === 'Ludhiana' || loc === 'Amritsar'
                  : true;
                return (
                  <option
                    key={loc}
                    value={loc}
                    disabled={!enabled}
                    style={{ background: enabled ? "#0f172a" : "#6b7280", color: enabled ? "#f8fafc" : "#6b728c" }}
                  >
                    {loc}
                  </option>
                );
              })}
            </select>
          </div>

          <div style={{ display: "flex", gap: "0.375rem" }}>
            {SECTORS.map((s) => (
              <motion.button
                key={s.value}
                type="button"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSector(s.value)}
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  padding: "0.375rem 0.75rem",
                  borderRadius: "0.5rem",
                  cursor: "pointer",
                  border: sector === s.value ? "1px solid #38bdf8" : "1px solid rgba(255,255,255,0.12)",
                  background: sector === s.value ? "rgba(56,189,248,0.15)" : "rgba(255,255,255,0.05)",
                  color: sector === s.value ? "#38bdf8" : "#94a3b8",
                }}
              >
                {s.label}
              </motion.button>
            ))}
          </div>
        </div>

        {/* Agriculture location constraint note */}
        {sector === 'agriculture' && (
          <div style={{
            fontSize: "0.7rem",
            color: "#facc15",
            background: "rgba(234,179,8,0.08)",
            border: "1px solid rgba(234,179,8,0.3)",
            borderRadius: "0.5rem",
            padding: "0.5rem 0.75rem",
            marginBottom: "0.625rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}>
            <div style={{ fontWeight: 600 }}>Agriculture coverage: Punjab only</div>
            <span>Valid locations: Ludhiana, Amritsar</span>
          </div>
        )}

        <form onSubmit={(e) => handleSend(e)}>
          <div style={{ position: "relative", display: "flex", alignItems: "center", boxShadow: "0 4px 12px rgba(0, 0, 0, 0.3)", borderRadius: "1rem", overflow: "hidden", border: "1px solid rgba(255, 255, 255, 0.15)", background: "#0f172a" }}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a location-specific weather impact question..."
              style={{ width: "100%", padding: "1rem 3.5rem 1rem 1rem", fontSize: "0.875rem", color: "#f8fafc", background: "transparent", border: "none", outline: "none" }}
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              style={{ position: "absolute", right: "0.5rem", background: "#0ea5e9", color: "#ffffff", padding: "0.625rem", borderRadius: "0.75rem", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
            >
              <Send size={16} color="#ffffff" />
            </motion.button>
          </div>
        </form>
      </div>
    </div>
  );
}
