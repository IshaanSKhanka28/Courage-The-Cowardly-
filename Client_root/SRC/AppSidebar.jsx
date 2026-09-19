import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { 
  Info, 
  Sun, 
  MessageSquare, 
  ShieldCheck 
} from "lucide-react";

export function AppSidebar({ children }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const location = useLocation();

  const navItems = [
    { label: "About Project", href: "/", icon: Info },
    { label: "Weather & Risks", href: "/weather", icon: Sun },
    { label: "Chatbot AI", href: "/chat", icon: MessageSquare },
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans">
      
      {/* Full-Height Left Sidebar */}
      <aside
        onMouseEnter={() => setIsExpanded(true)}
        onMouseLeave={() => setIsExpanded(false)}
        className={`h-full bg-white border-r border-slate-200 flex flex-col justify-between py-6 px-4 transition-all duration-300 ease-in-out z-30 shadow-xl select-none ${
          isExpanded ? "w-64" : "w-20"
        }`}
      >
        <div>
          {/* Logo / Brand Header */}
          <div className="flex items-center gap-3 px-2 mb-8">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center shrink-0 shadow-md shadow-teal-600/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div className={`overflow-hidden transition-all duration-300 ${isExpanded ? "opacity-150 w-auto" : "opacity-0 w-0"}`}>
              <h1 className="font-extrabold text-slate-800 text-lg tracking-wider">NIMIT</h1>
              <p className="text-[10px] text-teal-600 font-semibold uppercase tracking-widest">Risk System</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.href}
                  to={item.href}
                  className={`flex items-center gap-4 px-3.5 py-3 rounded-2xl transition-all font-medium text-sm group ${
                    isActive
                      ? "bg-teal-50 text-teal-700 border border-teal-100 shadow-xs"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <Icon className={`w-5 h-5 shrink-0 ${isActive ? "text-teal-600" : "text-slate-500 group-hover:text-slate-900"}`} />
                  <span className={`whitespace-nowrap transition-opacity duration-300 ${isExpanded ? "opacity-100" : "opacity-0 pointer-events-none"}`}>
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer Status Indicator */}
        <div className="pt-4 border-t border-slate-100 px-2 flex items-center gap-3">
          <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse shrink-0 shadow-sm shadow-emerald-500/50" />
          <div className={`overflow-hidden transition-all duration-300 ${isExpanded ? "opacity-100 w-auto" : "opacity-0 w-0"}`}>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider whitespace-nowrap">System Live</span>
          </div>
        </div>
      </aside>

      {/* Main Right-Hand Content Area (Automatically expands/adjusts) */}
      <main className="flex-1 h-full overflow-y-auto bg-gradient-to-br from-slate-50 via-white to-teal-50/10 p-8 md:p-12">
        <div className="max-w-5xl mx-auto w-full">
          {children}
        </div>
      </main>

    </div>
  );
}