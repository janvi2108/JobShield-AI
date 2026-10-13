import React from 'react';

/**
 * Technical badge indicator for security status, model lifecycle, and risk levels.
 */
export default function StatusBadge({ status, label, size = 'sm' }) {
  const styles = {
    pending: 'bg-shield-surface/60 text-shield-soft border-shield-border',
    warning: 'bg-amber-950/40 text-amber-300 border-amber-800/60',
    danger: 'bg-red-950/40 text-red-300 border-red-800/60',
    success: 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60',
    info: 'bg-sky-950/40 text-sky-300 border-sky-800/60',
    neutral: 'bg-shield-surface/40 text-shield-muted border-shield-border',
    accent: 'bg-[#D9B100]/15 text-[#F3DA87] border-[#D9B100]/40',
  };

  const currentStyle = styles[status] || styles.neutral;
  const sizeClasses = size === 'xs' ? 'text-[11px] px-2 py-0.5' : 'text-xs px-2.5 py-1';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono uppercase tracking-wider font-medium rounded border ${sizeClasses} ${currentStyle}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          status === 'success'
            ? 'bg-emerald-400'
            : status === 'danger'
            ? 'bg-red-400'
            : status === 'warning'
            ? 'bg-amber-400'
            : status === 'accent'
            ? 'bg-[#D9B100]'
            : 'bg-shield-soft'
        }`}
      />
      {label}
    </span>
  );
}
