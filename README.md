# JobShield AI: Explainable AI-Based Fraud Detection for Job & Internship Opportunities

JobShield AI is a specialized cybersecurity and machine learning platform engineered to detect, classify, and explain fraudulent job postings and predatory internship opportunities. Using statistical Natural Language Processing (TF-IDF), high-dimensional classifiers, heuristic threat policies, and SHAP-aligned feature attributions, JobShield AI provides job-seekers, career advisors, and university students with transparent, verifiable scam risk assessments.

---

## 1. Project Purpose & Problem Statement

Employment fraud has escalated rapidly with the rise of remote hiring, generative scam syndicates, and online recruitment platforms. Victims often face:
- **Upfront Fee Schemes**: Demands for software license purchases, equipment setup fees, or visa processing funds.
- **Credential & Identity Harvesting**: Phishing for Social Security Numbers, banking details, or identity documents before genuine interviews.
- **Fake Check & Money Mule Traps**: Overpayment scams requiring cryptocurrency transfers or wire disbursements.
- **Spoofed Recruiter Identities**: Impersonating established companies using throwaway email domains or untraceable messaging apps (Telegram, WhatsApp).

JobShield AI tackles this challenge through **Explainable AI (XAI)**?delivering not merely a black-box probability, but an actionable, evidence-grounded risk breakdown explaining *why* a posting was flagged.

---

## 2. Part 1 Implementation Summary

Part 1 represents the complete, fully functional core detection engine, trained benchmark models, inference API, explainability, frontend integration, and test suite.

| Component | Status | Implementation Details |
|---|---|---|
| **EMSCAD Data Preparation** | Completed | `scripts/prepare_dataset.py` with leakage removal (`in_balanced_dataset`), deduplication (248 duplicates removed), and stratified 80/10/10 partitioning. |
| **Data Accounting & Transparency** | Completed | Fully accounted for raw 17,880 -> 17,632 retained postings (accounting for 866 -> 856 fraudulent count). |
| **Model Training & Comparison** | Completed | `scripts/train_models.py` training 4 candidates (Logistic Regression, Linear SVM, Random Forest, XGBoost) on 10,031 features. |
| **Model Selection & Tuning** | Completed | Evaluated candidates on validation split using PR-AUC and minority F1-score; tuned optimal decision threshold (0.48). |
| **Champion Model** | Completed | **Linear Support Vector Machine** (Calibrated) achieving **0.9046 Val PR-AUC** and **0.8608 Val F1-score**. |
| **Held-Out Test Benchmark** | Completed | Evaluated on untouched test split (1,764 samples): **0.8899 PR-AUC**, **0.8344 F1**, **0.8831 Precision**, **0.7907 Recall**, **0.9847 Accuracy**. |
| **Model Serialization** | Completed | Persisted complete pipeline to `models/model.joblib` (7.5 MB) and benchmark telemetry to `models/metrics.json`. |
| **Inference Service** | Completed | `backend/app/services/prediction_service.py` with calibrated scoring, risk categorization, and threat heuristics. |
| **Explainable AI (XAI)** | Completed | Linear feature attribution and SHAP-aligned token contributions for transparent reasoning. |
| **FastAPI Backend Endpoints** | Completed | `GET /api/health`, `GET /api/metrics`, `POST /api/analyze` running on port 8008. |
| **React + Vite Frontend** | Completed | Unified dark aesthetic (`LandingPage`, `AnalyzePage`, `ResultsPage`, `PerformancePage`). |
| **Automated Test Suite** | Completed | 28 automated tests covering dataset preparation, pipeline feature extraction, API routes, and inference (100% passing). |

---

## 3. Real EMSCAD Dataset Accounting & Split Ratios

The raw dataset (`data/raw/DataSet.csv`) contains **17,880 records** (17,014 legitimate, 866 fraudulent).

