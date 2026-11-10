# JobShield AI: Explainable AI-Based Fraud Detection for Job & Internship Opportunities

JobShield AI is a specialized cybersecurity and machine learning platform engineered to detect, classify, and explain fraudulent job postings and predatory internship opportunities. Using statistical Natural Language Processing (TF-IDF), high-dimensional classifiers, heuristic threat policies, grounded Large Language Model (LLM) reasoning, and transparent feature attributions, JobShield AI provides job-seekers, career advisors, and university students with evidence-grounded scam risk assessments.

---

## 1. Project Purpose & Problem Statement

Employment fraud has escalated rapidly with the rise of remote hiring, generative scam syndicates, and online recruitment platforms. Victims often face:
- **Upfront Fee Schemes**: Demands for software license purchases, equipment setup fees, or visa processing funds.
- **Credential & Identity Harvesting**: Phishing for Social Security Numbers, banking details, or identity documents before genuine interviews.
- **Fake Check & Money Mule Traps**: Overpayment scams requiring cryptocurrency transfers or wire disbursements.
- **Spoofed Recruiter Identities**: Impersonating established companies using throwaway email domains or untraceable messaging apps (Telegram, WhatsApp).

JobShield AI tackles this challenge through **Explainable AI (XAI)**—delivering not merely a black-box probability, but an actionable, evidence-grounded risk breakdown explaining *why* a posting was flagged.

---

## 2. System Architecture & Features

### Part 1: Core ML Detection Engine
- **EMSCAD Data Preparation**: Leakage removal (`in_balanced_dataset`), deduplication (248 duplicates removed), and stratified 80/10/10 partitioning across 17,632 retained postings.
- **Candidate Classifiers**: Evaluated 4 candidate models (Logistic Regression, Linear SVM, Random Forest, XGBoost) across 10,031 features.
- **Champion Classifier**: **Linear Support Vector Machine** (Calibrated) achieving **0.9046 Val PR-AUC** and **0.8608 Val F1-score**.
- **Held-Out Test Benchmark**: 1,764 untouched samples: **0.8899 PR-AUC**, **0.8344 F1**, **0.8831 Precision**, **0.7907 Recall**, **0.9847 Accuracy**.
- **Model Serialization**: Persisted complete pipeline to `models/model.joblib` and benchmark telemetry to `models/metrics.json`.

### Part 2: Advanced AI Integration & Grounded Explainability
1. **Smart Job Posting Extraction**:
   - **SSRF-Protected URL Fetcher**: Blocks private subnets (RFC 1918), loopback, link-local, cloud metadata IPs (`169.254.169.254`), and validates redirects.
   - **HTML Content Parser**: Strips scripts/styles and isolates job containers using BeautifulSoup.
   - **Adversarial Defang & Cleaner**: Normalizes Unicode, whitespace, and neutralizes prompt injection patterns.
   - **20-Field Extractor**: Extracts structured fields via Groq LLM with deterministic regex/heuristic fallback.
   - **Normalizer**: Produces completeness scores and missing attribute audit.
2. **Grounded AI Explanation Generator**:
   - **Model Authority**: The Linear SVM champion model remains the sole classification authority; LLMs never alter the ML score or verdict.
   - **Groq Cloud LLM Provider**: High-speed Llama 3.3 inference producing grounded structured JSON explanations.
   - **Deterministic Fallback**: Guaranteed offline execution when an API key is absent.
   - **Evidence Grounding**: Verifiable textual excerpts for financial solicitations, untraceable payments, encrypted chat redirects, and unverified credentials.
3. **Advanced Risk Analysis**:
   - Four-tier composite risk categorization: `CRITICAL`, `HIGH`, `MODERATE`, `LOW`.
4. **External Dataset Validation Pipeline**:
   - Automated ingestion and schema adapter for external benchmarks (e.g. Internship Job Scam Dataset).
   - Domain shift telemetry computing accuracy, precision delta, recall delta, F1 retention rate, PR-AUC, and ROC-AUC.
   - CLI script (`scripts/validate_external_dataset.py`) for automated evaluation.
5. **Modern Frontend Experience**:
   - React + Vite + Tailwind CSS with dark cybersecurity aesthetic (`#101114`, `#191C22`, `#2C313C`, `#D9B100`).
   - Tabbed input (Smart URL Extraction, Paste Description, Direct Entry).
   - Extracted attribute preview with completeness progress bar.
   - Rich results cards with grounded explanations, warning indicators, positive signals, and applicant safety checklist.
   - Out-of-domain generalization telemetry table on the model performance page.

