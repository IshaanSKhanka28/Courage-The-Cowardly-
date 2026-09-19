import { useState, useRef, useEffect } from 'react';
import { Send, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ChatPage() {
  const [query, setQuery] = useState('');
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

  const handleSend = (e, customText) => {
    if (e) e.preventDefault();
    const textToSend = customText || query;
    if (!textToSend.trim()) return;

    const userMessage = { id: Date.now(), sender: 'user', text: textToSend };
    setMessages((prev) => [...prev, userMessage]);
    if (!customText) setQuery('');
    setLoading(true);

    setTimeout(() => {
      const botResponse = {
        id: Date.now() + 1,
        sender: 'bot',
        answer: "Yeah, I'd avoid it. Mumbai's looking at heavy rain tomorrow morning — around 42mm between 6 and 10am — and Andheri Subway is one of the spots that's flooded three separate times last monsoon whenever rainfall crossed this range.",
        sources: ["BMC Drainage Report 2024", "IMD Mumbai bulletin"],
        trace: {
          forecast: "42mm rainfall (Open-Meteo API)",
          ruleEngine: "Heavy Rain category + Known Flood Zone escalation -> SEVERE risk",
          ragEvidence: "Matched chunk: 'Andheri subway waterlogging threshold > 35mm triggers immediate high alert.'"
        }
      };
      setMessages((prev) => [...prev, botResponse]);
      setLoading(false);
    }, 1000);
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
                onClick={(e) => handleSend(e, "Will my commute via the Andheri Subway in Mumbai be flooded tomorrow morning?")} 
                style={{ fontSize: "0.75rem", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#f8fafc", padding: "0.5rem 0.875rem", borderRadius: "0.75rem", cursor: "pointer" }}
              >
                🌧️ Andheri Subway Flooding
              </motion.button>
              <motion.button 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={(e) => handleSend(e, "Is tomorrow's Delhi heat safe for outdoor children's sports?")} 
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
                ) : (
                  <div style={{ background: "#0f172a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "1rem", padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem", boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.2)", maxWidth: "42rem", width: "100%" }}>
                    <div style={{ color: "#f8fafc", lineHeight: "1.625", fontSize: "1rem" }}>
                      "{msg.answer}"
                    </div>
                    
                    <div style={{ fontSize: "0.75rem", color: "#94a3b8", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "0.75rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <span>Sources: {msg.sources.join(', ')}</span>
                      <motion.button 
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => toggleTrace(msg.id)} 
                        style={{ display: "flex", alignItems: "center", gap: "0.25rem", color: "#38bdf8", fontWeight: 600, background: "none", border: "none", cursor: "pointer" }}
                      >
                        Why? {expandedTraces[msg.id] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </motion.button>
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
                            <div>• <span style={{ color: "#94a3b8" }}>Fact (Forecast):</span> {msg.trace.forecast}</div>
                            <div>• <span style={{ color: "#94a3b8" }}>Rule Engine:</span> {msg.trace.ruleEngine}</div>
                            <div>• <span style={{ color: "#94a3b8" }}>RAG Evidence:</span> {msg.trace.ragEvidence}</div>
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

      {/* Input Form pinned cleanly to the bottom */}
      <form onSubmit={(e) => handleSend(e)} style={{ paddingTop: "1rem", paddingBottom: "0.5rem", flexShrink: 0, background: "transparent" }}>
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
  );
}