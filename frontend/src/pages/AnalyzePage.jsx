import React, { useState, useMemo } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  SearchCheck, RotateCcw, ShieldAlert, AlertCircle, Info, ArrowRight, FileText,
} from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import { analyzeJob, getActiveApiUrl } from "../services/api";

const SUSPICIOUS_SAMPLE = `URGENT HIRING: Work From Home Data Entry Agent — Earn $800/Week Guaranteed

We are urgently hiring remote data entry agents to work from home. No experience necessary. You will be paid $800 per week guaranteed.

To get started, you must send a $150 registration fee to cover training materials and software setup. This is fully refundable after your first paycheck.

Apply directly via WhatsApp: +1-555-0198 (DO NOT email, WhatsApp only for fast response)
Telegram: @earnbigfromhome

Positions are filling up FAST. Only 10 spots left. Apply in the next 24 hours or lose your spot forever.

No interview required. No experience needed. Students and unemployed individuals encouraged to apply. Guaranteed approval for all applicants.`;

const LEGITIMATE_SAMPLE = `Software Engineering Intern — Summer 2025
Acme Technology Solutions | San Francisco, CA (Hybrid)

About Acme Technology Solutions:
We are a Series B SaaS company building developer productivity tools used by over 50,000 engineers worldwide. Our engineering team of 120 is distributed across San Francisco, London, and Singapore.

Role Overview:
We are looking for a motivated Software Engineering Intern to join our Platform team for a 12-week summer internship. You will work on real production systems, contribute to code that serves thousands of users, and be paired with a senior engineer mentor throughout the internship.

Responsibilities:
- Implement features in our core Python/TypeScript codebase under mentor guidance
- Participate in design reviews, sprint planning, and retrospectives
- Write unit and integration tests for your contributions
- Present your project deliverables at our end-of-summer demo day

Requirements:
- Currently enrolled in a Computer Science or related degree program
- Familiarity with Python or TypeScript (either is fine)
- Strong problem-solving skills and eagerness to learn

Compensation:
$42/hour. No fees. Housing stipend available for relocating interns.

To Apply:
Submit your application at careers.acmehq.com/intern-2025. We do not request payment at any stage of the hiring process.`;

