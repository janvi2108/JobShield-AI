import React from "react";
import { Link } from "react-router-dom";
import {
  ShieldAlert, ShieldCheck, ArrowRight, FileSpreadsheet, Search,
  AlertTriangle, CheckCircle2, Info,
} from "lucide-react";
import StatusBadge from "../components/StatusBadge";

function ScoreBar({ value }) {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? "bg-red-500" : pct >= 40 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-[#626A77]">Fraud Probability</span>
        <span className={pct >= 70 ? "text-red-400" : pct >= 40 ? "text-amber-400" : "text-emerald-400"}>
          {pct}%
        </span>
      </div>
      <div className="h-2 rounded-full bg-[#2C313C] overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function ResultsPage({ analysisResult }) {
  if (!analysisResult) {
    return (
      <div className="min-h-[calc(100vh-5rem)] bg-[#101114]">
        {/* Page header */}
        <div className="border-b border-[#2C313C]/50 bg-[#14161A]/60">
          <div className="max-w-4xl mx-auto px-6 sm:px-8 py-8">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#D9B100] font-semibold">
                Inference Report
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#F2F4F6] tracking-tight">Analysis Results</h1>
            <p className="mt-2 text-sm text-[#949BA6] max-w-xl">
              ML classification · risk categorization · SHAP attribution breakdown
            </p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-6 sm:px-8 py-12 space-y-8">
          {/* Empty state */}
          <div className="py-16 flex flex-col items-center text-center gap-6">
            <div className="w-16 h-16 rounded-2xl bg-[#191C22] border border-[#2C313C] flex items-center justify-center text-[#626A77]">
              <FileSpreadsheet className="w-7 h-7" />
            </div>
            <div className="max-w-md">
              <h2 className="text-lg font-semibold text-[#F2F4F6] mb-2">No Analysis In Memory</h2>
              <p className="text-sm text-[#949BA6] leading-relaxed">
                Results appear here after you submit a job posting for analysis. Because fake predictions are strictly prohibited, this page only populates with real ML inference output.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <Link to="/analyze" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#D9B100] hover:bg-[#e5bc05] text-[#101114] font-bold text-sm transition-all duration-150 hover:scale-[1.02]">
                <Search className="w-4 h-4" />Submit Job for Analysis
              </Link>
              <Link to="/performance" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#191C22] text-[#F2F4F6] border border-[#2C313C] hover:border-[#3B3F46] text-sm font-medium transition-colors">
                Check Model Status
              </Link>
            </div>
          </div>

          {/* Schema preview cards */}
          <div className="space-y-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-[#626A77] font-semibold">
              Result Schema (Active once model is trained)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { num: "1", title: "Classification & Score", desc: "Binary verdict (Legitimate / Fraudulent) with calibrated probability from the selected classifier." },
                { num: "2", title: "Risk Categorization", desc: "Low, Moderate, High, or Severe risk derived from probability thresholds and compound heuristic signals." },
                { num: "3", title: "Heuristic Threat Signals", desc: "Rules-based detection of payment requests, off-platform contact, domain anomalies, and urgency language." },
                { num: "4", title: "SHAP Token Attributions", desc: "Top-N positive and negative token contributions explaining which words most influenced the fraud score." },
              ].map(({ num, title, desc }) => (
                <div key={num} className="p-5 rounded-xl bg-[#191C22] border border-[#2C313C]">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-[#F2F4F6]">{num}. {title}</span>
                    <StatusBadge status="neutral" label="Spec Ready" size="xs" />
                  </div>
                  <p className="text-xs text-[#949BA6] leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const isFraud = analysisResult.is_fraudulent ?? (analysisResult.prediction === 1);
  const score = analysisResult.score ?? analysisResult.fraud_probability ?? 0;
  const riskSignals = analysisResult.risk_signals || analysisResult.heuristic_signals || [];
  const shapValues = analysisResult.shap_values || [];
  const explanation = analysisResult.explanation;

  return (
    <div className="min-h-[calc(100vh-5rem)] bg-[#101114]">
      {/* Page header */}
      <div className="border-b border-[#2C313C]/50 bg-[#14161A]/60">
        <div className="max-w-4xl mx-auto px-6 sm:px-8 py-8">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#D9B100] font-semibold">
              Inference Report
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#F2F4F6] tracking-tight">Analysis Results</h1>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 sm:px-8 py-8 sm:py-12 space-y-6">

        {/* Verdict banner */}
        <div className={`p-6 rounded-2xl border ${isFraud ? "bg-red-950/20 border-red-800/60" : "bg-emerald-950/20 border-emerald-800/60"}`}>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-5">
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-xl border ${isFraud ? "bg-red-950/40 border-red-700 text-red-400" : "bg-emerald-950/40 border-emerald-700 text-emerald-400"}`}>
                {isFraud ? <ShieldAlert className="w-7 h-7 stroke-[2]" /> : <ShieldCheck className="w-7 h-7 stroke-[2]" />}
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-xs font-mono uppercase tracking-wider text-[#626A77]">Verdict</span>
                  <StatusBadge status={isFraud ? "danger" : "success"} label={isFraud ? "High Scam Risk" : "Likely Legitimate"} size="xs" />
                </div>
                <h2 className="text-lg font-bold text-[#F2F4F6]">
                  {isFraud ? "Potentially Fraudulent Job Posting" : "Legitimate Employment Posting"}
                </h2>
                <p className="text-xs text-[#949BA6] mt-1 max-w-md">
                  {isFraud
                    ? "This posting exhibits multiple risk factors characteristic of employment fraud."
                    : "Textual patterns align with standard corporate hiring practices in the EMSCAD baseline."}
                </p>
              </div>
            </div>
            <div className="p-4 rounded-xl bg-[#14161A] border border-[#2C313C] font-mono text-center min-w-[120px]">
              <div className="text-[10px] text-[#626A77] uppercase mb-1">Model Score</div>
              <div className={`text-3xl font-bold ${isFraud ? "text-red-400" : "text-emerald-400"}`}>
                {(score * 100).toFixed(1)}%
              </div>
              <div className="text-[10px] text-[#626A77] mt-0.5">Fraud Probability</div>
            </div>
          </div>

          <div className="mt-5">
            <ScoreBar value={score} />
          </div>
        </div>

        {/* Risk signals */}
        {riskSignals.length > 0 && (
          <div className="p-5 rounded-2xl bg-[#191C22] border border-[#2C313C] space-y-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-[#626A77] font-semibold">
              Heuristic Risk Signals
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {riskSignals.map((signal, i) => (
                <div key={i} className="flex items-start gap-2.5 p-3 rounded-lg bg-[#14161A] border border-red-900/40">
                  <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                  <span className="text-xs text-[#F2F4F6]">{signal}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SHAP attributions */}
        {shapValues.length > 0 && (
          <div className="p-5 rounded-2xl bg-[#191C22] border border-[#2C313C] space-y-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-[#626A77] font-semibold">
              SHAP Token Attributions
            </h3>
            <p className="text-xs text-[#949BA6]">
              Positive values push the score toward fraud; negative values push toward legitimate.
            </p>
            <div className="space-y-3">
              {shapValues.map(({ token, value }, i) => {
                const absVal = Math.abs(value);
                const isFraudContrib = value > 0;
                return (
                  <div key={i} className="flex items-center gap-3">
                    <code className="text-xs text-[#F3DA87] font-mono bg-[#14161A] px-2.5 py-1 rounded min-w-[180px] max-w-[180px] truncate">
                      {token}
                    </code>
                    <div className="flex-1 h-1.5 rounded-full bg-[#2C313C]">
                      <div
                        className={`h-full rounded-full ${isFraudContrib ? "bg-red-500" : "bg-emerald-500"}`}
                        style={{ width: `${Math.min(absVal * 100, 100)}%` }}
                      />
                    </div>
                    <span className={`text-xs font-mono min-w-[50px] text-right ${isFraudContrib ? "text-red-400" : "text-emerald-400"}`}>
                      {value > 0 ? "+" : ""}{value.toFixed(3)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Action row */}
        <div className="flex flex-col sm:flex-row items-center gap-4 pt-4">
          <Link to="/analyze" className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-[#D9B100] hover:bg-[#e5bc05] text-[#101114] font-bold text-sm transition-all duration-150 hover:scale-[1.02]">
            <Search className="w-4 h-4" />Analyze Another Posting
          </Link>
          <Link to="/performance" className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-[#191C22] text-[#F2F4F6] border border-[#2C313C] hover:border-[#3B3F46] text-sm font-medium transition-colors">
            View Model Performance <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Disclaimer */}
        <div className="flex items-start gap-2.5 p-4 rounded-xl bg-[#191C22] border border-[#2C313C]">
          <Info className="w-4 h-4 text-[#626A77] flex-shrink-0 mt-0.5" />
          <p className="text-xs text-[#626A77] leading-relaxed">
            ML predictions are probabilistic, not definitive. Always verify suspicious postings independently. A low fraud score does not guarantee legitimacy.
          </p>
        </div>
      </div>
    </div>
  );
}
