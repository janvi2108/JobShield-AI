import React from "react";
import { Link } from "react-router-dom";
import {
  ShieldAlert, ShieldCheck, ArrowRight, FileSpreadsheet, Search,
  AlertTriangle, CheckCircle2, Info, Sparkles, AlertCircle, CheckSquare,
  HelpCircle, ExternalLink, ShieldQuestion, Flag, Lock, Eye
} from "lucide-react";
import StatusBadge from "../components/StatusBadge";

function ScoreBar({ value, riskLevel }) {
  const pct = Math.round(value * 100);
  const color =
    riskLevel === "CRITICAL" || pct >= 75
      ? "bg-red-500"
      : riskLevel === "HIGH" || pct >= 48
      ? "bg-amber-500"
      : riskLevel === "MODERATE"
      ? "bg-yellow-500"
      : "bg-emerald-500";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-[#949BA6]">Calibrated Fraud Probability</span>
        <span className={pct >= 48 ? "text-red-400 font-bold" : "text-emerald-400 font-bold"}>
          {pct}%
        </span>
      </div>
      <div className="h-2.5 rounded-full bg-[#2C313C] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${Math.max(2, pct)}%` }}
        />
      </div>
    </div>
  );
}

export default function ResultsPage({ analysisResult }) {
  if (!analysisResult) {
    return (
      <div className="min-h-[calc(100vh-5rem)] bg-[#101114]">
        <div className="border-b border-[#2C313C]/50 bg-[#14161A]/60">
          <div className="max-w-5xl mx-auto px-6 sm:px-8 py-8">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#D9B100] font-semibold">
                Inference Report
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#F2F4F6] tracking-tight">Analysis Results</h1>
            <p className="mt-2 text-sm text-[#949BA6] max-w-xl">
              ML classification · grounded AI explainability · evidence breakdown
            </p>
          </div>
        </div>

        <div className="max-w-5xl mx-auto px-6 sm:px-8 py-16 flex flex-col items-center text-center gap-6">
          <div className="w-16 h-16 rounded-2xl bg-[#191C22] border border-[#2C313C] flex items-center justify-center text-[#626A77]">
            <FileSpreadsheet className="w-7 h-7" />
          </div>
          <div className="max-w-md">
            <h2 className="text-lg font-semibold text-[#F2F4F6] mb-2">No Analysis In Memory</h2>
            <p className="text-sm text-[#949BA6] leading-relaxed">
              Results appear here after you submit a job posting for analysis. Run inference on a live posting or choose one of our verified sample presets.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <Link
              to="/analyze"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-[#D9B100] hover:bg-[#F3DA87] text-[#101114] font-bold text-sm transition-all shadow-lg shadow-[#D9B100]/10"
            >
              <Search className="w-4 h-4" /> Analyze a Job Posting
            </Link>
            <Link
              to="/performance"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-[#191C22] text-[#F2F4F6] border border-[#2C313C] hover:border-[#3B3F46] text-sm font-medium transition-colors"
            >
              Model Benchmarks
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const isFraud = analysisResult.is_fraudulent ?? (analysisResult.prediction === 1);
  const score = analysisResult.score ?? analysisResult.fraud_probability ?? 0;
  const riskLevel = analysisResult.risk_level || (isFraud ? "HIGH" : "LOW");
  const modelName = analysisResult.model_name || "Linear Support Vector Machine";
  const shapValues = analysisResult.shap_values || [];

  // Grounded explanation payload
  const groundedExp = analysisResult.metadata?.grounded_explanation || null;
  const warningSignals = groundedExp?.warning_signals || [];
  const positiveIndicators = groundedExp?.positive_indicators || [];
  const unverifiedInfo = groundedExp?.unverified_information || [];
  const checklist = groundedExp?.verification_checklist || [];

  return (
    <div className="min-h-[calc(100vh-5rem)] bg-[#101114]">
      {/* Header */}
      <div className="border-b border-[#2C313C]/50 bg-[#14161A]/60">
        <div className="max-w-5xl mx-auto px-6 sm:px-8 py-8">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#D9B100] font-semibold">
              Grounded Inference & Explainability Report
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#F2F4F6] tracking-tight">
            Analysis Results & Threat Audit
          </h1>
          <p className="mt-2 text-sm text-[#949BA6]">
            Classified by <span className="text-[#F2F4F6] font-medium">{modelName}</span> · Calibrated decision threshold: {analysisResult.decision_threshold || 0.48}
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 sm:px-8 py-8 sm:py-12 space-y-8">
        {/* Core Verdict Banner */}
        <div
          className={`p-6 sm:p-8 rounded-2xl border ${
            isFraud
              ? "bg-red-950/20 border-red-800/60 shadow-xl shadow-red-950/10"
              : "bg-emerald-950/20 border-emerald-800/60 shadow-xl shadow-emerald-950/10"
          }`}
        >
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div
                className={`p-3.5 rounded-2xl border ${
                  isFraud
                    ? "bg-red-950/50 border-red-700 text-red-400"
                    : "bg-emerald-950/50 border-emerald-700 text-emerald-400"
                }`}
              >
                {isFraud ? <ShieldAlert className="w-8 h-8 stroke-[2]" /> : <ShieldCheck className="w-8 h-8 stroke-[2]" />}
              </div>
              <div>
                <div className="flex items-center gap-2.5 mb-2">
                  <span className="text-xs font-mono uppercase tracking-wider text-[#949BA6]">Final Verdict</span>
                  <StatusBadge
                    status={isFraud ? "danger" : "success"}
                    label={`${riskLevel} RISK · ${isFraud ? "POTENTIAL SCAM" : "LIKELY LEGITIMATE"}`}
                    size="xs"
                  />
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-[#F2F4F6]">
                  {isFraud ? "Potentially Fraudulent Job Posting" : "Likely Legitimate Employment Posting"}
                </h2>
                <p className="text-xs sm:text-sm text-[#949BA6] mt-1.5 max-w-xl leading-relaxed">
                  {groundedExp?.overall_summary || (
                    isFraud
                      ? "This posting exhibits elevated statistical risk factors characteristic of employment fraud."
                      : "Textual patterns align with standard corporate hiring practices in the EMSCAD baseline."
                  )}
                </p>
              </div>
            </div>

            {/* Score pill */}
            <div className="p-4 sm:p-5 rounded-2xl bg-[#14161A] border border-[#2C313C] font-mono text-center min-w-[140px] flex-shrink-0">
              <div className="text-[10px] text-[#949BA6] uppercase tracking-wider mb-1">Risk Score</div>
              <div className={`text-4xl font-extrabold ${isFraud ? "text-red-400" : "text-emerald-400"}`}>
                {(score * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-[#626A77] mt-1 uppercase tracking-widest">{riskLevel} RISK</div>
            </div>
          </div>

          <div className="mt-6 pt-5 border-t border-[#2C313C]/40">
            <ScoreBar value={score} riskLevel={riskLevel} />
          </div>
        </div>

        {/* Grounded AI Explanation Card */}
        {groundedExp && (
          <div className="p-6 rounded-2xl bg-[#14161A] border border-[#2C313C] space-y-5">
            <div className="flex items-center justify-between border-b border-[#2C313C]/60 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-[#D9B100]" />
                <h3 className="text-sm font-semibold text-[#F2F4F6] uppercase tracking-wider font-mono">
                  Grounded AI Explanation & Evidence Synthesis
                </h3>
              </div>
              <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-[#191C22] text-[#949BA6] border border-[#2C313C]">
                Method: {groundedExp.generation_method}
              </span>
            </div>

            {/* Safety Verdict Banner */}
            <div className="p-4 rounded-xl bg-[#191C22] border border-[#2C313C] flex items-center justify-between gap-4">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#626A77]">
                  Applicant Safety Recommendation
                </span>
                <div className={`text-sm font-bold mt-0.5 ${isFraud ? "text-red-400" : "text-emerald-400"}`}>
                  {groundedExp.applicant_safety_verdict}
                </div>
              </div>
            </div>

            {/* Primary Reasons */}
            {groundedExp.primary_reasons?.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Primary Decision Drivers:
                </h4>
                <div className="space-y-2">
                  {groundedExp.primary_reasons.map((reason, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 p-3 rounded-xl bg-[#191C22]/80 border border-[#2C313C]/60 text-xs text-[#F2F4F6] leading-relaxed">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#D9B100] mt-2 flex-shrink-0" />
                      <span>{reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Warning Indicators (Evidence Citations) */}
        {warningSignals.length > 0 && (
          <div className="p-6 rounded-2xl bg-[#14161A] border border-red-950/60 space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <h3 className="text-sm font-semibold text-[#F2F4F6] uppercase tracking-wider font-mono">
                Verifiable Warning Indicators ({warningSignals.length} Flagged)
              </h3>
            </div>
            <div className="space-y-3">
              {warningSignals.map((w, i) => (
                <div key={i} className="p-4 rounded-xl bg-[#191C22] border border-red-900/40 space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs font-bold text-red-300">{w.indicator_name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-red-950/80 text-red-300 border border-red-800/80">
                        {w.severity}
                      </span>
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#14161A] text-[#949BA6] border border-[#2C313C]">
                        {w.category}
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-[#949BA6]">{w.reason_for_flagging}</div>
                  {w.evidence && (
                    <div className="p-2.5 rounded-lg bg-[#101114] border border-[#2C313C] font-mono text-[11px] text-[#F3DA87]/90 leading-normal">
                      &ldquo;{w.evidence}&rdquo;
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reassuring Positive Indicators */}
        {positiveIndicators.length > 0 && (
          <div className="p-6 rounded-2xl bg-[#14161A] border border-emerald-950/60 space-y-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-semibold text-[#F2F4F6] uppercase tracking-wider font-mono">
                Reassuring Organizational Signals ({positiveIndicators.length} Verified)
              </h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {positiveIndicators.map((r, i) => (
                <div key={i} className="p-4 rounded-xl bg-[#191C22] border border-emerald-900/30 space-y-1.5">
                  <div className="text-xs font-semibold text-emerald-300">{r.indicator_name}</div>
                  <div className="text-xs text-[#949BA6] leading-relaxed">{r.significance}</div>
                  {r.evidence && (
                    <div className="text-[11px] font-mono text-[#F2F4F6]/80 pt-1">
                      Evidence: {r.evidence}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Linear Model Feature Attributions */}
        {shapValues.length > 0 && (
          <div className="p-6 rounded-2xl bg-[#14161A] border border-[#2C313C] space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-[#F2F4F6] uppercase tracking-wider font-mono">
                  Linear Model Feature Contributions
                </h3>
                <p className="text-xs text-[#949BA6] mt-0.5">
                  Extracted from champion Linear SVM hyperplane weights (w_j · x_j). Positive pushes toward fraud.
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              {shapValues.map(({ token, value }, i) => {
                const absVal = Math.abs(value);
                const isFraudContrib = value > 0;
                return (
                  <div key={i} className="flex items-center gap-3">
                    <code className="text-xs text-[#F3DA87] font-mono bg-[#191C22] px-3 py-1.5 rounded-lg min-w-[200px] max-w-[200px] truncate border border-[#2C313C]">
                      {token}
                    </code>
                    <div className="flex-1 h-2 rounded-full bg-[#2C313C] overflow-hidden">
                      <div
                        className={`h-full rounded-full ${isFraudContrib ? "bg-red-500" : "bg-emerald-500"}`}
                        style={{ width: `${Math.min(absVal * 120, 100)}%` }}
                      />
                    </div>
                    <span
                      className={`text-xs font-mono min-w-[60px] text-right font-semibold ${
                        isFraudContrib ? "text-red-400" : "text-emerald-400"
                      }`}
                    >
                      {value > 0 ? "+" : ""}{value.toFixed(4)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Applicant Verification Checklist */}
        {checklist.length > 0 && (
          <div className="p-6 rounded-2xl bg-[#14161A] border border-[#2C313C] space-y-4">
            <div className="flex items-center gap-2">
              <CheckSquare className="w-5 h-5 text-[#D9B100]" />
              <h3 className="text-sm font-semibold text-[#F2F4F6] uppercase tracking-wider font-mono">
                Candidate Safety & Verification Checklist
              </h3>
            </div>
            <div className="space-y-2">
              {checklist.map((item, i) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-[#191C22] border border-[#2C313C] text-xs text-[#F2F4F6]">
                  <span className="w-5 h-5 rounded-md bg-[#2C313C] flex items-center justify-center font-mono text-[10px] text-[#D9B100] flex-shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <span className="leading-relaxed">{item}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Unverified Information & Missing Attributes */}
        {unverifiedInfo.length > 0 && (
          <div className="p-5 rounded-2xl bg-[#191C22] border border-[#2C313C] space-y-3">
            <div className="flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-[#949BA6]" />
              <h4 className="text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                Unverified Details & Missing Information
              </h4>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {unverifiedInfo.map((info, i) => (
                <div key={i} className="p-2.5 rounded-lg bg-[#14161A] border border-[#2C313C]/60 text-xs text-[#949BA6] flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-400/80" />
                  <span>{info}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Row */}
        <div className="flex flex-col sm:flex-row items-center gap-4 pt-4 border-t border-[#2C313C]/60">
          <Link
            to="/analyze"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-full bg-[#D9B100] hover:bg-[#F3DA87] text-[#101114] font-bold text-sm transition-all shadow-lg shadow-[#D9B100]/10"
          >
            <Search className="w-4 h-4" /> Analyze Another Opportunity
          </Link>
          <Link
            to="/performance"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-full bg-[#191C22] text-[#F2F4F6] border border-[#2C313C] hover:border-[#3B3F46] text-sm font-medium transition-colors"
          >
            Inspect Generalization Benchmarks <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