export default function AnalyzePage({ backendHealth, backendError, onNavigateToResults }) {
  const navigate = useNavigate();
  const [jobTitle, setJobTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState("");
  const [submitError, setSubmitError] = useState("");

  const minChars = 50;
  const charCount = description.length;
  const wordCount = useMemo(
    () => description.trim().split(/\s+/).filter(Boolean).length,
    [description]
  );

  const modelStatusNotice = useMemo(() => {
    if (backendError) {
      return {
        type: "error",
        title: "Backend Offline",
        message: backendError,
      };
    }
    if (backendHealth && !backendHealth.model_loaded) {
      return {
        type: "info",
        title: "ML Model Not Yet Loaded",
        message:
          "The inference pipeline is available but the trained model artifact has not been loaded. Run the training script to generate the model file, then restart the backend service.",
      };
    }
    return null;
  }, [backendHealth, backendError]);

  const handleLoadSample = (type) => {
    setValidationError("");
    setSubmitError("");
    if (type === "suspicious") {
      setJobTitle("Work From Home Data Entry Agent");
      setCompanyName("(unknown)");
      setDescription(SUSPICIOUS_SAMPLE);
    } else {
      setJobTitle("Software Engineering Intern");
      setCompanyName("Acme Technology Solutions");
      setDescription(LEGITIMATE_SAMPLE);
    }
  };

  const handleClear = () => {
    setJobTitle("");
    setCompanyName("");
    setDescription("");
    setValidationError("");
    setSubmitError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidationError("");
    setSubmitError("");

    if (charCount < minChars) {
      setValidationError(`Please provide at least ${minChars} characters of job posting text.`);
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await analyzeJob({
        title: jobTitle.trim() || "Job Posting Under Analysis",
        company_name: companyName.trim() || "",
        description: description.trim(),
      });

      if (!res.ok) {
        setSubmitError(res.error || "Analysis request failed.");
      } else {
        if (onNavigateToResults) {
          onNavigateToResults(res.data);
        }
        navigate("/results");
      }
    } catch (err) {
      setSubmitError(err.message || "An unexpected error occurred during submission.");
    } finally {
      setIsSubmitting(false);
    }
  };
  return (
    <div className="min-h-[calc(100vh-5rem)] bg-[#101114]">
      {/* Page header */}
      <div className="border-b border-[#2C313C]/50 bg-[#14161A]/60">
        <div className="max-w-4xl mx-auto px-6 sm:px-8 py-8">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#D9B100] font-semibold">
              Live Inference Engine
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#F2F4F6] tracking-tight">
            Analyze a Job Posting
          </h1>
          <p className="mt-2 text-sm text-[#949BA6] max-w-xl leading-relaxed">
            Paste the full job or internship text below. The ML pipeline will extract TF-IDF features, classify fraud risk, and generate SHAP explanations.
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 sm:px-8 py-8 sm:py-12 space-y-6">

        {/* Template loader + clear */}
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs text-[#626A77] font-mono uppercase tracking-wider">Load Template:</span>
          <button
            type="button"
            onClick={() => handleLoadSample("suspicious")}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-950/30 text-red-300 border border-red-900/60 hover:bg-red-950/50 transition-colors"
          >
            Suspicious Sample
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample("legitimate")}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-950/30 text-emerald-300 border border-emerald-900/60 hover:bg-emerald-950/50 transition-colors"
          >
            Legitimate Sample
          </button>
          <button
            type="button"
            onClick={handleClear}
            title="Clear all fields"
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-[#626A77] border border-[#2C313C] hover:text-[#F2F4F6] hover:bg-[#191C22] transition-colors flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />Clear
          </button>
        </div>

        {/* Model/Backend status notice */}
        {modelStatusNotice && (
          <div className={`p-4 rounded-xl border ${modelStatusNotice.type === "error" ? "bg-red-950/20 border-red-800/60 text-red-200" : "bg-amber-950/20 border-amber-800/60 text-amber-200"}`}>
            <div className="flex items-start gap-3">
              {modelStatusNotice.type === "error"
                ? <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                : <Info className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />}
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-[#F2F4F6]">{modelStatusNotice.title}</h4>
                <p className="text-xs text-[#949BA6] leading-relaxed">{modelStatusNotice.message}</p>
                <div className="pt-2 flex flex-wrap items-center gap-3 font-mono text-[11px] text-[#626A77]">
                  <span>Dataset: EMSCAD (17,880 rows)</span>
                  <span>·</span>
                  <span>Engine: <StatusBadge status="pending" label="Training Pending" size="xs" /></span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Analysis form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Metadata row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-mono uppercase tracking-wider text-[#626A77]">
                Job Title <span className="text-[#3B3F46]">(Optional)</span>
              </label>
              <input
                type="text"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="e.g. Remote Data Entry Assistant"
                className="w-full px-4 py-2.5 rounded-xl bg-[#191C22] border border-[#2C313C] text-sm text-[#F2F4F6] placeholder-[#3B3F46] focus:outline-none focus:border-[#D9B100] transition-colors"
              />
            </div>
            <div className="space-y-1.5">
              <label className="block text-xs font-mono uppercase tracking-wider text-[#626A77]">
                Company / Recruiter <span className="text-[#3B3F46]">(Optional)</span>
              </label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g. Acme Global Inc."
                className="w-full px-4 py-2.5 rounded-xl bg-[#191C22] border border-[#2C313C] text-sm text-[#F2F4F6] placeholder-[#3B3F46] focus:outline-none focus:border-[#D9B100] transition-colors"
              />
            </div>
          </div>

          {/* Posting textarea */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-mono uppercase tracking-wider text-[#F2F4F6] font-semibold">
                Job / Internship Posting Text <span className="text-[#D9B100]">*</span>
              </label>
              <div className="text-[11px] font-mono text-[#626A77] flex items-center gap-2">
                <span>{wordCount} words</span>
                <span>·</span>
                <span className={charCount < minChars && charCount > 0 ? "text-amber-400" : ""}>
                  {charCount} chars (min {minChars})
                </span>
              </div>
            </div>
            <textarea
              rows={14}
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                if (validationError && e.target.value.length >= minChars) setValidationError("");
              }}
              placeholder="Paste the full job posting, internship offer, recruiter email, or messaging transcript here..."
              className={`w-full p-4 rounded-xl bg-[#191C22] border text-sm text-[#F2F4F6] placeholder-[#3B3F46] font-mono text-xs leading-relaxed focus:outline-none focus:border-[#D9B100] transition-colors resize-y ${
                validationError ? "border-red-500/80" : "border-[#2C313C]"
              }`}
            />
            {validationError && (
              <p className="text-xs text-red-400 flex items-center gap-1.5 font-mono pt-1">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                {validationError}
              </p>
            )}
          </div>

          {/* Submit error */}
          {submitError && (
            <div className="p-4 rounded-xl bg-red-950/20 border border-red-800/60">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-red-300 leading-relaxed">{submitError}</p>
              </div>
            </div>
          )}

          {/* Action bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
            <p className="text-xs text-[#626A77] flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-[#D9B100]" />
              TF-IDF extraction · SHAP token attribution · Calibrated probability
            </p>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-[#D9B100] hover:bg-[#e5bc05] text-[#101114] font-bold text-sm transition-all duration-150 shadow-lg shadow-[#D9B100]/20 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-[#101114] border-t-transparent rounded-full animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <SearchCheck className="w-4 h-4 stroke-[2.5]" />
                  Analyze Job Opportunity
                </>
              )}
            </button>
          </div>
        </form>

        {/* Bottom info card */}
        <div className="mt-8 p-5 rounded-2xl bg-[#191C22] border border-[#2C313C]">
          <div className="flex items-start gap-3">
            <FileText className="w-5 h-5 text-[#D9B100] flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-[#F2F4F6] mb-1.5">What happens after you submit?</h3>
              <ul className="space-y-1 text-xs text-[#949BA6] leading-relaxed">
                <li>1. Your text is vectorized using the TF-IDF pipeline trained on 17,880 EMSCAD postings.</li>
                <li>2. The ML classifier outputs a calibrated fraud probability score.</li>
                <li>3. Heuristic rules detect explicit red flags (payment requests, off-platform contact, etc.).</li>
                <li>4. SHAP values identify the exact tokens that most influenced the classification.</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
