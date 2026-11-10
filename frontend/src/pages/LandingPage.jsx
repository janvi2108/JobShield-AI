import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight, Shield, ShieldAlert, ShieldCheck, Brain, AlertTriangle,
  BarChart3, Zap, Eye, ChevronDown, CheckCircle2, FileText, Search,
  TrendingUp, Lock, Globe, Clock, Star, MessageSquare, DollarSign, Phone,
} from "lucide-react";

const SECTION = "relative z-10 max-w-6xl mx-auto px-6 sm:px-8";

function AmbientGlow({ className, style }) {
  return <div aria-hidden="true" className={`pointer-events-none absolute rounded-full blur-[120px] ${className}`} style={style} />;
}
function Eyebrow({ children }) {
  return <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-[11px] font-mono font-semibold uppercase tracking-[0.2em] text-[#F3DA87] border-[#D9B100]/25 bg-[#D9B100]/5">{children}</span>;
}
function FAQItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-[#2C313C]/60">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between gap-4 py-5 text-left group focus-visible:outline-none">
        <span className="text-sm font-medium text-[#F2F4F6] group-hover:text-white transition-colors">{q}</span>
        <ChevronDown className={`w-4 h-4 text-[#626A77] flex-shrink-0 transition-transform duration-200 ${open ? "rotate-180 text-[#D9B100]" : ""}`} />
      </button>
      {open && <p className="pb-5 text-sm text-[#949BA6] leading-relaxed">{a}</p>}
    </div>
  );
}
function RiskSignal({ icon: Icon, label, severity }) {
  const colors = { high: "text-red-400 border-red-800/60 bg-red-950/20", medium: "text-amber-400 border-amber-800/60 bg-amber-950/20" };
  return (
    <div className={`flex items-center gap-2.5 px-3 py-2 rounded-lg border text-xs font-medium ${colors[severity]}`}>
      <Icon className="w-3.5 h-3.5 flex-shrink-0" />{label}
    </div>
  );
}
function StatCard({ value, label, sub }) {
  return (
    <div className="flex flex-col items-center text-center gap-1">
      <div className="text-4xl sm:text-5xl font-bold text-[#F3DA87] tracking-tight tabular-nums">{value}</div>
      <div className="text-sm font-semibold text-[#F2F4F6]">{label}</div>
      {sub && <div className="text-xs text-[#626A77]">{sub}</div>}
    </div>
  );
}
function UseCaseCard({ icon: Icon, title, desc, tag }) {
  return (
    <div className="group p-6 rounded-2xl bg-[#191C22] border border-[#2C313C] hover:border-[#D9B100]/30 hover:bg-[#1C1F27] transition-all duration-300">
      <div className="w-10 h-10 rounded-xl bg-[#D9B100]/10 border border-[#D9B100]/20 flex items-center justify-center text-[#D9B100] mb-4 group-hover:border-[#D9B100]/40 transition-colors">
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-sm font-semibold text-[#F2F4F6]">{title}</h3>
        <span className="text-[10px] font-mono font-semibold text-[#626A77] uppercase tracking-wider">{tag}</span>
      </div>
      <p className="text-xs text-[#949BA6] leading-relaxed">{desc}</p>
    </div>
  );
}
function WorkflowStep({ num, title, desc, icon: Icon }) {
  return (
    <div className="flex gap-5 items-start">
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-[#D9B100]/10 border border-[#D9B100]/30 flex items-center justify-center">
        <Icon className="w-4 h-4 text-[#D9B100]" />
      </div>
      <div className="flex-1 pt-1">
        <div className="text-[10px] font-mono text-[#D9B100]/70 font-bold mb-1">STEP {num}</div>
        <h4 className="text-sm font-semibold text-[#F2F4F6] mb-1">{title}</h4>
        <p className="text-xs text-[#949BA6] leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="bg-[#101114] text-[#F2F4F6] overflow-hidden selection:bg-[#D9B100]/20 selection:text-[#F3DA87]">

      {/* HERO */}
      <section className="relative min-h-[calc(100vh-5rem)] flex flex-col items-center justify-center text-center px-6 sm:px-8 pt-12 pb-24">
        <AmbientGlow className="-top-40 left-1/2 -translate-x-1/2 w-[1200px] h-[500px] opacity-30" style={{ background: "radial-gradient(ellipse, rgba(217,177,0,0.18) 0%, rgba(59,63,70,0.12) 40%, transparent 70%)" }} />
        <AmbientGlow className="top-1/3 left-1/4 w-[400px] h-[400px] opacity-15" style={{ background: "radial-gradient(circle, rgba(217,177,0,0.25) 0%, transparent 70%)" }} />
        <div className="relative z-10 max-w-5xl mx-auto">
          <div className="flex justify-center mb-7"><Eyebrow>AI-Powered Job Fraud Detection</Eyebrow></div>
          <h1 className="text-5xl sm:text-7xl lg:text-[5.75rem] font-bold tracking-[-0.035em] leading-[1.02] text-[#F2F4F6]">
            <span className="block">Know the Risk.</span>
            <span className="block mt-1">Before You <span className="relative inline-block">Apply.<span aria-hidden="true" className="absolute -bottom-1 left-0 right-0 h-[3px] rounded-full" style={{ background: "linear-gradient(90deg, #D9B100, #F3DA87, #D9B100)" }} /></span></span>
          </h1>
          <p className="mt-8 text-lg sm:text-xl text-[#949BA6] max-w-2xl mx-auto leading-relaxed">
            JobShield AI analyzes job and internship postings using machine learning trained on the <span className="text-[#F2F4F6] font-medium">EMSCAD dataset</span> — 17,880 real postings — to detect employment fraud before you invest your time.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/analyze" className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-4 rounded-full bg-[#D9B100] hover:bg-[#e5bc05] text-[#101114] font-bold text-sm sm:text-base transition-all duration-200 shadow-xl shadow-[#D9B100]/20 hover:shadow-[#D9B100]/35 hover:scale-[1.03]">
              <Search className="w-4 h-4 stroke-[2.5]" />Analyze a Job Posting
            </Link>
            <Link to="/performance" className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-[#191C22]/80 hover:bg-[#21252D] text-[#F2F4F6] font-medium text-sm sm:text-base border border-[#3B3F46] hover:border-[#626A77] hover:scale-[1.02] transition-all duration-200">
              View Model Performance<ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-xs text-[#626A77] font-mono">
            {[["17,880 training samples"],["EMSCAD dataset"],["SHAP explainability"],["Open ML pipeline"]].map(([t]) => (
              <div key={t} className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-[#D9B100]" />{t}</div>
            ))}
          </div>
        </div>
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5 text-[#3B3F46]">
          <span className="text-[10px] font-mono uppercase tracking-[0.2em]">Scroll</span>
          <ChevronDown className="w-4 h-4 animate-bounce" />
        </div>
      </section>

      {/* STATS BAND */}
      <section className="border-y border-[#2C313C]/50 bg-[#14161A]/60 py-12 sm:py-16">
        <div className={SECTION}>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 sm:gap-12">
            <StatCard value="17,880" label="Job Postings" sub="EMSCAD dataset" />
            <StatCard value="866" label="Fraud Cases" sub="4.84% prevalence" />
            <StatCard value="4" label="ML Models" sub="Compared and evaluated" />
            <StatCard value="SHAP" label="Explainability" sub="Per-token attribution" />
          </div>
        </div>
      </section>

      {/* CORE CAPABILITIES */}
      <section id="capabilities" className="relative py-24 sm:py-32">
        <AmbientGlow className="top-20 right-0 w-[500px] h-[400px] opacity-10" style={{ background: "radial-gradient(circle, rgba(217,177,0,0.3) 0%, transparent 65%)" }} />
        <div className={SECTION}>
          <div className="flex flex-col items-start mb-14">
            <Eyebrow>Core Detection Engine</Eyebrow>
            <h2 className="mt-5 text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[#F2F4F6]">Built on real fraud patterns.<br /><span className="text-[#D9B100]">Explained transparently.</span></h2>
            <p className="mt-5 text-base text-[#949BA6] max-w-2xl leading-relaxed">Every prediction is backed by explainable AI — you see exactly which words and patterns triggered the fraud signal, not just a probability score.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { icon: Brain, num: "01", title: "TF-IDF Text Extraction", desc: "Converts raw job posting text into high-dimensional feature vectors, capturing unigrams and bigrams that distinguish fraud from legitimate postings." },
              { icon: ShieldAlert, num: "02", title: "ML Classification", desc: "Four candidate classifiers — Logistic Regression, Linear SVM, Random Forest, and XGBoost — trained on the EMSCAD dataset with stratified cross-validation." },
              { icon: Eye, num: "03", title: "SHAP Explainability", desc: "SHAP LinearExplainer or TreeExplainer generates per-token attribution scores, revealing exactly which phrases increased or decreased the fraud probability." },
            ].map(({ icon: Icon, num, title, desc }) => (
              <div key={num} className="group p-7 rounded-2xl bg-[#191C22] border border-[#2C313C] hover:border-[#D9B100]/30 hover:bg-[#1C1F27] transition-all duration-300">
                <div className="flex items-center justify-between mb-5">
                  <div className="w-11 h-11 rounded-xl bg-[#D9B100]/10 border border-[#D9B100]/20 flex items-center justify-center text-[#D9B100] group-hover:border-[#D9B100]/50 transition-colors"><Icon className="w-5 h-5" /></div>
                  <span className="text-xs font-mono font-bold text-[#D9B100]/50">{num}</span>
                </div>
                <h3 className="text-base font-semibold text-[#F2F4F6] mb-2.5">{title}</h3>
                <p className="text-sm text-[#949BA6] leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="py-24 sm:py-32 border-t border-[#2C313C]/40">
        <div className={SECTION}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
            <div>
              <Eyebrow>How It Works</Eyebrow>
              <h2 className="mt-5 text-3xl sm:text-4xl font-bold tracking-tight text-[#F2F4F6]">Four steps.<br />Full transparency.</h2>
              <p className="mt-5 text-base text-[#949BA6] leading-relaxed">From raw posting text to a fully explained fraud verdict in seconds.</p>
              <div className="mt-10 space-y-8">
                <WorkflowStep num="1" icon={FileText} title="Paste the job posting" desc="Copy the full text of any job listing, internship offer, or recruiter message into the Analyze form." />
                <WorkflowStep num="2" icon={Zap} title="TF-IDF feature extraction" desc="The backend vectorizes your text using the trained TF-IDF pipeline, extracting thousands of weighted n-gram features." />
                <WorkflowStep num="3" icon={Brain} title="ML inference & probability score" desc="The winning classifier outputs a calibrated fraud probability score between 0 and 100%." />
                <WorkflowStep num="4" icon={Eye} title="SHAP attribution breakdown" desc="See exactly which tokens pushed the score up or down — no black box, complete explainability." />
              </div>
            </div>

            {/* Live mock result card */}
            <div className="lg:sticky lg:top-24">
              <div className="rounded-2xl border border-[#2C313C] bg-[#14161A] overflow-hidden shadow-2xl shadow-black/40">
                <div className="px-5 py-3 bg-[#191C22] border-b border-[#2C313C] flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#3B3F46]" />
                    <span className="w-2.5 h-2.5 rounded-full bg-[#3B3F46]" />
                    <span className="w-2.5 h-2.5 rounded-full bg-[#D9B100]/40" />
                  </div>
                  <span className="text-[11px] font-mono text-[#626A77] ml-2">jobshield-ai / results</span>
                </div>
                <div className="p-6 space-y-5">
                  <div className="p-4 rounded-xl bg-red-950/25 border border-red-800/50 flex items-start gap-3">
                    <ShieldAlert className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="text-xs font-mono text-red-400/70 uppercase tracking-wide mb-0.5">High Risk Detected</div>
                      <div className="text-sm font-semibold text-[#F2F4F6]">Potentially Fraudulent Posting</div>
                      <div className="mt-1 text-xs text-[#949BA6]">Multiple risk indicators found in this posting.</div>
                    </div>
                    <div className="ml-auto pl-4 text-center">
                      <div className="text-2xl font-bold text-red-400">87.3%</div>
                      <div className="text-[10px] text-[#626A77]">fraud prob.</div>
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] font-mono text-[#626A77] uppercase tracking-wider mb-3">Risk Signals Detected</div>
                    <div className="flex flex-wrap gap-2">
                      <RiskSignal icon={DollarSign} label="Upfront payment request" severity="high" />
                      <RiskSignal icon={Phone} label="WhatsApp contact only" severity="high" />
                      <RiskSignal icon={Globe} label="No company domain" severity="medium" />
                      <RiskSignal icon={Clock} label="Urgency language" severity="medium" />
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] font-mono text-[#626A77] uppercase tracking-wider mb-3">Top SHAP Attributions</div>
                    <div className="space-y-2">
                      {[{ word: '"send money"', weight: 0.92 }, { word: '"work from home"', weight: 0.71 }, { word: '"no experience needed"', weight: 0.58 }].map(({ word, weight }) => (
                        <div key={word} className="flex items-center gap-3">
                          <code className="text-xs text-[#F3DA87] font-mono bg-[#1C1F27] px-2 py-0.5 rounded min-w-[160px]">{word}</code>
                          <div className="flex-1 h-1.5 rounded-full bg-[#2C313C]"><div className="h-full rounded-full bg-red-500" style={{ width: `${weight * 100}%` }} /></div>
                          <span className="text-xs font-mono text-red-400">+{weight.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* RISK SIGNALS */}
      <section className="py-24 sm:py-32 border-t border-[#2C313C]/40">
        <div className={SECTION}>
          <div className="text-center mb-14">
            <Eyebrow>What We Detect</Eyebrow>
            <h2 className="mt-5 text-3xl sm:text-4xl font-bold tracking-tight text-[#F2F4F6]">Common fraud patterns in job postings</h2>
            <p className="mt-4 text-base text-[#949BA6] max-w-xl mx-auto">Our model was trained on real fraud cases. Here are the patterns it has learned to recognize.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { icon: DollarSign, title: "Upfront Payment Requests", desc: "Demands for registration fees, training kits, or equipment deposits before starting work.", severity: "CRITICAL", cls: "text-red-400 bg-red-950/20 border-red-800/40" },
              { icon: Phone, title: "Off-Platform Communication", desc: "Pressure to move to WhatsApp, Telegram, or personal email for confidential processes.", severity: "HIGH", cls: "text-amber-400 bg-amber-950/20 border-amber-800/40" },
              { icon: Globe, title: "Missing Company Details", desc: "No verifiable company name, domain email, or LinkedIn — classic anonymity tactics.", severity: "HIGH", cls: "text-amber-400 bg-amber-950/20 border-amber-800/40" },
              { icon: Clock, title: "Artificial Urgency", desc: "Phrases like limited spots, apply today only, or 24-hour deadline to rush decisions.", severity: "MEDIUM", cls: "text-yellow-500 bg-yellow-950/20 border-yellow-800/40" },
              { icon: Star, title: "Unrealistic Compensation", desc: "Entry-level roles promising thousands per week with no skills required.", severity: "HIGH", cls: "text-amber-400 bg-amber-950/20 border-amber-800/40" },
              { icon: MessageSquare, title: "Vague Job Descriptions", desc: "Extremely short or generic postings with no specific responsibilities or requirements.", severity: "MEDIUM", cls: "text-yellow-500 bg-yellow-950/20 border-yellow-800/40" },
            ].map(({ icon: Icon, title, desc, severity, cls }) => (
              <div key={title} className="group p-5 rounded-xl bg-[#191C22] border border-[#2C313C] hover:border-[#3B3F46] transition-all">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-[#D9B100]/8 border border-[#D9B100]/15 flex items-center justify-center text-[#D9B100]"><Icon className="w-4 h-4" /></div>
                  <span className={`text-[9px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${cls}`}>{severity}</span>
                </div>
                <h3 className="text-sm font-semibold text-[#F2F4F6] mb-1.5">{title}</h3>
                <p className="text-xs text-[#949BA6] leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* USE CASES */}
      <section className="py-24 sm:py-32 border-t border-[#2C313C]/40 bg-[#14161A]/40">
        <div className={SECTION}>
          <div className="flex flex-col items-start mb-12">
            <Eyebrow>Use Cases</Eyebrow>
            <h2 className="mt-5 text-3xl sm:text-4xl font-bold tracking-tight text-[#F2F4F6]">Who benefits from JobShield AI?</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <UseCaseCard icon={Search} title="Job Seekers" tag="Primary" desc="Verify a suspicious internship offer before submitting your CV or paying any fees." />
            <UseCaseCard icon={Shield} title="University Career Offices" tag="Institutional" desc="Screen job postings shared on notice boards and portals before recommending them to students." />
            <UseCaseCard icon={Brain} title="Researchers & ML Students" tag="Academic" desc="Study the EMSCAD pipeline, SHAP explanations, and model comparison methodology for research." />
            <UseCaseCard icon={TrendingUp} title="HR & Recruitment Teams" tag="Professional" desc="Audit incoming job ad templates and detect fraudulent impersonation of your company brand." />
            <UseCaseCard icon={Lock} title="Cybersecurity Analysts" tag="Security" desc="Integrate the API into phishing detection workflows to flag employment-based social engineering." />
            <UseCaseCard icon={BarChart3} title="Data Science Projects" tag="Portfolio" desc="Fork the open pipeline to benchmark custom models on the EMSCAD classification task." />
          </div>
        </div>
      </section>

      {/* MODEL TRANSPARENCY */}
      <section className="py-24 sm:py-32 border-t border-[#2C313C]/40">
        <div className={SECTION}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <Eyebrow>Model Transparency</Eyebrow>
              <h2 className="mt-5 text-3xl sm:text-4xl font-bold tracking-tight text-[#F2F4F6]">No black boxes.<br /><span className="text-[#D9B100]">Every decision explained.</span></h2>
              <p className="mt-5 text-base text-[#949BA6] leading-relaxed">JobShield AI shows you exactly which features contributed to each prediction using industry-standard SHAP values.</p>
              <div className="mt-8 space-y-4">
                {[
                  "SHAP LinearExplainer for Logistic Regression & SVM",
                  "SHAP TreeExplainer for Random Forest & XGBoost",
                  "Per-token positive and negative contribution scores",
                  "Calibrated probability outputs — not raw logit scores",
                  "PR-AUC as the primary metric for imbalanced data",
                ].map((item) => (
                  <div key={item} className="flex items-center gap-3 text-sm text-[#949BA6]">
                    <CheckCircle2 className="w-4 h-4 text-[#D9B100] flex-shrink-0" />{item}
                  </div>
                ))}
              </div>
              <div className="mt-8">
                <Link to="/performance" className="inline-flex items-center gap-2 text-sm font-medium text-[#D9B100] hover:text-[#F3DA87] transition-colors">
                  View model benchmarks<ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {[
                { name: "Logistic Regression", type: "Linear", desc: "Calibrated baseline", dot: "bg-[#D9B100]" },
                { name: "Linear SVM", type: "Max-Margin", desc: "Sparse text spaces", dot: "bg-sky-400" },
                { name: "Random Forest", type: "Ensemble", desc: "Non-linear patterns", dot: "bg-emerald-400" },
                { name: "XGBoost", type: "Boosting", desc: "State-of-the-art", dot: "bg-amber-400" },
              ].map(({ name, type, desc, dot }) => (
                <div key={name} className="p-4 rounded-xl bg-[#191C22] border border-[#2C313C]">
                  <div className={`w-2 h-2 rounded-full ${dot} mb-3`} />
                  <div className="text-sm font-semibold text-[#F2F4F6] mb-1">{name}</div>
                  <div className="text-[11px] font-mono text-[#D9B100]/70 mb-2 uppercase">{type}</div>
                  <div className="text-xs text-[#626A77]">{desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-24 sm:py-32 border-t border-[#2C313C]/40 bg-[#14161A]/50">
        <div className="relative z-10 max-w-3xl mx-auto px-6 sm:px-8">
          <div className="text-center mb-12">
            <Eyebrow>FAQ</Eyebrow>
            <h2 className="mt-5 text-3xl sm:text-4xl font-bold tracking-tight text-[#F2F4F6]">Common questions</h2>
          </div>
          <FAQItem q="What is the EMSCAD dataset?" a="EMSCAD (Employment Scam Aegean Dataset) is a real-world dataset published by the University of the Aegean containing 17,880 job postings — 866 of which are verified fraudulent. It is the gold standard for employment fraud ML research." />
          <FAQItem q="How accurate is the fraud detection?" a="Accuracy alone is misleading for imbalanced datasets. We evaluate using PR-AUC and F1-Score on the minority fraud class. The winning model from our 4-candidate comparison is reported on the Model Performance page." />
          <FAQItem q="Can I trust a low risk result?" a="No ML model is perfect. A low-risk score means the posting text does not match patterns seen in EMSCAD fraud cases. Always cross-reference with independent company research before applying." />
          <FAQItem q="Does JobShield AI store my submitted postings?" a="No. Submitted text is processed in memory by the FastAPI backend and discarded after inference. No posting text is stored persistently." />
          <FAQItem q="What does the SHAP waterfall chart show?" a="SHAP values measure each word's contribution to the fraud score. Positive values push the score toward fraud; negative values push it toward legitimate. This shows exactly why the model made its decision." />
          <FAQItem q="Is this project open source?" a="Yes. The full ML pipeline — data preparation, training, evaluation, and FastAPI backend — is openly structured and documented in this project repository." />
        </div>
      </section>

      {/* CTA BANNER */}
      <section className="py-24 sm:py-32 border-t border-[#2C313C]/40">
        <div className="relative max-w-4xl mx-auto px-6 sm:px-8 text-center">
          <AmbientGlow className="top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] opacity-20" style={{ background: "radial-gradient(ellipse, rgba(217,177,0,0.35) 0%, transparent 70%)" }} />
          <div className="relative z-10">
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-[#F2F4F6] mb-5">Protect your next opportunity.</h2>
            <p className="text-base text-[#949BA6] max-w-xl mx-auto mb-10 leading-relaxed">Paste any suspicious job posting and get a full fraud risk analysis — with explainable AI — in seconds.</p>
            <Link to="/analyze" className="inline-flex items-center justify-center gap-2.5 px-10 py-4 rounded-full bg-[#D9B100] hover:bg-[#e5bc05] text-[#101114] font-bold text-base transition-all duration-200 shadow-xl shadow-[#D9B100]/20 hover:shadow-[#D9B100]/35 hover:scale-[1.03]">
              <Search className="w-4 h-4 stroke-[2.5]" />Start Free Analysis
            </Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-[#2C313C]/40 py-10">
        <div className={SECTION}>
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-md bg-[#D9B100]/10 border border-[#D9B100]/30 flex items-center justify-center text-[#D9B100]"><Shield className="w-3.5 h-3.5" /></div>
              <span className="font-semibold text-sm text-[#F2F4F6]">JobShield <span className="text-[#D9B100] font-mono">AI</span></span>
            </div>
            <nav className="flex items-center gap-6 text-xs text-[#626A77] font-mono">
              <Link to="/analyze" className="hover:text-[#949BA6] transition-colors">Analyze</Link>
              <Link to="/results" className="hover:text-[#949BA6] transition-colors">Results</Link>
              <Link to="/performance" className="hover:text-[#949BA6] transition-colors">Performance</Link>
              <a href="http://127.0.0.1:8001/docs" target="_blank" rel="noreferrer" className="hover:text-[#949BA6] transition-colors">API Docs</a>
            </nav>
            <div className="text-xs text-[#3B3F46] font-mono">© 2026 JobShield AI</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
