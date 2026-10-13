import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  SearchCheck,
  AlertCircle,
  FileText,
  RotateCcw,
  Sparkles,
  Info,
  ExternalLink,
  ShieldAlert,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';

const SAMPLE_POSTINGS = {
  suspicious: `Position: Remote Entry-Level Data Entry Assistant & Operations
Company: Global Digital Dynamics Inc.
Location: Fully Remote (Anywhere in US/Canada)
Salary: $45.00 - $55.00 / hour (Immediate daily payout)

About the Opportunity:
We are seeking motivated individuals for our remote data team. No prior experience required. Flexible working hours (10-20 hrs/week). Immediate onboarding within 24 hours.

Key Responsibilities:
- Receive and compile customer records via encrypted channels.
- Coordinate fund transfers and purchasing of home office workstation materials.
- Verify payment receipts via wire transfer, Western Union, and cryptocurrency.

Requirements:
- Must have personal bank account or digital crypto wallet for equipment check disbursement.
- Candidates must purchase our pre-approved home office laptop bundle ($850) which will be fully reimbursed on your first paycheck.
- Fast-track interview conducted entirely via Telegram: @global_recruiter_hr. Contact immediately to secure your spot.`,

  legitimate: `Position: Junior Frontend Developer (React / JavaScript)
Company: DataCore Technologies Ltd.
Location: Austin, TX (Hybrid - 2 days in office)
Salary: $75,000 - $88,000 / year + Comprehensive Benefits

About DataCore Technologies:
DataCore provides enterprise analytics and data pipeline solutions to Fortune 500 organizations. We foster an inclusive, engineering-first culture.

Responsibilities:
- Collaborate with cross-functional teams to build and maintain responsive React web applications.
- Implement reusable UI components in accordance with our design system.
- Participate in code reviews, automated testing, and agile sprint planning.
- Diagnose and resolve frontend performance bottlenecks and browser compatibility issues.

Requirements:
- Bachelor's degree in Computer Science or equivalent practical experience.
- 1-2 years experience with modern JavaScript (ES6+), React, and CSS/Tailwind.
- Familiarity with RESTful APIs, Git version control, and CI/CD pipelines.
- Strong communication skills and collaborative problem-solving approach.
- Note: All interviews are conducted via our official Google Meet domain (@datacore.io). We never request equipment payments or personal banking info prior to formal HR onboarding.`,
};

