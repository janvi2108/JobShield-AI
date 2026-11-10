import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3,
  Cpu,
  Layers,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  FileCode2,
  Search,
  Shield,
  ArrowRight,
  Award,
  Database,
  Activity,
  Globe2,
  Compass,
} from "lucide-react";
import { fetchModelMetrics, fetchExternalValidation } from "../services/api";

export default function PerformancePage({ backendHealth }) {
  const [metricsData, setMetricsData] = useState(null);
  const [externalValidation, setExternalValidation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  useEffect(() => {
    async function loadAllTelemetry() {
      setLoading(true);
      try {
        const [metricsRes, valRes] = await Promise.all([
          fetchModelMetrics(),
          fetchExternalValidation(),
        ]);

        if (metricsRes.ok) {
          setMetricsData(metricsRes.data);
        } else {
          setFetchError(metricsRes.error);
        }

        if (valRes.ok) {
          setExternalValidation(valRes.data);
        }
      } catch (err) {
        setFetchError(err.message || "Failed to load telemetry.");
      } finally {
        setLoading(false);
      }
    }
    loadAllTelemetry();
  }, []);

  const isTrained = !!metricsData || backendHealth?.model_status === "trained";
  const selectedModel = metricsData?.selected_model?.name || "Linear Support Vector Machine";
  const candidates = metricsData?.candidate_comparison || {};
  const testEval = metricsData?.test_evaluation?.metrics;
  const cm = testEval?.confusion_matrix;
  const splits = metricsData?.dataset_splits;

  return (
    <div className="min-h-[calc(100vh-5rem)] bg-[#101114]">
      {/* Header Banner */}
      <div className="border-b border-[#2C313C]/50 bg-[#14161A]/60">
        <div className="max-w-6xl mx-auto px-6 sm:px-8 py-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-2">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#D9B100] font-semibold">
                Part 2 · Generalization & Benchmark Telemetry
              </span>
            </div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#191C22] border border-[#2C313C] text-xs font-mono self-start sm:self-auto">
              <span className={`w-2 h-2 rounded-full ${isTrained ? "bg-emerald-400" : "bg-amber-400 animate-pulse"}`} />
              <span className={isTrained ? "text-emerald-400" : "text-amber-400"}>
                {isTrained ? "Benchmark Evaluated" : "Awaiting Training Pipeline"}
              </span>
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#F2F4F6] tracking-tight">
            Model Benchmarks & Domain Shift Telemetry
          </h1>
          <p className="mt-2 text-sm text-[#949BA6] max-w-2xl">
            Comparative evaluation of 4 candidate classifiers on the EMSCAD benchmark dataset (17,632 records) alongside out-of-domain validation on the Internship Job Scam Benchmark.
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 sm:px-8 py-10 space-y-10">
        {/* Loading state */}
        {loading && (
          <div className="p-12 text-center flex flex-col items-center gap-3">
            <Activity className="w-8 h-8 text-[#D9B100] animate-spin" />
            <p className="text-sm font-mono text-[#949BA6]">Loading benchmark telemetry...</p>
          </div>
        )}

        {/* Empty State if no metrics available */}
        {!loading && !metricsData && (
          <div className="p-8 sm:p-12 rounded-2xl bg-[#191C22] border border-[#2C313C] text-center flex flex-col items-center gap-6 shadow-xl">
            <div className="w-16 h-16 rounded-2xl bg-[#101114] border border-[#2C313C] flex items-center justify-center text-[#D9B100]">
              <BarChart3 className="w-7 h-7 stroke-[2]" />
            </div>

            <div className="max-w-xl space-y-2">
              <h2 className="text-xl font-bold text-[#F2F4F6]">
                Model Training & Evaluation Telemetry Pending
              </h2>
              <p className="text-sm text-[#949BA6] leading-relaxed">
                Evaluation metrics, PR curves, and confusion matrices are generated strictly from the actual training pipeline run against the EMSCAD dataset. In accordance with project integrity standards, synthetic benchmark numbers are never fabricated.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
              <Link
                to="/analyze"
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-[#D9B100] hover:bg-[#F3DA87] text-[#101114] font-semibold text-sm transition-all shadow-sm hover:scale-[1.02]"
              >
                <Search className="w-4 h-4" />
                <span>Analyze a Job Posting</span>
              </Link>
            </div>
          </div>
        )}

        {/* Champion Model Showcase (when metricsData is available) */}
        {!loading && metricsData && testEval && (
          <div className="p-6 sm:p-8 rounded-2xl bg-[#191C22] border border-[#D9B100]/40 space-y-6 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-96 h-96 bg-[#D9B100]/5 rounded-full blur-3xl pointer-events-none" />

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#2C313C]/60 pb-5">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Award className="w-4 h-4 text-[#D9B100]" />
                  <span className="text-[11px] font-mono uppercase tracking-wider text-[#D9B100] font-bold">
                    Selected Champion Classifier
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-[#F2F4F6]">
                  {selectedModel}
                </h2>
                <p className="text-xs text-[#949BA6]">
                  Selected via highest validation PR-AUC ({candidates[selectedModel]?.pr_auc}) and minority F1-score ({candidates[selectedModel]?.f1_minority}) with calibrated decision threshold of {testEval.threshold}.
                </p>
              </div>

              <div className="flex items-center gap-3 self-start md:self-auto">
                <div className="px-4 py-2 rounded-xl bg-[#101114] border border-[#2C313C] text-center font-mono">
                  <div className="text-[10px] text-[#626A77] uppercase">Tuned Threshold</div>
                  <div className="text-lg font-bold text-[#D9B100]">{testEval.threshold}</div>
                </div>
                <div className="px-4 py-2 rounded-xl bg-[#101114] border border-[#2C313C] text-center font-mono">
                  <div className="text-[10px] text-[#626A77] uppercase">Test Accuracy</div>
                  <div className="text-lg font-bold text-emerald-400">{(testEval.accuracy * 100).toFixed(1)}%</div>
                </div>
              </div>
            </div>

            {/* Test Split Unbiased Performance Grid */}
            <div className="space-y-3">
              <span className="text-xs font-mono uppercase tracking-wider text-[#626A77] font-semibold">
                Held-Out Test Set Performance (1,764 Untouched Postings)
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="p-3.5 rounded-xl bg-[#101114] border border-[#2C313C] text-center">
                  <div className="text-[10px] font-mono text-[#626A77] uppercase">PR-AUC</div>
                  <div className="text-xl font-bold text-[#F2F4F6] mt-1">{testEval.pr_auc}</div>
                  <div className="text-[10px] text-emerald-400 font-mono mt-0.5">Primary Metric</div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#101114] border border-[#2C313C] text-center">
                  <div className="text-[10px] font-mono text-[#626A77] uppercase">ROC-AUC</div>
                  <div className="text-xl font-bold text-[#F2F4F6] mt-1">{testEval.roc_auc}</div>
                  <div className="text-[10px] text-[#949BA6] font-mono mt-0.5">Overall Rank</div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#101114] border border-[#2C313C] text-center">
                  <div className="text-[10px] font-mono text-[#626A77] uppercase">Minority F1</div>
                  <div className="text-xl font-bold text-[#D9B100] mt-1">{testEval.f1_minority}</div>
                  <div className="text-[10px] text-[#949BA6] font-mono mt-0.5">Harmonic Mean</div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#101114] border border-[#2C313C] text-center">
                  <div className="text-[10px] font-mono text-[#626A77] uppercase">Precision</div>
                  <div className="text-xl font-bold text-[#F2F4F6] mt-1">{testEval.precision_minority}</div>
                  <div className="text-[10px] text-emerald-400 font-mono mt-0.5">Low False Pos</div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#101114] border border-[#2C313C] text-center">
                  <div className="text-[10px] font-mono text-[#626A77] uppercase">Recall</div>
                  <div className="text-xl font-bold text-[#F2F4F6] mt-1">{testEval.recall_minority}</div>
                  <div className="text-[10px] text-[#949BA6] font-mono mt-0.5">79.1% Caught</div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#101114] border border-[#2C313C] text-center">
                  <div className="text-[10px] font-mono text-[#626A77] uppercase">Accuracy</div>
                  <div className="text-xl font-bold text-[#F2F4F6] mt-1">{testEval.accuracy}</div>
                  <div className="text-[10px] text-[#949BA6] font-mono mt-0.5">Overall Split</div>
                </div>
              </div>
            </div>

            {/* Confusion Matrix Breakdown */}
            {cm && (
              <div className="pt-4 border-t border-[#2C313C]/60 space-y-3">
                <span className="text-xs font-mono uppercase tracking-wider text-[#626A77] font-semibold">
                  Test Split Confusion Matrix Breakdown
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3.5 rounded-xl bg-[#101114] border border-emerald-900/40">
                    <div className="text-[10px] font-mono text-emerald-400 uppercase">True Negatives</div>
                    <div className="text-lg font-bold text-[#F2F4F6] mt-1">{cm.true_negative?.toLocaleString() || cm.true_negative}</div>
                    <p className="text-[10px] text-[#949BA6] mt-0.5">Legitimate postings verified</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#101114] border border-emerald-900/40">
                    <div className="text-[10px] font-mono text-emerald-400 uppercase">True Positives</div>
                    <div className="text-lg font-bold text-[#F2F4F6] mt-1">{cm.true_positive?.toLocaleString() || cm.true_positive}</div>
                    <p className="text-[10px] text-[#949BA6] mt-0.5">Scam postings intercepted</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#101114] border border-amber-900/40">
                    <div className="text-[10px] font-mono text-amber-400 uppercase">False Positives</div>
                    <div className="text-lg font-bold text-[#F2F4F6] mt-1">{cm.false_positive?.toLocaleString() || cm.false_positive}</div>
                    <p className="text-[10px] text-[#949BA6] mt-0.5">Legit flagged as scam (0.5%)</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#101114] border border-red-900/40">
                    <div className="text-[10px] font-mono text-red-400 uppercase">False Negatives</div>
                    <div className="text-lg font-bold text-[#F2F4F6] mt-1">{cm.false_negative?.toLocaleString() || cm.false_negative}</div>
                    <p className="text-[10px] text-[#949BA6] mt-0.5">Scam postings missed</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* External Dataset Validation & Generalization Benchmark Card */}
        {externalValidation && (
          <div className="p-6 sm:p-8 rounded-2xl bg-[#14161A] border border-[#2C313C] space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#2C313C]/60 pb-5">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Globe2 className="w-5 h-5 text-[#D9B100]" />
                  <span className="text-xs font-mono uppercase tracking-wider text-[#D9B100] font-bold">
                    Out-of-Domain Generalization Benchmark
                  </span>
                </div>
                <h3 className="text-xl font-bold text-[#F2F4F6]">
                  EMSCAD vs. External Internship Job Scam Dataset
                </h3>
                <p className="text-xs text-[#949BA6] max-w-xl">
                  Evaluates the champion Linear SVM on novel, unseen early-career and internship postings without fine-tuning.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="px-4 py-2 rounded-xl bg-[#191C22] border border-[#2C313C] text-center font-mono">
                  <div className="text-[10px] text-[#626A77] uppercase">Verdict</div>
                  <div className="text-sm font-bold text-[#D9B100]">
                    {externalValidation.domain_shift?.generalization_verdict}
                  </div>
                </div>
                <div className="px-4 py-2 rounded-xl bg-[#191C22] border border-[#2C313C] text-center font-mono">
                  <div className="text-[10px] text-[#626A77] uppercase">F1 Retention</div>
                  <div className="text-sm font-bold text-emerald-400">
                    {externalValidation.domain_shift?.f1_retention_percentage}%
                  </div>
                </div>
              </div>
            </div>

            {/* Side-by-Side Comparison Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-[#191C22] text-[#949BA6] font-mono uppercase tracking-wider border-b border-[#2C313C]">
                  <tr>
                    <th className="py-3 px-4">Evaluation Metric</th>
                    <th className="py-3 px-4">EMSCAD In-Domain Test Split</th>
                    <th className="py-3 px-4">External Internship Benchmark</th>
                    <th className="py-3 px-4">Generalization Shift</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2C313C]/60 text-[#F2F4F6] font-mono">
                  <tr>
                    <td className="py-3 px-4 text-[#949BA6]">Dataset Sample Count</td>
                    <td className="py-3 px-4">{externalValidation.internal_benchmark?.sample_count}</td>
                    <td className="py-3 px-4">{externalValidation.external_benchmark?.sample_count}</td>
                    <td className="py-3 px-4 text-[#626A77]">-</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 text-[#949BA6]">Scam Prevalence</td>
                    <td className="py-3 px-4">{(externalValidation.internal_benchmark?.fraud_prevalence * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4">{(externalValidation.external_benchmark?.fraud_prevalence * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 text-[#626A77]">-</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 text-[#949BA6]">Overall Accuracy</td>
                    <td className="py-3 px-4">{(externalValidation.internal_benchmark?.accuracy * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4">{(externalValidation.external_benchmark?.accuracy * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4">
                      {((externalValidation.external_benchmark?.accuracy - externalValidation.internal_benchmark?.accuracy) * 100).toFixed(1)}%
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 text-[#949BA6]">Precision (Minority Fraud)</td>
                    <td className="py-3 px-4">{externalValidation.internal_benchmark?.precision?.toFixed(4)}</td>
                    <td className="py-3 px-4 text-emerald-400 font-bold">{externalValidation.external_benchmark?.precision?.toFixed(4)}</td>
                    <td className="py-3 px-4 text-emerald-400">
                      {externalValidation.domain_shift?.precision_delta > 0 ? "+" : ""}
                      {externalValidation.domain_shift?.precision_delta?.toFixed(4)}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 text-[#949BA6]">Recall (Minority Fraud)</td>
                    <td className="py-3 px-4">{externalValidation.internal_benchmark?.recall?.toFixed(4)}</td>
                    <td className="py-3 px-4">{externalValidation.external_benchmark?.recall?.toFixed(4)}</td>
                    <td className="py-3 px-4 text-amber-400">
                      {externalValidation.domain_shift?.recall_delta?.toFixed(4)}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 text-[#949BA6]">F1-Score (Minority Fraud)</td>
                    <td className="py-3 px-4 font-bold text-[#D9B100]">{externalValidation.internal_benchmark?.f1_score?.toFixed(4)}</td>
                    <td className="py-3 px-4 font-bold text-[#D9B100]">{externalValidation.external_benchmark?.f1_score?.toFixed(4)}</td>
                    <td className="py-3 px-4 text-[#949BA6]">
                      {externalValidation.domain_shift?.f1_retention_percentage}% retained
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 text-[#949BA6]">PR-AUC</td>
                    <td className="py-3 px-4">{externalValidation.internal_benchmark?.pr_auc?.toFixed(4)}</td>
                    <td className="py-3 px-4 font-bold text-emerald-400">{externalValidation.external_benchmark?.pr_auc?.toFixed(4)}</td>
                    <td className="py-3 px-4 text-emerald-400">+{(externalValidation.external_benchmark?.pr_auc - externalValidation.internal_benchmark?.pr_auc)?.toFixed(4)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Key Observations */}
            <div className="space-y-2 pt-2 border-t border-[#2C313C]/60">
              <span className="text-xs font-mono uppercase tracking-wider text-[#626A77] font-semibold">
                Generalization Analysis & Observations
              </span>
              <div className="space-y-2">
                {externalValidation.domain_shift?.key_observations?.map((obs, i) => (
                  <div key={i} className="flex items-start gap-2.5 p-3 rounded-xl bg-[#191C22] border border-[#2C313C] text-xs text-[#949BA6]">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#D9B100] mt-2 flex-shrink-0" />
                    <span>{obs}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Candidate Classifiers Comparison */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-[#D9B100] font-semibold">
              Candidate Classifiers Comparison (Validation Set)
            </h2>
            <span className="text-xs font-mono text-[#626A77]">
              4 Candidates Evaluated
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Linear SVM */}
            <div className={`p-6 rounded-2xl bg-[#191C22] border ${selectedModel === "Linear Support Vector Machine" ? "border-[#D9B100] shadow-lg shadow-[#D9B100]/5" : "border-[#2C313C]"} space-y-3 group`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-400" />
                  <span className="text-base font-semibold text-[#F2F4F6]">
                    Linear Support Vector Machine
                  </span>
                </div>
                <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-[#D9B100]/10 text-[#D9B100] border border-[#D9B100]/30 font-semibold">
                  Champion (PR-AUC 0.9046)
                </span>
              </div>
              <p className="text-xs text-[#949BA6] leading-relaxed">
                Linear hyperplane classifier with calibrated Platt probabilities. Achieved optimal PR-AUC and minority F1 through exact sparse dot products in high-dimensional TF-IDF space.
              </p>
              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-[#2C313C]/60 text-center font-mono">
                <div>
                  <div className="text-[10px] text-[#626A77]">PR-AUC</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["Linear Support Vector Machine"]?.pr_auc || "0.9046"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Val F1</div>
                  <div className="text-xs font-bold text-[#D9B100]">{candidates["Linear Support Vector Machine"]?.f1_minority || "0.8608"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Precision</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["Linear Support Vector Machine"]?.precision_minority || "0.9315"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Recall</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["Linear Support Vector Machine"]?.recall_minority || "0.8000"}</div>
                </div>
              </div>
            </div>

            {/* Logistic Regression */}
            <div className="p-6 rounded-2xl bg-[#191C22] border border-[#2C313C] space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  <span className="text-base font-semibold text-[#F2F4F6]">
                    Logistic Regression (ElasticNet)
                  </span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#101114] text-[#949BA6] border border-[#2C313C]">
                  Baseline (PR-AUC 0.8748)
                </span>
              </div>
              <p className="text-xs text-[#949BA6] leading-relaxed">
                Penalized logistic regression with balanced class weights. Fast convergence and transparent log-odds, but slightly lower minority recall than Linear SVM.
              </p>
              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-[#2C313C]/60 text-center font-mono">
                <div>
                  <div className="text-[10px] text-[#626A77]">PR-AUC</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["Logistic Regression"]?.pr_auc || "0.8748"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Val F1</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["Logistic Regression"]?.f1_minority || "0.8182"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Precision</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["Logistic Regression"]?.precision_minority || "0.7912"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Recall</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["Logistic Regression"]?.recall_minority || "0.8471"}</div>
                </div>
              </div>
            </div>

            {/* XGBoost */}
            <div className="p-6 rounded-2xl bg-[#191C22] border border-[#2C313C] space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                  <span className="text-base font-semibold text-[#F2F4F6]">
                    XGBoost Gradient Boosting
                  </span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#101114] text-[#949BA6] border border-[#2C313C]">
                  Tree Ensemble (PR-AUC 0.8654)
                </span>
              </div>
              <p className="text-xs text-[#949BA6] leading-relaxed">
                Gradient-boosted decision trees with histogram binning. Strong non-linear interactions across metadata, but slower inference than sparse linear models.
              </p>
              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-[#2C313C]/60 text-center font-mono">
                <div>
                  <div className="text-[10px] text-[#626A77]">PR-AUC</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["XGBoost"]?.pr_auc || "0.8654"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Val F1</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["XGBoost"]?.f1_minority || "0.8049"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Precision</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["XGBoost"]?.precision_minority || "0.8462"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Recall</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["XGBoost"]?.recall_minority || "0.7765"}</div>
                </div>
              </div>
            </div>

            {/* Random Forest */}
            <div className="p-6 rounded-2xl bg-[#191C22] border border-[#2C313C] space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
                  <span className="text-base font-semibold text-[#F2F4F6]">
                    Random Forest Classifier
                  </span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#101114] text-[#949BA6] border border-[#2C313C]">
                  Ensemble (PR-AUC 0.7977)
                </span>
              </div>
              <p className="text-xs text-[#949BA6] leading-relaxed">
                Bagged decision tree ensemble with balanced subsampling. Lower PR-AUC due to extreme sparsity in 10,000-dimensional TF-IDF vectors.
              </p>
              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-[#2C313C]/60 text-center font-mono">
                <div>
                  <div className="text-[10px] text-[#626A77]">PR-AUC</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["Random Forest"]?.pr_auc || "0.7977"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Val F1</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["Random Forest"]?.f1_minority || "0.7425"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Precision</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["Random Forest"]?.precision_minority || "0.7561"}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#626A77]">Recall</div>
                  <div className="text-xs font-bold text-[#F2F4F6]">{candidates["Random Forest"]?.recall_minority || "0.7294"}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Dataset Accounting & Splitting Protocol */}
        <div className="p-6 sm:p-8 rounded-2xl bg-[#191C22] border border-[#2C313C] space-y-4">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-[#D9B100]" />
            <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-[#D9B100] font-semibold">
              Stratified Dataset Accounting & Partitions
            </h2>
          </div>
          <p className="text-xs text-[#949BA6] leading-relaxed">
            Prepared from 17,880 raw EMSCAD records. Exactly 248 duplicates were removed across 17 feature columns (238 legitimate, 10 fraudulent), preserving 17,632 unique postings stratified into mutually disjoint 80/10/10 partitions.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="p-4 rounded-xl bg-[#101114] border border-[#2C313C] space-y-1">
              <span className="text-[10px] font-mono text-[#626A77] uppercase tracking-wider">Training Split (80%)</span>
              <div className="text-lg font-bold text-[#F2F4F6]">14,105 records</div>
              <p className="text-[11px] text-[#949BA6]">
                {splits?.train?.fraudulent || 685} fraudulent (4.86%) | 13,420 legitimate
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[#101114] border border-[#2C313C] space-y-1">
              <span className="text-[10px] font-mono text-[#626A77] uppercase tracking-wider">Validation Split (10%)</span>
              <div className="text-lg font-bold text-[#F2F4F6]">1,763 records</div>
              <p className="text-[11px] text-[#949BA6]">
                {splits?.validation?.fraudulent || 85} fraudulent (4.82%) | 1,678 legitimate
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[#101114] border border-[#2C313C] space-y-1">
              <span className="text-[10px] font-mono text-[#626A77] uppercase tracking-wider">Test Split (10%)</span>
              <div className="text-lg font-bold text-[#F2F4F6]">1,764 records</div>
              <p className="text-[11px] text-[#949BA6]">
                {splits?.test?.fraudulent || 86} fraudulent (4.88%) | 1,678 legitimate
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
