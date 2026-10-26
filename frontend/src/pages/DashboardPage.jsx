import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  ArrowRight,
  Database,
  Cpu,
  FileSearch,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Layers,
  Sparkles,
  Info,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';

export default function DashboardPage({ backendHealth, backendError }) {
  const isModelTrained = backendHealth?.model_status === 'trained';

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner / Project Overview */}
      <section className="p-6 md:p-8 rounded-lg bg-shield-card border border-shield-border relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="max-w-2xl space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#D9B100] font-semibold bg-[#D9B100]/10 px-2.5 py-0.5 rounded border border-[#D9B100]/30">
                Cybersecurity & ML Defense
              </span>
              <span className="text-xs font-mono text-shield-subtle">
                Part 1 (40% MVP Foundation)
              </span>
            </div>

            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-shield-text">
              JobShield AI — Explainable Fraud Detection Engine
            </h1>

            <p className="text-sm md:text-base text-shield-muted leading-relaxed">
              Protecting job and internship seekers against fraudulent opportunities, 
              credential harvesting, upfront payment scams, and deceptive recruiter postings 
              using transparent machine learning classification and explainable AI.
            </p>

            <div className="pt-2 flex flex-wrap items-center gap-3">
              <Link
                to="/analyze"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-md bg-[#D9B100] hover:bg-[#e5bc05] text-black font-semibold text-sm transition-colors shadow-sm"
              >
                <span>Analyze Job Opportunity</span>
                <ArrowRight className="w-4 h-4 stroke-[2.5]" />
              </Link>

              <Link
                to="/performance"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-md bg-shield-surface/60 hover:bg-shield-surface text-shield-text font-medium text-sm border border-shield-border transition-colors"
              >
                <span>Inspect Model Pipeline</span>
              </Link>
            </div>
          </div>

          {/* Quick Engine Status Card */}
          <div className="w-full lg:w-80 p-4 rounded-md bg-shield-base/90 border border-shield-border space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-shield-border pb-2">
              <span className="text-shield-subtle uppercase text-[11px] tracking-wider">
                System Readiness
              </span>
              <StatusBadge
                status={isModelTrained ? 'success' : 'warning'}
                label={isModelTrained ? 'Ready' : 'Foundation Mode'}
                size="xs"
              />
            </div>

            <div className="space-y-2 text-shield-muted text-xs">
              <div className="flex justify-between">
                <span className="text-shield-subtle">Backend API:</span>
                <span className={backendError ? 'text-red-400' : 'text-emerald-400'}>
                  {backendError ? 'Offline (Port 8008)' : 'Active (FastAPI)'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-shield-subtle">Model Artifact:</span>
                <span className="text-[#F3DA87]">
                  {isModelTrained ? 'Serialized (.joblib)' : 'Pending Training'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-shield-subtle">Dataset Target:</span>
                <span className="text-shield-text">EMSCAD (17,880)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-shield-subtle">Explainability:</span>
                <span className="text-shield-text">SHAP Tree/Linear</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Detection Workflow Overview */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-shield-soft font-mono">
            4-Stage Detection Architecture
          </h2>
          <span className="text-xs text-shield-subtle font-mono">
            End-to-End Pipeline
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-shield-card border border-shield-border flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono font-semibold text-[#D9B100]">
                  STAGE 01
                </span>
                <FileSearch className="w-4 h-4 text-shield-subtle" />
              </div>
              <h3 className="text-sm font-semibold text-shield-text mb-1.5">
                Ingestion & Tokenization
              </h3>
              <p className="text-xs text-shield-muted leading-relaxed">
                Cleanses raw job postings, extracts textual bodies (title, requirements, description), and creates leakage-free TF-IDF feature matrices.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-shield-border/60 text-[11px] font-mono text-shield-subtle">
              Input: Raw Text Posting
            </div>
          </div>

          <div className="p-4 rounded-lg bg-shield-card border border-shield-border flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono font-semibold text-[#D9B100]">
                  STAGE 02
                </span>
                <Cpu className="w-4 h-4 text-shield-subtle" />
              </div>
              <h3 className="text-sm font-semibold text-shield-text mb-1.5">
                Multi-Model Scoring
              </h3>
              <p className="text-xs text-shield-muted leading-relaxed">
                Evaluates 4 candidate classifiers: Logistic Regression, Linear SVM, Random Forest, and XGBoost with PR-AUC optimization.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-shield-border/60 text-[11px] font-mono text-shield-subtle">
              Scoring: Class Probability
            </div>
          </div>

          <div className="p-4 rounded-lg bg-shield-card border border-shield-border flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono font-semibold text-[#D9B100]">
                  STAGE 03
                </span>
                <ShieldAlert className="w-4 h-4 text-shield-subtle" />
              </div>
              <h3 className="text-sm font-semibold text-shield-text mb-1.5">
                Risk Heuristic Policy
              </h3>
              <p className="text-xs text-shield-muted leading-relaxed">
                Flags domain spoofing, upfront equipment charges, crypto payment requests, interview-via-messaging apps, and salary anomalies.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-shield-border/60 text-[11px] font-mono text-shield-subtle">
              Rules: Threat Indicators
            </div>
          </div>

          <div className="p-4 rounded-lg bg-shield-card border border-shield-border flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono font-semibold text-[#D9B100]">
                  STAGE 04
                </span>
                <Sparkles className="w-4 h-4 text-shield-subtle" />
              </div>
              <h3 className="text-sm font-semibold text-shield-text mb-1.5">
                SHAP Explainability
              </h3>
              <p className="text-xs text-shield-muted leading-relaxed">
                Computes Shapley values for the analyzed posting, quantifying exactly which terms drove the prediction toward fraudulent or legitimate.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-shield-border/60 text-[11px] font-mono text-shield-subtle">
              Output: Explainable Rationale
            </div>
          </div>
        </div>
      </section>

      {/* Dataset Context & Subsystem Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Dataset Breakdown */}
        <section className="p-5 rounded-lg bg-shield-card border border-shield-border space-y-4">
          <div className="flex items-center justify-between border-b border-shield-border pb-3">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-[#D9B100]" />
              <h3 className="text-sm font-semibold text-shield-text">
                Target Dataset: EMSCAD
              </h3>
            </div>
            <span className="text-[11px] font-mono text-shield-subtle">
              Kaggle / Aegean
            </span>
          </div>

          <p className="text-xs text-shield-muted leading-relaxed">
            The Employment Scam Aegean Dataset contains real-world job advertisements 
            categorized into legitimate postings and verified scams.
          </p>

          <div className="space-y-2.5 font-mono text-xs">
            <div className="p-2.5 rounded bg-shield-base border border-shield-border flex justify-between">
              <span className="text-shield-subtle">Total Records:</span>
              <span className="text-shield-text font-semibold">17,880</span>
            </div>
            <div className="p-2.5 rounded bg-shield-base border border-shield-border flex justify-between">
              <span className="text-shield-subtle">Legitimate Class (0):</span>
              <span className="text-emerald-400 font-semibold">17,014 (95.16%)</span>
            </div>
            <div className="p-2.5 rounded bg-shield-base border border-shield-border flex justify-between">
              <span className="text-shield-subtle">Fraudulent Class (1):</span>
              <span className="text-red-400 font-semibold">866 (4.84%)</span>
            </div>
            <div className="p-2.5 rounded bg-shield-base border border-shield-border flex justify-between">
              <span className="text-shield-subtle">Class Imbalance:</span>
              <span className="text-amber-400 font-semibold">~19.6 : 1</span>
            </div>
          </div>

          <div className="p-2.5 rounded bg-shield-surface/30 border border-shield-border text-[11px] text-shield-muted flex items-start gap-2">
            <Info className="w-3.5 h-3.5 text-shield-soft flex-shrink-0 mt-0.5" />
            <span>
              Metadata leak fields (such as <code className="text-shield-text">in_balanced_dataset</code>) 
              will be excluded prior to fitting.
            </span>
          </div>
        </section>

        {/* Model Pipeline Status */}
        <section className="p-5 rounded-lg bg-shield-card border border-shield-border space-y-4">
          <div className="flex items-center justify-between border-b border-shield-border pb-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#D9B100]" />
              <h3 className="text-sm font-semibold text-shield-text">
                Candidate Classifiers
              </h3>
            </div>
            <StatusBadge
              status={isModelTrained ? 'success' : 'pending'}
              label={isModelTrained ? 'Trained' : 'Pending'}
              size="xs"
            />
          </div>

          <p className="text-xs text-shield-muted leading-relaxed">
            The four candidate algorithms will be trained on the training partition and evaluated via 
            PR-AUC and F1-Score:
          </p>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between p-2 rounded bg-shield-base border border-shield-border">
              <span className="text-shield-text">1. Logistic Regression</span>
              <span className="text-shield-subtle">TF-IDF Linear Baseline</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-shield-base border border-shield-border">
              <span className="text-shield-text">2. Linear SVM</span>
              <span className="text-shield-subtle">High-Dimensional Sparse</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-shield-base border border-shield-border">
              <span className="text-shield-subtle">3. Random Forest</span>
              <span className="text-shield-subtle">Ensemble Non-Linear</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-shield-base border border-shield-border">
              <span className="text-shield-text">4. XGBoost</span>
              <span className="text-shield-subtle">Gradient Boosted Trees</span>
            </div>
          </div>

          <div className="pt-1 text-[11px] font-mono text-shield-subtle">
            Selection Criteria: Maximum PR-AUC on Validation Set.
          </div>
        </section>

        {/* Analysis Session / Recent Activity Empty State */}
        <section className="p-5 rounded-lg bg-shield-card border border-shield-border flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-shield-border pb-3 mb-4">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-[#D9B100]" />
                <h3 className="text-sm font-semibold text-shield-text">
                  Recent Inferences
                </h3>
              </div>
              <span className="text-[11px] font-mono text-shield-subtle">
                Session Log
              </span>
            </div>

            <EmptyState
              icon={FileSearch}
              title="No Inferences Recorded"
              description="No job postings have been submitted for analysis during this session."
              technicalNote="Subsequent phases will persist session evaluation telemetry and SQLite history."
              actionButton={
                <Link
                  to="/analyze"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-shield-surface/60 hover:bg-shield-surface text-shield-text text-xs font-medium border border-shield-border transition-colors"
                >
                  <span>Go to Analyze Job</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              }
            />
          </div>
        </section>
      </div>
    </div>
  );
}
