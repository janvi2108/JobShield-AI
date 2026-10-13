import React from 'react';
import { Link } from 'react-router-dom';
import {
  FileSpreadsheet,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  Layers,
  HelpCircle,
  ExternalLink,
  ChevronRight,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';

export default function ResultsPage({ analysisResult }) {
  // If no genuine analysis result exists yet (as in this foundation phase),
  // show an honest, meaningful empty state with layout specifications.
  if (!analysisResult) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto">
        {/* Page header */}
        <div className="border-b border-shield-border pb-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#D9B100] font-semibold">
              Inference Report & SHAP Breakdown
            </span>
          </div>
          <h2 className="text-xl font-bold text-shield-text">
            Job Opportunity Analysis Results
          </h2>
          <p className="text-xs text-shield-muted mt-0.5">
            Transparent breakdown of model classification score, threat heuristic indicators, and explainable feature contributions.
          </p>
        </div>

        {/* Meaningful empty state */}
        <EmptyState
          icon={FileSpreadsheet}
          title="No Active Job Analysis In Memory"
          description="Analysis results are generated exclusively through live ML inference on submitted postings. Because fake predictions are strictly prohibited, this page will populate immediately once candidate models are trained on the EMSCAD dataset and an inference is run."
          technicalNote="Architecture Specification: When active, this page renders (1) Binary Classification Class & Probability Score, (2) Risk Severity Category & Basis, (3) Threat Heuristic Signals, and (4) SHAP Waterfall / Feature Contribution Attributions."
          actionButton={
            <div className="flex items-center gap-3">
              <Link
                to="/analyze"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-[#D9B100] hover:bg-[#e5bc05] text-black font-semibold text-xs transition-colors"
              >
                <span>Submit Job for Analysis</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                to="/performance"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-shield-card hover:bg-shield-surface text-shield-text border border-shield-border text-xs font-medium transition-colors"
              >
                <span>Check Model Readiness</span>
              </Link>
            </div>
          }
        />

        {/* Blueprint preview of the 4 key result sections */}
        <div className="space-y-3 pt-2">
          <h3 className="text-xs font-mono uppercase tracking-wider text-shield-subtle font-semibold">
            Result Schema Specifications (Under Implementation)
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-shield-card border border-shield-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-shield-text">
                  1. Classification & Score
                </span>
                <StatusBadge status="neutral" label="Spec Ready" size="xs" />
              </div>
              <p className="text-xs text-shield-muted leading-relaxed">
                Legitimate (0) vs. Potentially Fraudulent (1) prediction with exact calibrated probability output from the selected classifier.
              </p>
            </div>

            <div className="p-4 rounded-lg bg-shield-card border border-shield-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-shield-text">
                  2. Risk Policy Categorization
                </span>
                <StatusBadge status="neutral" label="Spec Ready" size="xs" />
              </div>
              <p className="text-xs text-shield-muted leading-relaxed">
                Low, Moderate, High, or Severe Risk classification derived from probability thresholds and compound threat signals.
              </p>
            </div>

            <div className="p-4 rounded-lg bg-shield-card border border-shield-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-shield-text">
                  3. Heuristic Threat Signals
                </span>
                <StatusBadge status="neutral" label="Spec Ready" size="xs" />
              </div>
              <p className="text-xs text-shield-muted leading-relaxed">
                Rules engine detection of upfront payment solicitations, untraceable messaging apps (Telegram/WhatsApp), and domain anomalies.
              </p>
            </div>

            <div className="p-4 rounded-lg bg-shield-card border border-shield-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-shield-text">
                  4. SHAP Token Attributions
                </span>
                <StatusBadge status="neutral" label="Spec Ready" size="xs" />
              </div>
              <p className="text-xs text-shield-muted leading-relaxed">
                Top N positive and negative token contributions explaining exactly which words increased or decreased the fraud score.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Active result view (when populated by actual ML response)
  const isFraud = analysisResult.prediction === 1;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Top Classification Summary Banner */}
      <div
        className={`p-6 rounded-lg border ${
          isFraud
            ? 'bg-red-950/20 border-red-800/60'
            : 'bg-emerald-950/20 border-emerald-800/60'
        }`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div
              className={`p-3 rounded-lg border ${
                isFraud
                  ? 'bg-red-950/40 border-red-700 text-red-400'
                  : 'bg-emerald-950/40 border-emerald-700 text-emerald-400'
              }`}
            >
              {isFraud ? (
                <ShieldAlert className="w-8 h-8 stroke-[2]" />
              ) : (
                <ShieldCheck className="w-8 h-8 stroke-[2]" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono uppercase tracking-wider text-shield-subtle">
                  Verdict
                </span>
                <StatusBadge
                  status={isFraud ? 'danger' : 'success'}
                  label={isFraud ? 'High Scam Risk' : 'Likely Legitimate'}
                  size="xs"
                />
              </div>
              <h2 className="text-xl font-bold text-shield-text">
                {isFraud
                  ? 'Potentially Fraudulent Job Posting'
                  : 'Legitimate Employment Posting'}
              </h2>
              <p className="text-xs text-shield-muted mt-1 max-w-xl">
                {isFraud
                  ? 'This posting exhibits multiple risk factors characteristic of employment fraud.'
                  : 'Textual patterns align with standard corporate hiring practices in the EMSCAD baseline.'}
              </p>
            </div>
          </div>

          <div className="p-3.5 rounded bg-shield-base border border-shield-border font-mono text-center min-w-36">
            <div className="text-[11px] text-shield-subtle uppercase">
              Model Score
            </div>
            <div className="text-2xl font-bold text-[#F3DA87]">
              {(analysisResult.score * 100).toFixed(1)}%
            </div>
            <div className="text-[10px] text-shield-muted">Fraud Probability</div>
          </div>
        </div>
      </div>
    </div>
  );
}
