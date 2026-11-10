import React, { useState, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  SearchCheck, RotateCcw, ShieldAlert, AlertCircle, AlertTriangle, Info, ArrowRight,
  Globe, FileText, Edit3, Sparkles, CheckCircle2, Check, ExternalLink,
  Loader2, Building2, Briefcase, DollarSign, Award, Layers
} from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import { analyzeJob, extractFromUrl, extractFromText } from "../services/api";

const PRESET_SAMPLES = {
  telegram_scam: {
    title: "Virtual Remote Assistant & Data Entry",
    company_name: "Apex Global Solutions LLC",
    description: "Urgent recruitment! Earn $45/hour guaranteed with flexible hours from home. We are hiring 10 candidates immediately. No interview required! Candidates must connect directly with our hiring lead on Telegram @fast_recruit_team or WhatsApp +1-555-0199. A refundable registration fee of $120 is required for your onboarding kit. Send payment via wire transfer or Cash App. Apply within 24 hours, limited spots left!",
    requirements: "No experience needed. Basic typing skills and smartphone.",
    benefits: "$45/hr guaranteed, instant daily payouts.",
    telecommuting: true,
    has_company_logo: false,
    has_questions: false,
    employment_type: "Part-time",
    required_experience: "Entry level",
    required_education: "High School or equivalent",
  },
  upfront_fee_scam: {
    title: "Executive Administrative Assistant",
    company_name: "TransNational Consulting",
    description: "Immediate hire guaranteed! We are looking for an executive assistant to handle scheduling, data logging, and customer outreach. Candidates must send a $150 deposit for certified software licenses and secure background checks. Fee is fully refunded upon completion of first assignment. Contact careers@gmail.com.",
    requirements: "Attention to detail, Microsoft Office knowledge.",
    benefits: "Guaranteed $900 weekly income.",
    telecommuting: true,
    has_company_logo: false,
    has_questions: false,
    employment_type: "Contract",
    required_experience: "Not Applicable",
    required_education: "Unspecified",
  },
  legitimate_intern: {
    title: "Software Engineering Intern — Summer 2027",
    company_name: "Stripe",
    description: "Join Stripe's Infrastructure Engineering team for a 12-week intensive summer internship in San Francisco. You will design, build, and deploy high-availability distributed systems handling millions of payment transactions daily. Paired with a senior staff engineer mentor, you will participate in architectural reviews, agile sprint cycles, and write automated tests.",
    requirements: "Currently pursuing a BS/MS in Computer Science or related STEM field. Proficiency in Python, Go, or Java. Solid foundation in data structures, algorithms, and system design.",
    benefits: "$55/hour, comprehensive health insurance, corporate housing stipend, 401(k) eligibility, roundtrip travel reimbursement.",
    telecommuting: false,
    has_company_logo: true,
    has_questions: true,
    employment_type: "Full-time",
    required_experience: "Internship",
    required_education: "Bachelor's Degree",
  },
  legitimate_analyst: {
    title: "Junior Data Analyst",
    company_name: "Datadog",
    description: "Datadog is looking for a Junior Data Analyst to join our Product Analytics organization. You will collaborate with product managers and engineers to build automated telemetry dashboards, query multi-terabyte data warehouses using SQL and dbt, and deliver statistical insights that drive user growth.",
    requirements: "Bachelor's degree in Statistics, Mathematics, Economics, or Computer Science. Strong SQL and Python skills (pandas, numpy). Experience with Looker or Tableau.",
    benefits: "Competitive base salary, equity stock options (RSUs), 100% employer-paid health, dental, vision, flexible PTO.",
    telecommuting: true,
    has_company_logo: true,
    has_questions: true,
    employment_type: "Full-time",
    required_experience: "Entry level",
    required_education: "Bachelor's Degree",
  },
};

