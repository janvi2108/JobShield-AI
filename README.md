# JobShield AI: Explainable AI-Based Fraud Detection for Job & Internship Opportunities

JobShield AI is a specialized cybersecurity and machine learning platform engineered to detect, classify, and explain fraudulent job postings and predatory internship opportunities. Using statistical Natural Language Processing (TF-IDF), high-dimensional classifiers, heuristic threat policies, and SHAP (SHapley Additive exPlanations), JobShield AI provides job-seekers and university graduates with transparent, verifiable scam risk assessments.

---

## 1. Project Purpose & Problem Statement

Employment fraud has escalated rapidly with the rise of remote hiring, generative scam syndicates, and online recruitment platforms. Victims often face:
- **Upfront Fee Schemes**: Demands for software license purchases, equipment setup fees, or visa processing funds.
- **Credential & Identity Harvesting**: Phishing for Social Security Numbers, banking details, or identity documents before genuine interviews.
- **Fake Check & Money Mule Traps**: Overpayment scams requiring cryptocurrency transfers or wire disbursements.
- **Spoofed Recruiter Identities**: Impersonating established companies using throwaway email domains or untraceable messaging apps (Telegram, WhatsApp).

JobShield AI tackles this challenge through **Explainable AI (XAI)**—delivering not merely a black-box probability, but an actionable, evidence-grounded risk breakdown explaining *why* a posting was flagged.

---

## 2. Current Implementation Status

This repository is currently at **Part 1, Phase 2: EMSCAD Dataset Preparation & Exploration**:

| Component | Status | Implementation Details |
|---|---|---|
| **Project Architecture** | ✅ Completed | Multi-tier repository structure (`backend/`, `frontend/`, `data/`, `models/`, `scripts/`, `notebooks/`, `docs/`). |
| **Backend API Core** | ✅ Completed | FastAPI service with CORS restriction, structured error handling, and `GET /api/health`. |
| **Backend & Pipeline Tests** | ✅ Completed | Automated `pytest` suite validating health schema, CORS headers, target mappers, leakage guards, and stratified splits (15/15 tests passing). |
| **Design System** | ✅ Completed | Cybersecurity SaaS dark theme with exact brand palette tokens (`#101114`, `#3B3F46`, `#D9B100`, `#F3DA87`, `#F2F4F6`). |
| **Frontend Dashboard** | ✅ Completed | 4-stage pipeline explanation, EMSCAD dataset characteristics, live API telemetry, and session overview. |
| **Analyze Job Page** | ✅ Completed | Input validation, word/char counters, sample templates (Suspicious vs. Legitimate), and honest training check. |
| **Analysis Results Page** | ✅ Completed | Meaningful empty state + complete specification schema blueprint ready for model inference output. |
| **Model Performance Page** | ✅ Completed | Comparison breakdown for Logistic Regression, Linear SVM, Random Forest, and XGBoost with PR-AUC evaluation policy. |
| **Dataset Inspection Tool** | ✅ Completed | `scripts/inspect_dataset.py` with multi-encoding fallback, missingness metrics, duplicates detection, and cardinality analysis. |
| **Dataset Preparation Pipeline** | ✅ Completed | `scripts/prepare_dataset.py` implementing target validation, `in_balanced_dataset` leakage removal, deduplication, and reproducible 80:10:10 stratified partitioning. |
| **Mentor Documentation** | ✅ Completed | `docs/dataset_preparation.md` explaining EMSCAD columns, imbalance, leakage prevention, and disjoint splits. |
| **Candidate Model Training** | ⏳ Next Phase | Training Logistic Regression, Linear SVM, Random Forest, and XGBoost on `train.csv`. |
| **SHAP Explanations** | ⏳ Next Phase | Feature attribution waterfall / token contribution plots. |
| **GenAI & SQLite History** | 📋 Part 2 Scope | LLM detail extraction, natural language summaries, and database history. |

---

## 3. Directory Structure

```
JobShield-AI/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI entrypoint, middleware & error handlers
│   │   ├── api/
│   │   │   ├── __init__.py            # API router aggregator
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       └── health.py          # GET /api/health endpoint
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py              # Pydantic Settings & CORS configuration
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── health.py              # Structured Pydantic response models
│   │   └── services/
│   │       ├── __init__.py
│   │       └── health_service.py      # Artifact verification & system health logic
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_health.py             # FastAPI health & CORS tests
│   │   └── test_dataset_preparation.py # Target mapping, deduplication & split tests
│   └── requirements.txt               # Backend & ML dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx             # Top bar with live backend status indicator
│   │   │   ├── Sidebar.jsx            # Dark security sidebar navigation
│   │   │   ├── StatusBadge.jsx        # Status pill indicator
│   │   │   └── EmptyState.jsx         # Technical honest empty-state component
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx      # Overview, architecture & dataset metrics
│   │   │   ├── AnalyzePage.jsx        # Job description input & validation
│   │   │   ├── ResultsPage.jsx        # Inference results & schema blueprint
│   │   │   └── PerformancePage.jsx    # Model comparison & PR-AUC methodology
│   │   ├── services/
│   │   │   └── api.js                 # Frontend API client (auto port fallback)
│   │   ├── App.jsx                    # Route mapping & layout wrapper
│   │   ├── main.jsx                   # React DOM root mounting
│   │   └── index.css                  # Tailwind styles & dark mode definitions
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js             # Brand palette tokens & dark configuration
│   ├── postcss.config.js
│   └── vite.config.js                 # Vite development & build setup
├── data/
│   ├── raw/                           # Raw source datasets (e.g. data/raw/DataSet.csv)
│   └── processed/                     # Cleaned partitions: train.csv, validation.csv, test.csv
├── models/                            # Trained serialized model artifacts (.joblib)
├── scripts/
│   ├── __init__.py
│   ├── inspect_dataset.py             # Data quality & encoding inspection CLI
│   └── prepare_dataset.py             # Preprocessing & stratified 80:10:10 splitting CLI
├── notebooks/                         # Exploratory data analysis (EDA) notebooks
├── docs/
│   ├── dataset_preparation.md         # Mentor guide: EMSCAD schema, imbalance, leakage & splits
│   └── ...
├── .env.example                       # Non-secret environment configuration
├── .gitignore                         # Python, Node, data, and secret exclusions
└── README.md                          # Project documentation
```

