import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Building,
  MapPin,
  Briefcase,
  DollarSign,
  Clock,
  Sparkles,
  FileText,
  ListChecks,
  CheckCircle2,
  Trash2,
  RefreshCw,
} from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import { fetchAnalysisDetail, deleteAnalysis } from "../services/api";

export default function AnalysisDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showRawDescription, setShowRawDescription] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchAnalysisDetail(id);
        if (res.ok && res.data) {
          setAnalysis(res.data.analysis || res.data.data || res.data);
        } else {
          setError(res.error || `Analysis #${id} not found.`);
        }
      } catch (err) {
        setError(err.message || "Failed to load analysis details.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  const handleDelete = async () => {
    if (!window.confirm(`Permanently delete analysis #${id}?`)) return;
    setDeleting(true);
    try {
      const res = await deleteAnalysis(id);
      if (res.ok) {
        navigate("/history");
      } else {
        alert(res.error || "Failed to delete analysis.");
      }
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 text-center space-y-4 font-mono">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#D9B100]" />
        <p className="text-sm text-shield-muted">Loading analysis #{id} from SQLite database...</p>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-4 font-mono">
        <AlertTriangle className="w-10 h-10 mx-auto text-red-400" />
        <h2 className="text-lg font-bold text-shield-text">Record Not Found</h2>
        <p className="text-xs text-shield-muted">{error || `No record exists for analysis ID #${id}.`}</p>
        <Link
          to="/history"
          className="inline-flex items-center gap-2 px-4 py-2 rounded bg-shield-card border border-shield-border text-xs text-shield-text hover:bg-shield-surface"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Analysis History
        </Link>
      </div>
    );
  }

  const ext = analysis.extracted_details || {};
  const explanation = analysis.grounded_explanation;
  const findings = analysis.evidence_findings || [];
  const isFraud = Boolean(analysis.is_fraudulent);
  const fraudProb = analysis.fraud_probability ?? 0;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Back Navigation Bar */}
      <div className="flex items-center justify-between border-b border-shield-border pb-4">
        <Link
          to="/history"
          className="inline-flex items-center gap-2 text-xs font-mono text-shield-subtle hover:text-[#D9B100] transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to History
        </Link>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-shield-subtle">
            Stored #{analysis.id} • {new Date(analysis.created_at).toLocaleString()}
          </span>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-1.5 rounded hover:bg-red-500/10 text-shield-subtle hover:text-red-400 transition-colors"
            title="Delete Analysis"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Verdict Banner */}
      <div
        className={`p-6 rounded-lg border ${
          isFraud
            ? "bg-red-950/20 border-red-500/40 text-red-100"
            : "bg-emerald-950/20 border-emerald-500/40 text-emerald-100"
        } relative overflow-hidden`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2 font-mono text-xs">
              {isFraud ? (
                <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-400 font-bold border border-red-500/30 flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5" /> FRAUDULENT POSTING DETECTED
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5" /> LIKELY LEGITIMATE OPPORTUNITY
                </span>
              )}
              <StatusBadge
                status={
                  analysis.risk_level === "CRITICAL"
                    ? "error"
                    : analysis.risk_level === "HIGH"
                    ? "warning"
                    : "success"
                }
                label={`${analysis.risk_level} RISK`}
                size="xs"
              />
            </div>

            <h1 className="text-2xl font-bold tracking-tight text-white">
              {analysis.title || "Untitled Job Posting"}
            </h1>
            <p className="text-sm opacity-80 flex items-center gap-2">
              <Building className="w-3.5 h-3.5 opacity-70" />
              {analysis.company || "Company not specified"}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-baseline sm:items-center gap-4 font-mono">
            <div className="text-left sm:text-right">
              <div className="text-[11px] uppercase tracking-wider opacity-70">
                Calibrated Fraud Probability
              </div>
              <div className="text-3xl font-extrabold text-white">
                {(fraudProb * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] opacity-70">
                Decision threshold: {analysis.decision_threshold}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Extracted Details & Grounded Explanation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Structured Extracted Fields */}
        <div className="lg:col-span-1 space-y-6">
          <div className="p-5 rounded-lg bg-shield-card border border-shield-border space-y-4">
            <div className="flex items-center justify-between border-b border-shield-border pb-3">
              <h3 className="text-xs font-mono font-semibold uppercase text-shield-soft tracking-wider flex items-center gap-2">
                <Briefcase className="w-3.5 h-3.5 text-[#D9B100]" /> Extracted Attributes
              </h3>
              <span className="text-[11px] font-mono text-shield-subtle">
                {ext.extraction_method || "NLP"}
              </span>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div>
                <span className="text-shield-subtle block">Location:</span>
                <span className="text-shield-text">{ext.location || "Not specified"}</span>
              </div>
              <div>
                <span className="text-shield-subtle block">Employment Type:</span>
                <span className="text-shield-text">{ext.employment_type || "Not specified"}</span>
              </div>
              <div>
                <span className="text-shield-subtle block">Compensation / Stipend:</span>
                <span className="text-[#D9B100] font-semibold">{ext.compensation || "Not specified"}</span>
              </div>
              <div>
                <span className="text-shield-subtle block">Work Arrangement:</span>
                <span className="text-shield-text">{ext.work_arrangement || "Not specified"}</span>
              </div>
              <div>
                <span className="text-shield-subtle block">Internship / Contract Duration:</span>
                <span className="text-shield-text">{ext.duration || "Not specified"}</span>
              </div>
              <div>
                <span className="text-shield-subtle block">Required Education:</span>
                <span className="text-shield-text">{ext.required_education || "Not specified"}</span>
              </div>
              <div>
                <span className="text-shield-subtle block">Required Experience:</span>
                <span className="text-shield-text">{ext.required_experience || "Not specified"}</span>
              </div>

              {ext.required_skills && ext.required_skills.length > 0 && (
                <div className="pt-2">
                  <span className="text-shield-subtle block mb-1.5">Identified Skills:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {ext.required_skills.map((s, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-shield-base border border-shield-border text-[11px] text-[#F3DA87]"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Model Evaluation Telemetry */}
          <div className="p-5 rounded-lg bg-shield-card border border-shield-border space-y-3 font-mono text-xs">
            <h3 className="font-semibold uppercase text-shield-soft tracking-wider border-b border-shield-border pb-2">
              Model Telemetry
            </h3>
            <div className="flex justify-between">
              <span className="text-shield-subtle">Champion Model:</span>
              <span className="text-shield-text">{analysis.model_name || "Linear SVM"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-shield-subtle">Status:</span>
              <span className="text-emerald-400">Offline Inference</span>
            </div>
            <div className="flex justify-between">
              <span className="text-shield-subtle">Engine:</span>
              <span className="text-shield-text">scikit-learn 1.5</span>
            </div>
          </div>
        </div>

        {/* Right Column: Grounded AI Explanation & Heuristic Findings */}
        <div className="lg:col-span-2 space-y-6">
          {/* Grounded Explanation Box */}
          {explanation ? (
            <div className="p-6 rounded-lg bg-shield-card border border-shield-border space-y-4">
              <div className="flex items-center justify-between border-b border-shield-border pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#D9B100]" />
                  <h3 className="text-sm font-semibold text-shield-text">
                    Grounded Explainability Report
                  </h3>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-shield-base text-shield-subtle border border-shield-border">
                  {explanation.generation_method === "llm_groq"
                    ? "Groq Cloud Llama-3.3"
                    : "Deterministic Grounded Fallback"}
                </span>
              </div>

              <p className="text-sm text-shield-text leading-relaxed">
                {explanation.overall_summary}
              </p>

              {explanation.primary_reasons && explanation.primary_reasons.length > 0 && (
                <div className="space-y-2 pt-2">
                  <h4 className="text-xs font-mono uppercase text-[#D9B100] tracking-wider">
                    Key Decision Drivers
                  </h4>
                  <ul className="space-y-1.5 text-xs text-shield-muted">
                    {explanation.primary_reasons.map((r, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-[#D9B100] mt-0.5">•</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {explanation.verification_checklist && explanation.verification_checklist.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-shield-border/60">
                  <h4 className="text-xs font-mono uppercase text-emerald-400 tracking-wider flex items-center gap-1.5">
                    <ListChecks className="w-3.5 h-3.5" /> Candidate Safety Checklist
                  </h4>
                  <ul className="space-y-1.5 text-xs text-shield-muted">
                    {explanation.verification_checklist.map((c, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="p-6 rounded-lg bg-shield-card border border-shield-border text-xs font-mono text-shield-subtle">
              No grounded explanation was persisted for this session.
            </div>
          )}

          {/* Evidence Findings (Threat Signals) */}
          <div className="p-6 rounded-lg bg-shield-card border border-shield-border space-y-4">
            <div className="flex items-center justify-between border-b border-shield-border pb-3">
              <h3 className="text-sm font-semibold text-shield-text flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" /> Detected Evidence Findings ({findings.length})
              </h3>
              <span className="text-[11px] font-mono text-shield-subtle">Heuristic Scanner</span>
            </div>

            {findings.length === 0 ? (
              <p className="text-xs font-mono text-emerald-400">
                ✓ No critical scam threat signals or upfront fee solicitations detected in this posting.
              </p>
            ) : (
              <div className="space-y-3 font-mono text-xs">
                {findings.map((f, idx) => (
                  <div
                    key={f.id || idx}
                    className="p-3 rounded bg-shield-base border border-shield-border space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-red-400 font-semibold">{f.indicator_name}</span>
                      <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-red-500/20 text-red-300">
                        {f.severity}
                      </span>
                    </div>
                    <p className="text-shield-muted">{f.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Collapsible Raw Job Description */}
          <div className="p-4 rounded-lg bg-shield-card border border-shield-border space-y-3">
            <button
              onClick={() => setShowRawDescription(!showRawDescription)}
              className="w-full flex items-center justify-between text-xs font-mono text-shield-soft hover:text-shield-text transition-colors"
            >
              <span className="flex items-center gap-2">
                <FileText className="w-3.5 h-3.5" />
                Original Submitted Description
              </span>
              <span>{showRawDescription ? "Hide ▲" : "View ▼"}</span>
            </button>

            {showRawDescription && (
              <div className="pt-2 border-t border-shield-border">
                <pre className="p-3 rounded bg-shield-base border border-shield-border text-xs font-mono text-shield-muted whitespace-pre-wrap max-h-80 overflow-y-auto leading-relaxed">
                  {analysis.description || "No description provided."}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

