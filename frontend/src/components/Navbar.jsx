import React from 'react';
import { Menu, RefreshCw, Server, ExternalLink } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function Navbar({
  pageTitle,
  pageCategory = 'JobShield AI',
  backendHealth,
  backendLoading,
  backendError,
  onRefreshHealth,
  setMobileOpen,
}) {
  return (
    <header className="h-16 bg-shield-base/90 border-b border-shield-border px-4 lg:px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        {/* Mobile menu trigger */}
        <button
          onClick={() => setMobileOpen(true)}
          className="lg:hidden p-2 rounded text-shield-muted hover:text-shield-text hover:bg-shield-surface/50"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Page title and hierarchy */}
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-shield-subtle">
            <span>{pageCategory}</span>
            <span>/</span>
            <span className="text-shield-soft font-medium">{pageTitle}</span>
          </div>
          <h1 className="text-base font-semibold text-shield-text tracking-tight">
            {pageTitle}
          </h1>
        </div>
      </div>

      {/* Right controls: Backend health indicator & links */}
      <div className="flex items-center gap-3">
        {/* Backend health status badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-shield-card border border-shield-border text-xs">
          <Server className="w-3.5 h-3.5 text-shield-subtle" />
          <span className="text-shield-muted font-mono text-[11px]">API:</span>
          {backendLoading ? (
            <span className="font-mono text-[11px] text-shield-soft animate-pulse">
              Connecting...
            </span>
          ) : backendError ? (
            <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-red-400">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
              Offline
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              v{backendHealth?.version || '0.1.0'} Online
            </span>
          )}
        </div>

        {/* Refresh health check button */}
        <button
          onClick={onRefreshHealth}
          disabled={backendLoading}
          title="Refresh backend status"
          className="p-2 rounded border border-shield-border bg-shield-card hover:bg-shield-surface/50 text-shield-muted hover:text-shield-text transition-colors disabled:opacity-50"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${backendLoading ? 'animate-spin text-shield-soft' : ''}`}
          />
        </button>

        {/* Link to FastAPI interactive documentation */}
        <a
          href="http://127.0.0.1:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded border border-shield-border bg-shield-card hover:bg-shield-surface/50 text-xs font-mono text-shield-muted hover:text-shield-text transition-colors"
        >
          <span>API Docs</span>
          <ExternalLink className="w-3 h-3 text-shield-subtle" />
        </a>
      </div>
    </header>
  );
}
