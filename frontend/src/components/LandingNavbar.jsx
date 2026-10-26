import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu, X, Shield, Activity } from "lucide-react";

export default function LandingNavbar({ backendHealth, backendLoading, backendError }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const handleAboutClick = (e) => {
    if (location.pathname === "/") {
      e.preventDefault();
      const el = document.getElementById("capabilities");
      if (el) el.scrollIntoView({ behavior: "smooth" });
    }
  };

  const isActive = (path) => location.pathname === path;

  const navLinkClass = (path) =>
    `text-sm font-medium transition-colors ${
      isActive(path)
        ? "text-[#F2F4F6] font-semibold"
        : "text-[#949BA6] hover:text-[#F2F4F6]"
    }`;

  // Backend status dot
  const statusDot = backendLoading
    ? "bg-amber-400 animate-pulse"
    : backendHealth
    ? "bg-emerald-400"
    : "bg-red-500";

  const statusLabel = backendLoading
    ? "Connecting..."
    : backendHealth
    ? "Backend Online"
    : "Backend Offline";

  return (
    <header className="sticky top-0 z-50 w-full bg-[#101114]/85 backdrop-blur-xl border-b border-[#2C313C]/40">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 h-16 md:h-20 flex items-center justify-between">

        {/* Brand */}
        <Link to="/" className="flex items-center gap-2.5 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D9B100] rounded-lg py-1 px-1.5 -ml-1.5">
          <div className="w-8 h-8 rounded-lg bg-[#D9B100]/10 border border-[#D9B100]/30 flex items-center justify-center text-[#D9B100] group-hover:border-[#D9B100]/60 transition-colors">
            <Shield className="w-4 h-4 stroke-[2.25]" />
          </div>
          <span className="font-semibold text-lg md:text-xl tracking-tight text-[#F2F4F6] group-hover:text-white transition-colors">
            JobShield <span className="text-[#D9B100] font-mono font-bold text-base md:text-lg">AI</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-8">
          <Link to="/" className={navLinkClass("/")}>Home</Link>
          <Link to="/analyze" className={navLinkClass("/analyze")}>Analyze</Link>
          <Link to="/performance" className={navLinkClass("/performance")}>Performance</Link>
          <Link to="/#capabilities" onClick={handleAboutClick} className="text-sm font-medium text-[#949BA6] hover:text-[#F2F4F6] transition-colors">About</Link>
        </nav>

        {/* Desktop right actions */}
        <div className="hidden md:flex items-center gap-3">
          {/* Backend status pill */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#191C22] border border-[#2C313C] text-xs font-mono text-[#626A77]">
            <span className={`w-1.5 h-1.5 rounded-full ${statusDot}`} />
            {statusLabel}
          </div>
          <Link to="/performance" className="px-4 py-2 rounded-full text-sm font-medium text-[#F2F4F6] border border-[#3B3F46] hover:border-[#626A77] hover:bg-[#191C22] transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D9B100]">
            View Project
          </Link>
          <Link to="/analyze" className="px-5 py-2 rounded-full text-sm font-semibold bg-[#D9B100] hover:bg-[#e5bc05] text-[#101114] transition-all duration-150 shadow-sm hover:shadow-[#D9B100]/25 hover:scale-[1.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D9B100]">
            Analyze a Job
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded-lg text-[#949BA6] hover:text-[#F2F4F6] hover:bg-[#191C22] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D9B100]"
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#2C313C]/60 bg-[#101114]/98 px-6 py-5 space-y-4">
          <nav className="flex flex-col space-y-3 font-medium text-sm">
            {[
              ["/", "Home"],
              ["/analyze", "Analyze"],
              ["/performance", "Model Performance"],
            ].map(([path, label]) => (
              <Link key={path} to={path} onClick={() => setMobileMenuOpen(false)} className={`py-1 transition-colors ${isActive(path) ? "text-[#F2F4F6]" : "text-[#949BA6] hover:text-[#F2F4F6]"}`}>
                {label}
              </Link>
            ))}
            <Link to="/#capabilities" onClick={(e) => { setMobileMenuOpen(false); handleAboutClick(e); }} className="text-[#949BA6] hover:text-[#F2F4F6] transition-colors py-1">
              About
            </Link>
          </nav>
          <div className="pt-3 border-t border-[#2C313C]/40 flex flex-col gap-2.5">
            <div className="flex items-center gap-1.5 text-xs font-mono text-[#626A77]">
              <span className={`w-1.5 h-1.5 rounded-full ${statusDot}`} />{statusLabel}
            </div>
            <Link to="/analyze" onClick={() => setMobileMenuOpen(false)} className="w-full text-center px-4 py-2.5 rounded-full text-xs font-semibold bg-[#D9B100] hover:bg-[#e5bc05] text-[#101114] transition-colors shadow-sm">
              Analyze a Job
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