### Resolution of the Fraudulent Count Discrepancy (866 -> 856)
1. **Raw Duplicates**: Across all 18 raw columns, 235 exact duplicate rows exist (227 legitimate, 8 fraudulent).
2. **Leakage-Column Impact**: The metadata column `in_balanced_dataset` indicates whether Aegean researchers sampled the row for their 50/50 balanced sub-corpus. Excluding `in_balanced_dataset` exposes **13 additional duplicate records** (11 legitimate, 2 fraudulent) where all real job posting attributes are identical but differed only by that sampling flag.
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

### Champion Model Selection Rationale
Linear Support Vector Machine (with Sigmoid calibration) achieved the highest Precision-Recall AUC (0.9046) and highest F1-score (0.8608) on the minority fraud class. Margin maximization in sparse TF-IDF text spaces proves exceptionally effective at isolating rare employment fraud phrase patterns while maintaining low false-positive rates (0.5% on test data).

### Final Unbiased Evaluation on Held-Out Test Split (1,764 samples)
- **PR-AUC**: `0.8899`
- **ROC-AUC**: `0.9877`
- **F1-Score (Minority)**: `0.8344`
- **Precision (Minority)**: `0.8831`
- **Recall (Minority)**: `0.7907`
- **Overall Accuracy**: `0.9847`
- **Test Confusion Matrix**:
  - True Negatives (Legitimate verified): **1,669** (99.5%)
  - False Positives (Legitimate flagged as scam): **9** (0.5%)
  - False Negatives (Scams missed): **18** (20.9%)
  - True Positives (Scams caught): **68** (79.1%)

---

## 5. Directory Structure

```
JobShield-AI/
??? backend/
?   ??? app/
?   ?   ??? main.py                  # FastAPI application entrypoint & middleware
?   ?   ??? api/
?   ?   ?   ??? __init__.py          # API router aggregator
?   ?   ?   ??? routes/
?   ?   ?       ??? health.py        # GET /api/health
?   ?   ?       ??? metrics.py       # GET /api/metrics
?   ?   ?       ??? analyze.py       # POST /api/analyze
?   ?   ??? core/
?   ?   ?   ??? config.py            # Pydantic Settings & CORS configuration
?   ?   ??? schemas/
?   ?   ?   ??? health.py            # Health schemas
?   ?   ?   ??? analysis.py          # Prediction & Explainability schemas
?   ?   ??? services/
?   ?       ??? health_service.py    # Subsystem telemetry
?   ?       ??? ml_pipeline.py       # Reusable EMSCADPreprocessor & feature extractor
?   ?       ??? prediction_service.py # Inference, heuristic signals & linear attributions
?   ??? tests/
?       ??? test_dataset_preparation.py # 13 dataset integrity tests
?       ??? test_health.py              # 4 health endpoint tests
?       ??? test_ml_pipeline.py         # 3 preprocessor unit tests
?       ??? test_prediction_and_api.py  # 8 prediction and API integration tests
??? data/
?   ??? raw/
?   ?   ??? DataSet.csv              # Raw EMSCAD dataset (17,880 rows)
?   ??? processed/
?       ??? train.csv                # 14,105 training samples
?       ??? validation.csv           # 1,763 validation samples
?       ??? test.csv                 # 1,764 held-out test samples
?       ??? dataset_report.json      # Raw inspection telemetry
?       ??? split_summary.json       # Partition summary & accounting
??? frontend/
?   ??? src/
?   ?   ??? App.jsx                  # Unified application shell & routing
?   ?   ??? index.css                # Tailwind CSS styling & custom dark palette
?   ?   ??? components/
?   ?   ?   ??? LandingNavbar.jsx    # Unified top navbar with live backend status
?   ?   ?   ??? StatusBadge.jsx      # Reusable badge component
?   ?   ?   ??? ErrorBoundary.jsx    # Client error boundary
?   ?   ??? pages/
?   ?   ?   ??? LandingPage.jsx      # Product landing page
?   ?   ?   ??? AnalyzePage.jsx      # Submission form with sample pre-fill
?   ?   ?   ??? ResultsPage.jsx      # Live inference report & SHAP attributions
?   ?   ?   ??? PerformancePage.jsx  # Candidate benchmark table & confusion matrix
?   ?   ?   ??? NotFoundPage.jsx     # 404 handler
?   ?   ??? services/
?   ?       ??? api.js               # API client (health, analyze, metrics)
??? models/
?   ??? model.joblib                 # Persisted champion pipeline (7.5 MB)
?   ??? metrics.json                 # Genuine candidate comparison & test metrics
??? scripts/
    ??? inspect_dataset.py           # Dataset inspection CLI tool
    ??? prepare_dataset.py           # Dataset preparation and splitting CLI
    ??? train_models.py              # ML candidate training & evaluation pipeline
```