export default function AnalyzePage({ backendHealth, backendError, onNavigateToResults }) {
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [modelStatusNotice, setModelStatusNotice] = useState(null);

  const charCount = description.length;
  const wordCount = description.trim() ? description.trim().split(/\s+/).length : 0;
  const minChars = 50;

  const handleLoadSample = (type) => {
    if (type === 'suspicious') {
      setJobTitle('Remote Entry-Level Data Entry Assistant & Operations');
      setCompanyName('Global Digital Dynamics Inc.');
      setDescription(SAMPLE_POSTINGS.suspicious);
    } else {
      setJobTitle('Junior Frontend Developer (React / JavaScript)');
      setCompanyName('DataCore Technologies Ltd.');
      setDescription(SAMPLE_POSTINGS.legitimate);
    }
    setValidationError('');
    setModelStatusNotice(null);
  };

  const handleClear = () => {
    setJobTitle('');
    setCompanyName('');
    setDescription('');
    setValidationError('');
    setModelStatusNotice(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setValidationError('');
    setModelStatusNotice(null);

    if (charCount < minChars) {
      setValidationError(
        `Job description must be at least ${minChars} characters to allow meaningful TF-IDF feature extraction (currently ${charCount} characters).`
      );
      return;
    }

    setIsSubmitting(true);

    // Foundation Phase check:
    // In this MVP phase, we verify backend model artifact status honestly.
    // If backend reports pending_training, we display the honest technical status
    // rather than faking an ML prediction.
    setTimeout(() => {
      setIsSubmitting(false);

      if (backendError) {
        setModelStatusNotice({
          type: 'error',
          title: 'Backend API Unreachable',
          message:
            'Unable to reach FastAPI at http://127.0.0.1:8000/api. Ensure the backend server is running in a separate terminal via "uvicorn backend.app.main:app --reload".',
        });
      } else if (backendHealth?.model_status !== 'trained') {
        setModelStatusNotice({
          type: 'pending',
          title: 'Foundation Phase: Model Training Pending',
          message:
            'The backend foundation is healthy, but machine learning models have not been trained yet. In accordance with the project guidelines, fake predictions are never generated. Once candidate models (Logistic Regression, Linear SVM, Random Forest, XGBoost) are trained on the EMSCAD dataset in the next phase, live inference will be active here.',
        });
      }
    }, 400);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-shield-border pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#D9B100] font-semibold">
              Live Inference & Verification
            </span>
          </div>
          <h2 className="text-xl font-bold text-shield-text">
            Analyze Job Opportunity
          </h2>
          <p className="text-xs text-shield-muted mt-0.5">
            Submit a job posting text to extract risk signals, evaluate ML scam probability, and inspect model explanations.
          </p>
        </div>

        {/* Load sample triggers */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-shield-subtle font-mono hidden md:inline">
            Load Template:
          </span>
          <button
            type="button"
            onClick={() => handleLoadSample('suspicious')}
            className="px-2.5 py-1.5 rounded text-xs font-medium bg-red-950/30 text-red-300 border border-red-900/60 hover:bg-red-950/50 transition-colors"
          >
            Suspicious Sample
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample('legitimate')}
            className="px-2.5 py-1.5 rounded text-xs font-medium bg-emerald-950/30 text-emerald-300 border border-emerald-900/60 hover:bg-emerald-950/50 transition-colors"
          >
            Legitimate Sample
          </button>
          <button
            type="button"
            onClick={handleClear}
            title="Clear fields"
            className="p-1.5 rounded text-shield-muted hover:text-shield-text border border-shield-border hover:bg-shield-surface/40 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Honest Model Status / Error Notice */}
      {modelStatusNotice && (
        <div
          className={`p-4 rounded-lg border ${
            modelStatusNotice.type === 'error'
              ? 'bg-red-950/20 border-red-800/60 text-red-200'
              : 'bg-amber-950/20 border-amber-800/60 text-amber-200'
          }`}
        >
          <div className="flex items-start gap-3">
            {modelStatusNotice.type === 'error' ? (
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            ) : (
              <Info className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            )}
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-shield-text">
                {modelStatusNotice.title}
              </h4>
              <p className="text-xs text-shield-muted leading-relaxed">
                {modelStatusNotice.message}
              </p>
              <div className="pt-2 flex items-center gap-3 font-mono text-[11px]">
                <span className="text-shield-subtle">Target Pipeline:</span>
                <span className="text-shield-text">EMSCAD (17,880 rows)</span>
                <span className="text-shield-subtle">•</span>
                <span className="text-shield-subtle">Engine Status:</span>
                <StatusBadge status="pending" label="Training Pending" size="xs" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Analysis Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Optional Metadata Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-shield-muted font-mono uppercase tracking-wider">
              Job Title <span className="text-shield-subtle">(Optional)</span>
            </label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g. Remote Data Entry Assistant"
              className="w-full px-3 py-2 rounded-md bg-shield-card border border-shield-border text-sm text-shield-text placeholder-shield-subtle focus:outline-none focus:border-[#D9B100] transition-colors"
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-shield-muted font-mono uppercase tracking-wider">
              Company / Recruiter Domain <span className="text-shield-subtle">(Optional)</span>
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g. Acme Global Inc. / @acmecareers.com"
              className="w-full px-3 py-2 rounded-md bg-shield-card border border-shield-border text-sm text-shield-text placeholder-shield-subtle focus:outline-none focus:border-[#D9B100] transition-colors"
            />
          </div>
        </div>

        {/* Text Area for Posting Description */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-medium text-shield-text font-mono uppercase tracking-wider">
              Job / Internship Posting Text <span className="text-[#D9B100]">*</span>
            </label>
            <div className="text-[11px] font-mono text-shield-subtle space-x-2">
              <span>{wordCount} words</span>
              <span>•</span>
              <span className={charCount < minChars ? 'text-amber-400' : 'text-shield-soft'}>
                {charCount} characters (min {minChars})
              </span>
            </div>
          </div>

          <textarea
            rows={12}
            value={description}
            onChange={(e) => {
              setDescription(e.target.value);
              if (validationError && e.target.value.length >= minChars) {
                setValidationError('');
              }
            }}
            placeholder="Paste the full job posting, internship offer, recruiter email, or messaging transcript here..."
            className={`w-full p-3.5 rounded-md bg-shield-card border text-sm text-shield-text placeholder-shield-subtle font-mono text-xs leading-relaxed focus:outline-none focus:border-[#D9B100] transition-colors resize-y ${
              validationError ? 'border-red-500/80' : 'border-shield-border'
            }`}
          />

          {validationError && (
            <p className="text-xs text-red-400 flex items-center gap-1.5 font-mono pt-1">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              {validationError}
            </p>
          )}
        </div>

        {/* Actions bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
          <div className="text-xs text-shield-subtle flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-[#D9B100]" />
            <span>
              TF-IDF text extraction analyzes vocabulary, suspicious phrases, and structural indicators.
            </span>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-md bg-[#D9B100] hover:bg-[#e5bc05] text-black font-semibold text-sm transition-colors disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                <span>Checking Inference Pipeline...</span>
              </>
            ) : (
              <>
                <SearchCheck className="w-4 h-4 stroke-[2.5]" />
                <span>Analyze Job Opportunity</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