---

## 4. Visual Design System

The user interface follows a cybersecurity SaaS design:
- **Main Background**: `#101114`
- **Surface**: `#3B3F46` (with dark card elevations `#191C22` and `#21252D`)
- **Primary Accent**: `#D9B100` (Cyber Gold / Yellow)
- **Soft Accent**: `#F3DA87`
- **Primary Text**: `#F2F4F6`
- **Borders**: `#2C313C`

Decorative AI clichés (floating neon blobs, glassmorphism, chatbot interfaces, fake stats) are strictly excluded in favor of technical rigor and accessible contrast.

---

## 5. Prerequisites

- **Operating System**: Windows 10/11 (PowerShell environment)
- **Python**: 3.10+ (tested on Python 3.12.4)
- **Node.js**: 18+ (tested on Node v22.14.0, npm 10.9.2)
- **Git**

---

## 6. Windows PowerShell Setup & Run Instructions

Open separate Windows PowerShell windows for running the backend, frontend, and dataset tools:

### Terminal 1: Backend Setup & Execution

```powershell
# Navigate to workspace root
cd "c:\Users\Hp\OneDrive - IFI TECHSOLUTIONS LTD\Desktop\jobsheild ai minor"

# Install dependencies (FastAPI, Scikit-learn, XGBoost, etc.)
pip install -r backend/requirements.txt

# Start the FastAPI development server
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8008
```

The backend is accessible at:
- Root API: [http://127.0.0.1:8008/](http://127.0.0.1:8008/)
- Health Check: [http://127.0.0.1:8008/api/health](http://127.0.0.1:8008/api/health)
- Interactive OpenAPI Docs: [http://127.0.0.1:8008/docs](http://127.0.0.1:8008/docs)

### Terminal 2: Frontend Execution

```powershell
# Navigate to the frontend directory
cd "c:\Users\Hp\OneDrive - IFI TECHSOLUTIONS LTD\Desktop\jobsheild ai minor\frontend"

# Start the Vite development server
npm run dev
```

The frontend dashboard is accessible at:
- Web App: [http://localhost:5173/](http://localhost:5173/)

### Terminal 3: EMSCAD Dataset Tools (When CSV is Supplied)

Place the EMSCAD CSV file (commonly named `DataSet.csv`) in `data/raw/`, then run:

```powershell
# Inspect the raw dataset (generates data/processed/dataset_report.json)
python scripts/inspect_dataset.py --data-path data/raw/DataSet.csv

# Prepare, deduplicate, remove leakage, and generate 80:10:10 stratified splits
python scripts/prepare_dataset.py --data-path data/raw/DataSet.csv
```

Outputs generated in `data/processed/`:
- `train.csv` (80% stratified training split)
- `validation.csv` (10% stratified validation split)
- `test.csv` (10% held-out test split)
- `dataset_report.json` (comprehensive statistical report)
- `split_summary.json` (detailed split distribution and metadata)

---

## 7. Running Verification & Automated Tests

Run the complete test suite from the repository root:

```powershell
python -m pytest backend/tests/ -v
```

Expected output:
```
backend/tests/test_dataset_preparation.py::test_validate_and_map_target_valid_ft PASSED
backend/tests/test_dataset_preparation.py::test_validate_and_map_target_valid_strings_0_1 PASSED
backend/tests/test_dataset_preparation.py::test_validate_and_map_target_unexpected_labels PASSED
backend/tests/test_dataset_preparation.py::test_validate_and_map_target_null_values PASSED
backend/tests/test_dataset_preparation.py::test_validate_and_map_target_missing_column PASSED
backend/tests/test_dataset_preparation.py::test_deduplicate_dataframe PASSED
backend/tests/test_dataset_preparation.py::test_remove_leakage_columns PASSED
backend/tests/test_dataset_preparation.py::test_create_stratified_splits_integrity_and_disjointness PASSED
backend/tests/test_dataset_preparation.py::test_create_stratified_splits_reproducibility PASSED
backend/tests/test_dataset_preparation.py::test_prepare_emscad_dataset_end_to_end_on_fixture PASSED
backend/tests/test_dataset_preparation.py::test_resolve_dataset_path_missing PASSED
backend/tests/test_health.py::test_root_endpoint PASSED
backend/tests/test_health.py::test_health_endpoint_success PASSED
backend/tests/test_health.py::test_health_endpoint_details PASSED
backend/tests/test_health.py::test_cors_headers_allowed PASSED
============================== 15 passed in 8.5s ==============================
```

---

## 8. Next Steps (Proceeding to Model Training)

1. Supply the real EMSCAD CSV file (e.g. `data/raw/DataSet.csv`).
2. Run `python scripts/prepare_dataset.py` to create the processed partitions.
3. Fit TF-IDF on `train.csv` only and train the four candidate classifiers:
   - Logistic Regression
   - Linear Support Vector Machine (Linear SVM)
   - Random Forest Classifier
   - XGBoost Classifier
4. Compare validation PR-AUC, tune classification thresholds, evaluate on the test split, serialize winning artifacts to `models/`, and connect live predictions to FastAPI.