---

## 6. Setup and Reproduction Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+ and npm

### 1. Install Dependencies
```bash
# Backend dependencies
pip install -r backend/requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Dataset Preparation
To reproduce the clean, leakage-free 80/10/10 partitions:
```bash
python scripts/prepare_dataset.py --data-path data/raw/DataSet.csv
```

### 3. Model Training & Benchmark Evaluation
To reproduce candidate training, validation tuning, and test evaluation:
```bash
python scripts/train_models.py
```
This generates `models/model.joblib` and `models/metrics.json`.

### 4. Run Automated Tests
```bash
python -m pytest backend/tests
```
All 28 tests will execute and validate the pipeline end-to-end.

### 5. Start the Application
Start the FastAPI backend:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8008 --reload
```
Start the React frontend (in another terminal):
```bash
cd frontend
npm run dev
```
Open **`http://localhost:5173/`** in your browser.

---

## 7. API Reference

### `GET /api/health`
Returns system status and model readiness.
```json
{
  "status": "healthy",
  "service": "jobshield-ai-backend",
  "version": "0.1.0",
  "model_status": "trained",
  "details": {
    "api_prefix": "/api",
    "model_subsystem": { "artifacts_found": "model.joblib" }
  }
}
```

### `GET /api/metrics`
Returns candidate classifier comparison and test split confusion matrix.

### `POST /api/analyze`
Analyzes a submitted job posting.
**Request Body**:
```json
{
  "title": "URGENT Data Entry Agent",
  "company_name": "Fast Earn LLC",
  "description": "Urgent hiring. Earn $800 per week guaranteed. Send $150 training fee via wire transfer or telegram before starting.",
  "has_company_logo": false
}
```
**Response Body**:
```json
{
  "success": true,
  "model_status": "trained",
  "prediction": 1,
  "is_fraudulent": true,
  "fraud_probability": 0.9282,
  "score": 0.9282,
  "verdict": "Potentially Fraudulent Job Posting",
  "risk_level": "CRITICAL",
  "decision_threshold": 0.48,
  "model_name": "Linear Support Vector Machine",
  "heuristic_signals": [
    "Financial solicitation or upfront registration/training fee requested",
    "Recruitment redirected to encrypted/external chat platform (Telegram/WhatsApp)",
    "Unrealistic compensation guarantee or bypassed hiring/interview process",
    "No verified corporate employer logo present in posting"
  ],
  "shap_values": [
    { "token": "earn", "value": 0.3824 },
    { "token": "data entry", "value": 0.2317 },
    { "token": "work home", "value": 0.2232 },
    { "token": "guaranteed", "value": 0.1571 },
    { "token": "send", "value": 0.1250 }
  ]
}
```

---

## 8. Limitations & Future Scope (Part 2)

- **Text Length Dependency**: Predictions are most reliable when complete descriptions are supplied (minimum 50 words recommended).
- **Domain Adaptation**: The EMSCAD dataset reflects postings collected through 2014; emerging 2024-2026 scam vectors (such as fake AI trainer roles or remote crypto arbitrage tasks) are supplemented through heuristic keyword policies.
- **Part 2 Scope**: Integration of Large Language Model (GenAI) explanation summaries, recruiter email domain DNS verification, and SQLite persistent analysis history.
