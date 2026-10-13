import React from 'react';
import { AlertCircle } from 'lucide-react';

/**
 * Standard honest empty-state component for components pending ML execution or user input.
 */
export default function EmptyState({
  icon: Icon = AlertCircle,
  title,
  description,
  technicalNote,
  actionButton,
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 md:p-12 text-center rounded-lg border border-shield-border bg-shield-card/60 backdrop-blur-none">
      <div className="p-3.5 mb-4 rounded-md bg-shield-surface/50 border border-shield-border text-shield-soft">
        <Icon className="w-6 h-6 stroke-[1.75]" />
      </div>
      <h3 className="text-base font-semibold text-shield-text mb-2">
        {title}
      </h3>
      <p className="text-sm text-shield-muted max-w-md mb-4 leading-relaxed">
        {description}
      </p>

      {technicalNote && (
        <div className="max-w-lg w-full mb-6 p-3 rounded bg-shield-base/80 border border-shield-border text-left">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase font-mono tracking-wider font-semibold text-shield-soft">
              System Context
            </span>
          </div>
          <p className="font-mono text-xs text-shield-muted leading-relaxed">
            {technicalNote}
          </p>
        </div>
      )}

      {actionButton && <div>{actionButton}</div>}
    </div>
  );
}