---

## 3. Real EMSCAD Dataset Accounting & Split Ratios

The raw dataset (`data/raw/DataSet.csv`) contains **17,880 records** (17,014 legitimate, 866 fraudulent).

### Resolution of the Fraudulent Count Discrepancy (866 -> 856)
1. **Raw Duplicates**: Across all 18 raw columns, 235 exact duplicate rows exist (227 legitimate, 8 fraudulent).
2. **Leakage-Column Impact**: Excluding the leakage sampling column `in_balanced_dataset` exposes **13 additional duplicate records** (11 legitimate, 2 fraudulent) where all real job posting attributes are identical.
3. **Total Deduplication**: Exactly **248 duplicate records** were removed (238 legitimate, 10 fraudulent).
4. **Retained Distribution**: Exactly **17,632 unique postings** (16,776 legitimate [95.15%], 856 fraudulent [4.85%]).

### Stratified Partitions (80 / 10 / 10)
Partitioning was performed with fixed seed `42` preserving the 4.85% fraud ratio across all mutually disjoint splits:

| Partition | Total Records | Fraudulent (Class 1) | Legitimate (Class 0) | Fraud Prevalence |
|---|---|---|---|---|
| **Training (80%)** | 14,105 | 685 | 13,420 | 4.86% |
| **Validation (10%)** | 1,763 | 85 | 1,678 | 4.82% |
| **Test (10%)** | 1,764 | 86 | 1,678 | 4.88% |
| **Total Retained** | **17,632** | **856** | **16,776** | **4.85%** |

---

## 4. Machine Learning Benchmark & Model Selection

### Feature Representation
- **Text Features**: `title`, `company_profile`, `description`, `requirements`, `benefits` combined and transformed via `TfidfVectorizer(max_features=10000, ngram_range=(1, 2), sublinear_tf=True, min_df=2)`.
- **Structured Features**: `telecommuting`, `has_company_logo`, `has_questions` (binary encoded) and `employment_type`, `required_experience`, `required_education` (One-Hot Encoded).
- **Total Feature Dimensions**: 10,031 features. Fitted strictly on training data.

### Candidate Model Comparison (Validation Set)

| Candidate Model | Val PR-AUC | Val F1 (Minority) | Precision | Recall | Tuned Threshold | Status |
|---|---|---|---|---|---|---|
| **Linear Support Vector Machine** | **0.9046** | **0.8608** | **0.9315** | **0.8000** | **0.480** | **Selected Champion** |
| **Logistic Regression** | 0.8748 | 0.8182 | 0.7912 | 0.8471 | 0.610 | Baseline |
| **XGBoost Classifier** | 0.8721 | 0.7898 | 0.8611 | 0.7294 | 0.740 | Boosted |
| **Random Forest Classifier** | 0.7977 | 0.7425 | 0.7561 | 0.7294 | 0.600 | Bagging Ensemble |

---

## 5. Quickstart & Local Execution

### 1. Environment Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Optional: Set your Groq API key in `.env` for LLM explanation generation (deterministic grounded fallback is used automatically if omitted):
```env
LLM_API_KEY=your_groq_api_key_here
```

### 2. Run Automated Test Suite
```bash
python -m pytest backend/tests
```
*Runs all 45 automated unit and integration tests across data prep, ML inference, extraction, explainability, and validation.*

### 3. Run External Dataset Validation CLI
```bash
python scripts/validate_external_dataset.py
```

### 4. Start Backend Service
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8008 --reload
```
API Documentation available at: **`http://127.0.0.1:8008/docs`**

### 5. Start React Frontend
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173/`** in your browser.

---

## 6. Complete API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | `GET` | Service status, model artifact presence, pipeline health. |
| `/api/metrics` | `GET` | Benchmark comparison metrics across 4 candidate models. |
| `/api/analyze` | `POST` | Live ML inference on job postings (probability, verdict, risk signals, SHAP attributions, grounded explanation). |
| `/api/extract/url` | `POST` | SSRF-safe URL crawling and structured 20-field job extraction. |
| `/api/extract/text` | `POST` | NLP parsing and structured 20-field extraction from unstructured text. |
| `/api/explain` | `POST` | Evidence-grounded AI explanation report with verified citations and safety checklist. |
| `/api/validation/external` | `GET` | Out-of-domain evaluation and generalization shift telemetry. |
