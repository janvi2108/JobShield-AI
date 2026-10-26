import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, SearchCheck } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center p-6 text-center">
      <div className="max-w-md w-full p-8 rounded-xl bg-[#191C22] border border-[#2C313C] space-y-5 shadow-2xl">
        <div className="w-14 h-14 rounded-full bg-[#D9B100]/10 border border-[#D9B100]/30 text-[#D9B100] mx-auto flex items-center justify-center">
          <ShieldAlert className="w-7 h-7 stroke-[1.75]" />
        </div>

        <div className="space-y-1.5">
          <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#D9B100] font-semibold">
            404 Error
          </span>
          <h2 className="text-2xl font-bold text-[#F2F4F6] tracking-tight">
            Page Not Found
          </h2>
          <p className="text-xs text-[#949BA6] leading-relaxed max-w-xs mx-auto">
            The destination you requested does not exist or has moved. Use the options below to navigate back safely.
          </p>
        </div>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            to="/"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-full bg-[#101114] hover:bg-[#21252D] text-[#F2F4F6] border border-[#3B3F46] hover:border-[#626A77] font-medium text-xs transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return Home</span>
          </Link>
          <Link
            to="/analyze"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-full bg-[#D9B100] hover:bg-[#e5bc05] text-[#101114] font-semibold text-xs transition-colors shadow-sm"
          >
            <SearchCheck className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>Analyze a Job</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
