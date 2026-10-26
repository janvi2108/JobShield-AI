import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  ShieldAlert,
  LayoutDashboard,
  SearchCheck,
  FileSpreadsheet,
  BarChart3,
  Terminal,
  Activity,
  Layers,
} from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function Sidebar({ backendHealth, mobileOpen, setMobileOpen }) {
  const navItems = [
    {
      to: '/',
      label: 'Home',
      icon: LayoutDashboard,
      badge: 'Overview',
    },
    {
      to: '/analyze',
      label: 'Analyze Job',
      icon: SearchCheck,
      badge: 'Inference',
    },
    {
      to: '/results',
      label: 'Analysis Results',
      icon: FileSpreadsheet,
      badge: 'Report',
    },
    {
      to: '/performance',
      label: 'Model Performance',
      icon: BarChart3,
      badge: 'Metrics',
    },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-shield-base border-r border-shield-border flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand header */}
        <div className="h-16 px-5 flex items-center justify-between border-b border-shield-border">
          <Link
            to="/"
            onClick={() => setMobileOpen(false)}
            className="flex items-center gap-2.5 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D9B100] rounded-md p-1 -ml-1"
          >
            <div className="w-9 h-9 rounded bg-[#D9B100]/10 border border-[#D9B100]/40 flex items-center justify-center text-[#D9B100] group-hover:border-[#D9B100]/70 transition-colors">
              <ShieldAlert className="w-5 h-5 stroke-[2]" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold tracking-tight text-shield-text text-base group-hover:text-white transition-colors">
                  JobShield
                </span>
                <span className="text-[11px] font-mono px-1.5 py-0.2 bg-[#D9B100] text-black font-semibold rounded">
                  AI
                </span>
              </div>
              <p className="text-[10px] uppercase font-mono tracking-wider text-shield-subtle">
                Fraud Detection Engine
              </p>
            </div>
          </Link>
        </div>

        {/* Navigation list */}
        <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-shield-subtle font-semibold">
              Security Navigation
            </span>
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-shield-surface/80 text-shield-text border-l-2 border-[#D9B100]'
                      : 'text-shield-muted hover:text-shield-text hover:bg-shield-surface/30'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className="flex items-center gap-3">
                      <Icon
                        className={`w-4 h-4 ${
                          isActive ? 'text-[#D9B100]' : 'text-shield-subtle'
                        }`}
                      />
                      <span>{item.label}</span>
                    </div>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        isActive
                          ? 'bg-[#D9B100]/20 text-shield-soft font-medium'
                          : 'text-shield-subtle bg-shield-border/40'
                      }`}
                    >
                      {item.badge}
                    </span>
                  </>
                )}
              </NavLink>
            );
          })}

          <div className="pt-6 px-3 pb-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-shield-subtle font-semibold">
              Engine Modules
            </span>
          </div>

          <div className="px-3 py-2 space-y-2 text-xs font-mono text-shield-muted">
            <div className="flex items-center justify-between py-1 border-b border-shield-border/40">
              <span className="text-shield-subtle">Dataset:</span>
              <span className="text-shield-text">EMSCAD</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-shield-border/40">
              <span className="text-shield-subtle">Candidates:</span>
              <span className="text-shield-text">4 Models</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-shield-border/40">
              <span className="text-shield-subtle">Explainability:</span>
              <span className="text-shield-text">SHAP Ready</span>
            </div>
          </div>
        </div>

        {/* Sidebar Footer System Status */}
        <div className="p-3 border-t border-shield-border bg-shield-base">
          <div className="p-2.5 rounded bg-shield-card border border-shield-border">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-mono uppercase tracking-wider text-shield-subtle">
                ML Pipeline Status
              </span>
              <StatusBadge
                status={
                  backendHealth?.model_status === 'trained'
                    ? 'success'
                    : 'pending'
                }
                label={
                  backendHealth?.model_status === 'trained'
                    ? 'Trained'
                    : 'Pending'
                }
                size="xs"
              />
            </div>
            <div className="flex items-center gap-1.5 text-xs text-shield-muted">
              <Activity className="w-3.5 h-3.5 text-shield-soft" />
              <span className="text-[11px] truncate">
                {backendHealth?.model_status === 'trained'
                  ? 'Model Active'
                  : 'Awaiting training run'}
              </span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