export default function AnalyzePage({ backendHealth, backendError, onNavigateToResults }) {
  const navigate = useNavigate();

  // Mode selection: 'url', 'paste', 'manual'
  const [activeTab, setActiveTab] = useState("url");

  // URL extraction state
  const [inputUrl, setInputUrl] = useState("");
  const [isExtractingUrl, setIsExtractingUrl] = useState(false);
  const [urlExtractError, setUrlExtractError] = useState("");
  const [urlValidationNotice, setUrlValidationNotice] = useState(null);
  const urlInputRef = useRef(null);

  // Paste extraction state
  const [rawPastedText, setRawPastedText] = useState("");
  const [isExtractingText, setIsExtractingText] = useState(false);
  const [textExtractError, setTextExtractError] = useState("");
  const [textValidationNotice, setTextValidationNotice] = useState(null);
  const pasteTextareaRef = useRef(null);

  // Structured Job Form State (20-field aligned)
  const [jobTitle, setJobTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [location, setLocation] = useState("");
  const [workArrangement, setWorkArrangement] = useState("Not specified");
  const [duration, setDuration] = useState("");
  const [companyProfile, setCompanyProfile] = useState("");
  const [description, setDescription] = useState("");
  const [responsibilities, setResponsibilities] = useState("");
  const [requirements, setRequirements] = useState("");
  const [benefits, setBenefits] = useState("");
  const [compensation, setCompensation] = useState("");
  const [skillsList, setSkillsList] = useState([]);
  const [employmentType, setEmploymentType] = useState("Not specified");
  const [requiredExperience, setRequiredExperience] = useState("Internship");
  const [requiredEducation, setRequiredEducation] = useState("Bachelor's Degree");
  const [telecommuting, setTelecommuting] = useState(false);
  const [hasCompanyLogo, setHasCompanyLogo] = useState(false);
  const [hasQuestions, setHasQuestions] = useState(false);

  // Extraction metadata & completeness tracking
  const [extractionMeta, setExtractionMeta] = useState(null);

  // Track extraction request sequence to avoid stale responses
  const extractionRequestRef = useRef(0);

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState("");
  const [submitError, setSubmitError] = useState("");

  const minChars = 40;
  const charCount = description.length;
  const wordCount = useMemo(
    () => description.trim().split(/\s+/).filter(Boolean).length,
    [description]
  );

  // Calculate completeness score
  const completeness = useMemo(() => {
    let score = 0;
    if (jobTitle.trim().length > 2) score += 20;
    if (companyName.trim().length > 1) score += 15;
    if (description.trim().length > 50) score += 25;
    if (requirements.trim().length > 10) score += 15;
    if (responsibilities.trim().length > 10) score += 10;
    if (benefits.trim().length > 2 || compensation.trim().length > 2) score += 15;
    return Math.min(100, score);
  }, [jobTitle, companyName, description, requirements, responsibilities, benefits, compensation]);

  // Load sample preset
  const handleLoadPreset = (key) => {
    const sample = PRESET_SAMPLES[key];
    if (!sample) return;
    setJobTitle(sample.title);
    setCompanyName(sample.company_name);
    setLocation(sample.location || "Remote");
    setWorkArrangement(sample.telecommuting ? "Remote" : "On-site");
    setDuration("");
    setCompanyProfile(sample.company_profile || "");
    setDescription(sample.description);
    setResponsibilities(sample.responsibilities || "");
    setRequirements(sample.requirements || "");
    setBenefits(sample.benefits || "");
    setCompensation(sample.benefits || "");
    setSkillsList([]);
    setEmploymentType(sample.employment_type || "Full-time");
    setRequiredExperience(sample.required_experience || "Entry level");
    setRequiredEducation(sample.required_education || "Bachelor's Degree");
    setTelecommuting(Boolean(sample.telecommuting));
    setHasCompanyLogo(Boolean(sample.has_company_logo));
    setHasQuestions(Boolean(sample.has_questions));
    setExtractionMeta({
      method: "preset_sample",
      confidence: 1.0,
      completeness_score: 95,
      missing_fields: [],
    });
    setValidationError("");
    setSubmitError("");
    setActiveTab("manual");
  };

  const handleClear = () => {
    setJobTitle("");
    setCompanyName("");
    setLocation("");
    setWorkArrangement("Not specified");
    setDuration("");
    setCompanyProfile("");
    setDescription("");
    setResponsibilities("");
    setRequirements("");
    setBenefits("");
    setCompensation("");
    setSkillsList([]);
    setEmploymentType("Not specified");
    setRequiredExperience("Internship");
    setRequiredEducation("Bachelor's Degree");
    setTelecommuting(false);
    setHasCompanyLogo(false);
    setHasQuestions(false);
    setExtractionMeta(null);
    setInputUrl("");
    setRawPastedText("");
    setValidationError("");
    setSubmitError("");
    setUrlExtractError("");
    setTextExtractError("");
    setUrlValidationNotice(null);
    setTextValidationNotice(null);
  };

  // URL extraction handler
  const handleExtractFromUrl = async (e) => {
    e.preventDefault();
    setUrlExtractError("");
    setUrlValidationNotice(null);

    // --- Issue D fix: use WHATWG URL parser for robust validation ---
    const trimmedUrl = inputUrl.trim();
    let isValidUrl = false;
    try {
      const parsed = new URL(trimmedUrl);
      isValidUrl = parsed.protocol === "http:" || parsed.protocol === "https:";
    } catch {
      isValidUrl = false;
    }
    if (!trimmedUrl || !isValidUrl) {
      setUrlExtractError("Please enter a valid public HTTP or HTTPS URL (e.g. https://careers.example.com/job/12345).");
      return;
    }

    // --- Issue A fix: clear all previously extracted fields before every new attempt ---
    setJobTitle("");
    setCompanyName("");
    setLocation("");
    setWorkArrangement("Not specified");
    setDuration("");
    setCompanyProfile("");
    setDescription("");
    setResponsibilities("");
    setRequirements("");
    setBenefits("");
    setCompensation("");
    setSkillsList([]);
    setEmploymentType("Not specified");
    setRequiredExperience("Entry level");
    setRequiredEducation("Unspecified");
    setTelecommuting(false);
    setHasCompanyLogo(false);
    setHasQuestions(false);
    setExtractionMeta(null);
    setUrlValidationNotice(null);

    // Bump request counter to detect stale responses from previous in-flight requests
    const currentRequestId = ++extractionRequestRef.current;

    setIsExtractingUrl(true);
    try {
      const res = await extractFromUrl(trimmedUrl);

      // Discard stale response if a newer request was started
      if (currentRequestId !== extractionRequestRef.current) return;

      if (!res.ok) {
        // Map extraction_status to a user-friendly message
        const exStatus = res.data?.extraction_status;
        let errorMsg = res.error || "Failed to extract job posting from URL.";
        if (exStatus === "ACCESS_RESTRICTED") {
          errorMsg = "Website access was restricted. This website does not allow automated extraction. Please copy and paste the job description text using the 'Paste Job Description' tab.";
        } else if (exStatus === "JAVASCRIPT_REQUIRED") {
          errorMsg = "This webpage requires JavaScript to display its content. Please open the URL in your browser, copy the job description text, and use the 'Paste Job Description' tab instead.";
        } else if (exStatus === "LISTING_PAGE") {
          errorMsg = "This URL contains multiple job listings, not an individual posting. Please open the listing, click on a specific job, and provide its direct URL.";
        } else if (exStatus === "NOT_A_JOB_POSTING") {
          errorMsg = "The retrieved page does not appear to be an individual job advertisement. Please provide a direct link to a specific job posting.";
        } else if (exStatus === "RETRIEVAL_FAILED") {
          errorMsg = res.data?.validation_message || "Could not retrieve the webpage. Please verify the URL is correct and the site is accessible.";
        } else if (exStatus === "URL_INVALID") {
          errorMsg = "The URL was rejected for security reasons. Only publicly accessible HTTP/HTTPS URLs are supported.";
        }
        setUrlExtractError(errorMsg);
        return;
      }

      // Check if server classified page as non-job content (HTTP 200, success=false)
      if (res.data?.is_valid_job === false || (!res.data?.success && res.data?.validation_message)) {
        const exStatus = res.data?.extraction_status;
        let noticeTitle = "Job Description Not Detected";
        let noticeMsg = res.data.validation_message || "The target URL does not contain an identifiable job description. Please verify the link or paste the job posting text directly.";
        if (exStatus === "ACCESS_RESTRICTED") {
          noticeTitle = "Website Access Restricted";
        } else if (exStatus === "JAVASCRIPT_REQUIRED") {
          noticeTitle = "JavaScript-Rendered Page";
        } else if (exStatus === "LISTING_PAGE") {
          noticeTitle = "Multiple Job Listings Detected";
        } else if (exStatus === "NOT_A_JOB_POSTING") {
          noticeTitle = "Not a Job Posting";
        }
        setUrlValidationNotice({
          title: noticeTitle,
          message: noticeMsg,
          issues: res.data.invalid_signals || res.data.warnings || [],
        });
        return;
      }

      const ext = res.data?.extracted_job || res.data?.extracted_data;
      if (!ext) {
        setUrlExtractError("Extraction response was empty or malformed. Please verify the URL or paste the job description text directly.");
        return;
      }

      setJobTitle(ext.title || "");
      setCompanyName(ext.company_name || "");
      setLocation(ext.location || "");
      setWorkArrangement(ext.work_arrangement || (ext.is_remote ? "Remote" : "Not specified"));
      setDuration(ext.duration || "");
      setCompanyProfile(ext.company_profile || ext.company_description || "");
      setDescription(ext.description || ext.responsibilities || "");
      setRequirements(ext.requirements || "");
      setResponsibilities(ext.responsibilities || "");

      const compVal = ext.compensation || ext.salary_range || "";
      const benVal = ext.benefits || "";
      const combinedBen = benVal && compVal && !benVal.includes(compVal) ? `${compVal} · ${benVal}` : (compVal || benVal);
      setCompensation(compVal);
      setBenefits(combinedBen);
      setSkillsList(ext.required_skills || []);

      setEmploymentType(ext.employment_type || "Not specified");
      setRequiredExperience(ext.required_experience || "Entry level");

      const eduStr = ext.required_education || "";
      if (eduStr.toLowerCase().includes("master")) {
        setRequiredEducation("Master's Degree");
      } else if (eduStr.toLowerCase().includes("bachelor")) {
        setRequiredEducation("Bachelor's Degree");
      } else if (eduStr.toLowerCase().includes("high school")) {
        setRequiredEducation("High School or equivalent");
      } else {
        setRequiredEducation("Unspecified");
      }

      setTelecommuting(Boolean(ext.is_remote ?? ext.telecommuting));
      setHasCompanyLogo(Boolean(ext.has_company_logo));
      setHasQuestions(Boolean(ext.has_questions));

      const compScore = typeof res.data.completeness?.score === "number"
        ? res.data.completeness.score
        : Math.round((ext.completeness_score || 0) * 100);
      const missingList = res.data.completeness?.missing_fields || ext.missing_fields || [];
      const methodLabel = res.data.extraction_method || res.data.source_type || "URL Extractor";
      const confidenceVal = typeof res.data.extraction_confidence === "number"
        ? res.data.extraction_confidence
        : (compScore > 0 ? Number((compScore / 100).toFixed(2)) : 0.0);

      setExtractionMeta({
        method: methodLabel,
        confidence: confidenceVal,
        completeness_score: compScore,
        missing_fields: missingList,
        page_title: res.data.source_identifier || "",
      });
      setActiveTab("manual"); // Switch to editor to review extracted data
    } catch (err) {
      if (currentRequestId !== extractionRequestRef.current) return;
      setUrlExtractError(err.message || "Network error during URL extraction.");
    } finally {
      setIsExtractingUrl(false);
    }
  };

  // Text extraction handler
  const handleExtractFromText = async (e) => {
    e.preventDefault();
    setTextExtractError("");
    setTextValidationNotice(null);
    if (!rawPastedText.trim() || rawPastedText.trim().length < 20) {
      setTextExtractError("Please paste at least 20 characters of job description text.");
      return;
    }

    setIsExtractingText(true);
    try {
      const res = await extractFromText(rawPastedText.trim());
      if (!res.ok) {
        setTextExtractError(res.error || "Failed to parse job description.");
        return;
      }

      // Check if server rejected content as non-job technical data (e.g. portal config JSON)
      if (res.data?.is_valid_job === false || (!res.data?.success && res.data?.validation_message)) {
        setTextValidationNotice({
          title: "Job Description Not Detected",
          message: res.data.validation_message || "The submitted content appears to contain website configuration, metadata, or technical code rather than an actual job posting. Please paste the visible job description, including responsibilities and qualifications.",
          issues: res.data.invalid_signals || res.data.warnings || [],
        });
        return;
      }

      const ext = res.data?.extracted_job || res.data?.extracted_data;
      if (!ext) {
        setTextExtractError("Extraction response was empty or malformed. Please check the text format.");
        return;
      }

      setJobTitle(ext.title || "");
      setCompanyName(ext.company_name || "");
      setLocation(ext.location || "");
      setWorkArrangement(ext.work_arrangement || (ext.is_remote ? "Remote" : "Not specified"));
      setDuration(ext.duration || "");
      setCompanyProfile(ext.company_profile || ext.company_description || "");
      setDescription(ext.description || rawPastedText);
      setRequirements(ext.requirements || "");
      setResponsibilities(ext.responsibilities || "");

      const compVal = ext.compensation || ext.salary_range || "";
      const benVal = ext.benefits || "";
      const combinedBen = benVal && compVal && !benVal.includes(compVal) ? `${compVal} · ${benVal}` : (compVal || benVal);
      setCompensation(compVal);
      setBenefits(combinedBen);
      setSkillsList(ext.required_skills || []);

      setEmploymentType(ext.employment_type || "Not specified");
      setRequiredExperience(ext.required_experience || "Entry level");

      const eduStr = ext.required_education || "";
      if (eduStr.toLowerCase().includes("master")) {
        setRequiredEducation("Master's Degree");
      } else if (eduStr.toLowerCase().includes("bachelor")) {
        setRequiredEducation("Bachelor's Degree");
      } else if (eduStr.toLowerCase().includes("high school")) {
        setRequiredEducation("High School or equivalent");
      } else {
        setRequiredEducation("Unspecified");
      }

      setTelecommuting(Boolean(ext.is_remote ?? ext.telecommuting));
      setHasCompanyLogo(Boolean(ext.has_company_logo));
      setHasQuestions(Boolean(ext.has_questions));

      const compScore = typeof res.data.completeness?.score === "number"
        ? res.data.completeness.score
        : Math.round((ext.completeness_score || 0) * 100);
      const missingList = res.data.completeness?.missing_fields || ext.missing_fields || [];
      const methodLabel = res.data.extraction_method || res.data.source_type || "Text Parser";
      const confidenceVal = typeof res.data.extraction_confidence === "number"
        ? res.data.extraction_confidence
        : (compScore > 0 ? Number((compScore / 100).toFixed(2)) : 0.0);

      setExtractionMeta({
        method: methodLabel,
        confidence: confidenceVal,
        completeness_score: compScore,
        missing_fields: missingList,
      });
      setActiveTab("manual"); // Switch to editor to review
    } catch (err) {
      setTextExtractError(err.message || "Network error during text extraction.");
    } finally {
      setIsExtractingText(false);
    }
  };

  // Final ML Analysis Submission
  const handleSubmitAnalysis = async (e) => {
    e.preventDefault();
    setValidationError("");
    setSubmitError("");

    if (!jobTitle.trim()) {
      setValidationError("Job title is required for accurate classification.");
      return;
    }
    if (charCount < minChars) {
      setValidationError(`Job description requires at least ${minChars} characters of content.`);
      return;
    }

    setIsSubmitting(true);
    try {
      let finalDescription = description.trim();
      if (responsibilities.trim() && !finalDescription.includes(responsibilities.trim())) {
        finalDescription += "\n\nResponsibilities:\n" + responsibilities.trim();
      }

      const payload = {
        title: jobTitle.trim(),
        company_name: companyName.trim(),
        company_profile: companyProfile.trim(),
        description: finalDescription,
        requirements: requirements.trim(),
        benefits: (benefits.trim() || compensation.trim()),
        telecommuting: telecommuting ? 1 : 0,
        has_company_logo: hasCompanyLogo ? 1 : 0,
        has_questions: hasQuestions ? 1 : 0,
        employment_type: employmentType,
        required_experience: requiredExperience,
        required_education: requiredEducation,
      };

      const res = await analyzeJob(payload);
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
      {/* Page Header */}
      <div className="border-b border-[#2C313C]/50 bg-[#14161A]/60">
        <div className="max-w-5xl mx-auto px-6 sm:px-8 py-8">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#D9B100] font-semibold">
              Part 2 · Advanced AI & Inference Engine
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#F2F4F6] tracking-tight">
            Analyze Job & Internship Opportunity
          </h1>
          <p className="mt-2 text-sm text-[#949BA6] max-w-2xl leading-relaxed">
            Extract attributes from live URLs, parse unstructured job postings, or enter details directly.
            Evaluated against our champion Linear SVM model with grounded explainability and deterministic threat detection.
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 sm:px-8 py-8 space-y-6">
        {/* Preset Sample Selector */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-[#191C22]/80 border border-[#2C313C]">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-[#626A77] font-mono uppercase tracking-wider mr-1">Load Preset:</span>
            <button
              type="button"
              onClick={() => handleLoadPreset("telegram_scam")}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-950/40 text-red-300 border border-red-900/60 hover:bg-red-950/60 transition-colors"
            >
              Telegram Scam
            </button>
            <button
              type="button"
              onClick={() => handleLoadPreset("upfront_fee_scam")}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-950/40 text-amber-300 border border-amber-900/60 hover:bg-amber-950/60 transition-colors"
            >
              Upfront Fee Phishing
            </button>
            <button
              type="button"
              onClick={() => handleLoadPreset("legitimate_intern")}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-950/40 text-emerald-300 border border-emerald-900/60 hover:bg-emerald-950/60 transition-colors"
            >
              Stripe Intern
            </button>
            <button
              type="button"
              onClick={() => handleLoadPreset("legitimate_analyst")}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-950/40 text-blue-300 border border-blue-900/60 hover:bg-blue-950/60 transition-colors"
            >
              Datadog Analyst
            </button>
          </div>
          <button
            type="button"
            onClick={handleClear}
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-[#626A77] border border-[#2C313C] hover:text-[#F2F4F6] hover:bg-[#191C22] transition-colors flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Clear All
          </button>
        </div>

        {/* Input Method Navigation Tabs */}
        <div className="flex border-b border-[#2C313C] gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("url")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "url"
                ? "border-[#D9B100] text-[#D9B100]"
                : "border-transparent text-[#949BA6] hover:text-[#F2F4F6]"
            }`}
          >
            <Globe className="w-4 h-4" />
            Smart URL Extraction
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("paste")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "paste"
                ? "border-[#D9B100] text-[#D9B100]"
                : "border-transparent text-[#949BA6] hover:text-[#F2F4F6]"
            }`}
          >
            <FileText className="w-4 h-4" />
            Paste Job Description
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("manual")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "manual"
                ? "border-[#D9B100] text-[#D9B100]"
                : "border-transparent text-[#949BA6] hover:text-[#F2F4F6]"
            }`}
          >
            <Edit3 className="w-4 h-4" />
            Field Editor & Verification
            {charCount > 0 && (
              <span className="ml-1.5 px-2 py-0.5 rounded-full text-[10px] bg-[#D9B100]/20 text-[#D9B100]">
                {completeness}%
              </span>
            )}
          </button>
        </div>

        {/* TAB 1: Smart URL Extraction */}
        {activeTab === "url" && (
          <div className="p-6 rounded-2xl bg-[#14161A] border border-[#2C313C] space-y-4">
            <div>
              <h3 className="text-base font-semibold text-[#F2F4F6] flex items-center gap-2">
                <Globe className="w-4 h-4 text-[#D9B100]" /> Extract From Live Career URL
              </h3>
              <p className="text-xs text-[#949BA6] mt-1">
                Enter any public job posting URL. Our SSRF-protected crawler parses the HTML and extracts 20 structured fields.
              </p>
            </div>

            <form onSubmit={handleExtractFromUrl} className="space-y-4">
              <div className="flex gap-2">
                <input
                  ref={urlInputRef}
                  type="url"
                  value={inputUrl}
                  onChange={(e) => {
                    setInputUrl(e.target.value);
                    if (urlValidationNotice) setUrlValidationNotice(null);
                  }}
                  placeholder="https://example.com/careers/software-engineer"
                  className="flex-1 px-4 py-3 rounded-xl bg-[#191C22] border border-[#2C313C] text-sm text-[#F2F4F6] placeholder-[#626A77] focus:outline-none focus:border-[#D9B100]"
                />
                <button
                  type="submit"
                  disabled={isExtractingUrl}
                  className="px-6 py-3 rounded-xl bg-[#D9B100] text-[#101114] font-semibold text-sm hover:bg-[#F3DA87] transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  {isExtractingUrl ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Extracting...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" /> Extract Fields
                    </>
                  )}
                </button>
              </div>

              {urlValidationNotice && (
                <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-600/50 space-y-3 animate-fadeIn">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <h4 className="text-sm font-semibold text-amber-200">
                        {urlValidationNotice.title}
                      </h4>
                      <p className="text-xs text-amber-300/90 leading-relaxed">
                        {urlValidationNotice.message}
                      </p>
                    </div>
                  </div>
                  {urlValidationNotice.issues && urlValidationNotice.issues.length > 0 && (
                    <div className="pl-8 space-y-1">
                      <p className="text-[11px] font-medium text-amber-400 uppercase tracking-wider">Detected Issues:</p>
                      <ul className="list-disc list-inside text-xs text-amber-300/80 space-y-0.5">
                        {urlValidationNotice.issues.map((issue, idx) => (
                          <li key={idx}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="pl-8 pt-1 flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        setUrlValidationNotice(null);
                        urlInputRef.current?.focus();
                      }}
                      className="px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-medium hover:bg-amber-500/30 transition-colors"
                    >
                      Edit URL & Try Again
                    </button>
                  </div>
                </div>
              )}

              {urlExtractError && (
                <div className="p-3 rounded-xl bg-red-950/30 border border-red-900/60 text-xs text-red-300 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <span>{urlExtractError}</span>
                </div>
              )}
            </form>
          </div>
        )}

        {/* TAB 2: Paste Raw Text */}
        {activeTab === "paste" && (
          <div className="p-6 rounded-2xl bg-[#14161A] border border-[#2C313C] space-y-4">
            <div>
              <h3 className="text-base font-semibold text-[#F2F4F6] flex items-center gap-2">
                <FileText className="w-4 h-4 text-[#D9B100]" /> Parse Unstructured Job Text
              </h3>
              <p className="text-xs text-[#949BA6] mt-1">
                Paste the raw text from LinkedIn, Indeed, email, or messaging apps. Our NLP extraction engine parses company name, requirements, and compensation automatically.
              </p>
            </div>

            <form onSubmit={handleExtractFromText} className="space-y-4">
              <textarea
                ref={pasteTextareaRef}
                rows={8}
                value={rawPastedText}
                onChange={(e) => {
                  setRawPastedText(e.target.value);
                  if (textValidationNotice) setTextValidationNotice(null);
                }}
                placeholder="Paste the entire job posting or message content here..."
                className="w-full px-4 py-3 rounded-xl bg-[#191C22] border border-[#2C313C] text-sm text-[#F2F4F6] placeholder-[#626A77] focus:outline-none focus:border-[#D9B100] font-mono text-xs leading-relaxed"
              />

              {textValidationNotice && (
                <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-600/50 space-y-3 animate-fadeIn">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <h4 className="text-sm font-semibold text-amber-200">
                        {textValidationNotice.title}
                      </h4>
                      <p className="text-xs text-amber-300/90 leading-relaxed">
                        {textValidationNotice.message}
                      </p>
                    </div>
                  </div>
                  {textValidationNotice.issues && textValidationNotice.issues.length > 0 && (
                    <div className="pl-8 space-y-1">
                      <p className="text-[11px] font-medium text-amber-400 uppercase tracking-wider">Detected Issues:</p>
                      <ul className="list-disc list-inside text-xs text-amber-300/80 space-y-0.5">
                        {textValidationNotice.issues.map((issue, idx) => (
                          <li key={idx}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="pl-8 pt-1 flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        setTextValidationNotice(null);
                        pasteTextareaRef.current?.focus();
                      }}
                      className="px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-medium hover:bg-amber-500/30 transition-colors"
                    >
                      Edit Input & Try Again
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setRawPastedText("");
                        setTextValidationNotice(null);
                        pasteTextareaRef.current?.focus();
                      }}
                      className="px-3 py-1.5 rounded-lg bg-[#191C22] text-[#949BA6] border border-[#2C313C] text-xs font-medium hover:text-[#F2F4F6] transition-colors"
                    >
                      Clear Text
                    </button>
                  </div>
                </div>
              )}

              {textExtractError && (
                <div className="p-3 rounded-xl bg-red-950/30 border border-red-900/60 text-xs text-red-300 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <span>{textExtractError}</span>
                </div>
              )}

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isExtractingText}
                  className="px-6 py-3 rounded-xl bg-[#D9B100] text-[#101114] font-semibold text-sm hover:bg-[#F3DA87] transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  {isExtractingText ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Parsing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" /> Parse & Extract Fields
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Extraction Preview Banner (when extracted) */}
        {extractionMeta && (
          <div className="p-4 rounded-xl bg-[#191C22] border border-[#D9B100]/40 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#D9B100]/10 border border-[#D9B100]/30 flex items-center justify-center text-[#D9B100]">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[#F2F4F6] flex items-center gap-2">
                  <span>Extracted via {extractionMeta.method || "Smart Extractor"}</span>
                  <span className="text-[11px] font-mono text-[#D9B100]">
                    ({Math.round((extractionMeta.confidence ?? 0.9) * 100)}% Confidence)
                  </span>
                </div>
                <div className="text-[11px] text-[#949BA6] mt-0.5">
                  Completeness score: {extractionMeta.completeness_score ?? 0}% · {extractionMeta.missing_fields?.length || 0} missing fields
                </div>
              </div>
            </div>
            <div className="w-36 h-2 bg-[#2C313C] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#D9B100] rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(0, extractionMeta.completeness_score ?? 0))}%` }}
              />
            </div>
          </div>
        )}

        {/* Structured Field Editor & Verification */}
        <form onSubmit={handleSubmitAnalysis} className="space-y-6">
          <div className="p-6 rounded-2xl bg-[#14161A] border border-[#2C313C] space-y-5">
            <div className="flex items-center justify-between border-b border-[#2C313C]/60 pb-3">
              <h3 className="text-sm font-semibold text-[#F2F4F6] uppercase tracking-wider font-mono">
                Posting Attributes (Verified for Inference)
              </h3>
              <div className="text-xs text-[#949BA6] font-mono">
                Word Count: <span className="text-[#F2F4F6]">{wordCount}</span>
              </div>
            </div>

            {/* Core Header Details */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Job Title <span className="text-[#D9B100]">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  placeholder="e.g. Senior Software Engineer / Data Intern"
                  className="w-full px-4 py-2.5 rounded-xl bg-[#191C22] border border-[#2C313C] text-sm text-[#F2F4F6] placeholder-[#626A77] focus:outline-none focus:border-[#D9B100]"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Company / Organization
                </label>
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g. Datadog / Stripe / Apex Capital"
                  className="w-full px-4 py-2.5 rounded-xl bg-[#191C22] border border-[#2C313C] text-sm text-[#F2F4F6] placeholder-[#626A77] focus:outline-none focus:border-[#D9B100]"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Location
                </label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Bengaluru / San Francisco / Remote"
                  className="w-full px-4 py-2.5 rounded-xl bg-[#191C22] border border-[#2C313C] text-sm text-[#F2F4F6] placeholder-[#626A77] focus:outline-none focus:border-[#D9B100]"
                />
              </div>
            </div>

            {/* Arrangement, Duration & Compensation */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Work Arrangement
                </label>
                <select
                  value={workArrangement}
                  onChange={(e) => {
                    setWorkArrangement(e.target.value);
                    if (e.target.value === "Remote") setTelecommuting(true);
                    else if (e.target.value === "Hybrid" || e.target.value === "On-site") setTelecommuting(false);
                  }}
                  className="w-full px-3 py-2 rounded-xl bg-[#191C22] border border-[#2C313C] text-xs text-[#F2F4F6] focus:outline-none focus:border-[#D9B100]"
                >
                  <option value="Hybrid">Hybrid</option>
                  <option value="Remote">Remote</option>
                  <option value="On-site">On-site</option>
                  <option value="Not specified">Not specified</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Duration
                </label>
                <input
                  type="text"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  placeholder="e.g. 6 months"
                  className="w-full px-4 py-2 rounded-xl bg-[#191C22] border border-[#2C313C] text-xs text-[#F2F4F6] placeholder-[#626A77] focus:outline-none focus:border-[#D9B100]"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Compensation / Stipend
                </label>
                <input
                  type="text"
                  value={compensation}
                  onChange={(e) => {
                    setCompensation(e.target.value);
                    if (!benefits) setBenefits(e.target.value);
                  }}
                  placeholder="e.g. INR 20,000 per month"
                  className="w-full px-4 py-2 rounded-xl bg-[#191C22] border border-[#2C313C] text-xs text-[#F2F4F6] placeholder-[#626A77] focus:outline-none focus:border-[#D9B100]"
                />
              </div>
            </div>

            {/* Main Description */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#F2F4F6]">
                  Full Job Description <span className="text-[#D9B100]">*</span>
                </label>
                <span className={`text-[11px] font-mono ${charCount < minChars ? "text-amber-400" : "text-[#626A77]"}`}>
                  {charCount} chars (min {minChars})
                </span>
              </div>
              <textarea
                rows={6}
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Paste the primary job description and core responsibilities here..."
                className="w-full px-4 py-3 rounded-xl bg-[#191C22] border border-[#2C313C] text-sm text-[#F2F4F6] placeholder-[#626A77] focus:outline-none focus:border-[#D9B100] leading-relaxed"
              />
            </div>

            {/* Requirements & Responsibilities */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Candidate Requirements & Qualifications
                </label>
                <textarea
                  rows={4}
                  value={requirements}
                  onChange={(e) => setRequirements(e.target.value)}
                  placeholder="e.g. BS in CS, Python, SQL, 2+ years experience..."
                  className="w-full px-4 py-2.5 rounded-xl bg-[#191C22] border border-[#2C313C] text-sm text-[#F2F4F6] placeholder-[#626A77] focus:outline-none focus:border-[#D9B100]"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Core Responsibilities & Duties
                </label>
                <textarea
                  rows={4}
                  value={responsibilities}
                  onChange={(e) => setResponsibilities(e.target.value)}
                  placeholder="e.g. Software development, debugging, testing, code reviews..."
                  className="w-full px-4 py-2.5 rounded-xl bg-[#191C22] border border-[#2C313C] text-sm text-[#F2F4F6] placeholder-[#626A77] focus:outline-none focus:border-[#D9B100]"
                />
              </div>
            </div>

            {/* Compensation & Benefits */}
            <div className="space-y-1.5">
              <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                Compensation & Offered Benefits
              </label>
              <textarea
                rows={2}
                value={benefits}
                onChange={(e) => setBenefits(e.target.value)}
                placeholder="e.g. $45/hr, health insurance, 401(k), paid stipend..."
                className="w-full px-4 py-2.5 rounded-xl bg-[#191C22] border border-[#2C313C] text-sm text-[#F2F4F6] placeholder-[#626A77] focus:outline-none focus:border-[#D9B100]"
              />
            </div>

            {/* Categorical Selectors */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="space-y-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Employment Type
                </label>
                <select
                  value={employmentType}
                  onChange={(e) => setEmploymentType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-[#191C22] border border-[#2C313C] text-xs text-[#F2F4F6] focus:outline-none focus:border-[#D9B100]"
                >
                  <option value="Internship">Internship</option>
                  <option value="Full-time">Full-time</option>
                  <option value="Part-time">Part-time</option>
                  <option value="Contract">Contract</option>
                  <option value="Temporary">Temporary</option>
                  <option value="Not specified">Not specified</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Experience Level
                </label>
                <select
                  value={requiredExperience}
                  onChange={(e) => setRequiredExperience(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-[#191C22] border border-[#2C313C] text-xs text-[#F2F4F6] focus:outline-none focus:border-[#D9B100]"
                >
                  <option value="Internship">Internship</option>
                  <option value="Entry level">Entry level</option>
                  <option value="Mid-Senior level">Mid-Senior level</option>
                  <option value="Director">Director</option>
                  <option value="Not Applicable">Not Applicable</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Required Education
                </label>
                <select
                  value={requiredEducation}
                  onChange={(e) => setRequiredEducation(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-[#191C22] border border-[#2C313C] text-xs text-[#F2F4F6] focus:outline-none focus:border-[#D9B100]"
                >
                  <option value="Bachelor's Degree">Bachelor's Degree</option>
                  <option value="Master's Degree">Master's Degree</option>
                  <option value="High School or equivalent">High School or equivalent</option>
                  <option value="Unspecified">Unspecified</option>
                </select>
              </div>
            </div>

            {/* Extracted Skills List */}
            {skillsList && skillsList.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-[#2C313C]/60">
                <label className="block text-xs font-mono uppercase tracking-wider text-[#949BA6]">
                  Extracted Candidate Skills ({skillsList.length})
                </label>
                <div className="flex flex-wrap gap-2">
                  {skillsList.map((skill, idx) => (
                    <span key={idx} className="px-2.5 py-1 rounded-lg text-xs bg-[#191C22] text-[#D9B100] border border-[#D9B100]/30 font-medium">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Binary Characteristic Flags */}
            <div className="flex flex-wrap items-center gap-6 pt-3 border-t border-[#2C313C]/60 text-xs">
              <label className="flex items-center gap-2 cursor-pointer text-[#F2F4F6]">
                <input
                  type="checkbox"
                  checked={telecommuting}
                  onChange={(e) => setTelecommuting(e.target.checked)}
                  className="rounded border-[#2C313C] text-[#D9B100] focus:ring-0 bg-[#191C22]"
                />
                <span>Remote / Telecommuting Role</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-[#F2F4F6]">
                <input
                  type="checkbox"
                  checked={hasCompanyLogo}
                  onChange={(e) => setHasCompanyLogo(e.target.checked)}
                  className="rounded border-[#2C313C] text-[#D9B100] focus:ring-0 bg-[#191C22]"
                />
                <span>Verified Employer Logo Attached</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-[#F2F4F6]">
                <input
                  type="checkbox"
                  checked={hasQuestions}
                  onChange={(e) => setHasQuestions(e.target.checked)}
                  className="rounded border-[#2C313C] text-[#D9B100] focus:ring-0 bg-[#191C22]"
                />
                <span>Application Screening Questions Present</span>
              </label>
            </div>
          </div>

          {/* Validation & Submit Errors */}
          {validationError && (
            <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-900/60 text-xs text-amber-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span>{validationError}</span>
            </div>
          )}

          {submitError && (
            <div className="p-4 rounded-xl bg-red-950/30 border border-red-900/60 text-xs text-red-300 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-400 flex-shrink-0" />
              <span>{submitError}</span>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-8 py-3.5 rounded-xl bg-[#D9B100] text-[#101114] font-bold text-sm hover:bg-[#F3DA87] transition-all disabled:opacity-50 flex items-center gap-2.5 shadow-lg shadow-[#D9B100]/10"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Evaluating ML Pipeline...
                </>
              ) : (
                <>
                  <SearchCheck className="w-4 h-4" /> Run ML Fraud Detection <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
