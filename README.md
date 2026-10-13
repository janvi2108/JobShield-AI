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

This repository is currently at **Part 1 (Foundation + Working MVP Dashboard)**:

| Component | Status | Implementation Details |
|---|---|---|
| **Project Architecture** | ✅ Completed | Clean multi-tier repo (`backend/`, `frontend/`, `data/`, `models/`, `scripts/`, `notebooks/`, `docs/`). |
| **Backend API Core** | ✅ Completed | FastAPI service running on port 8000 with CORS restriction, structured error handling, and `GET /api/health`. |
| **Backend Tests** | ✅ Completed | Automated `pytest` suite validating health schema, CORS headers, and subsystem detection (100% passing). |
| **Design System** | ✅ Completed | Dedicated cybersecurity SaaS dark theme with exact brand palette tokens (`#101114`, `#3B3F46`, `#D9B100`, `#F3DA87`, `#F2F4F6`). |
| **Frontend Dashboard** | ✅ Completed | 4-stage pipeline explanation, EMSCAD dataset characteristics, live API telemetry, and session overview. |
| **Analyze Job Page** | ✅ Completed | Input validation, word/char counters, sample templates (Suspicious vs. Legitimate), and honest training check. |
| **Analysis Results Page** | ✅ Completed | Meaningful empty state + complete specification schema blueprint ready for model inference output. |
| **Model Performance Page** | ✅ Completed | Comparison breakdown for Logistic Regression, Linear SVM, Random Forest, and XGBoost with PR-AUC evaluation policy. |
| **Dataset & ML Training** | ⏳ Next Step | Data preparation on EMSCAD (17,880 records), feature extraction, and candidate training. |
| **SHAP Explanations** | ⏳ Next Step | Feature attribution waterfall / token contribution plots. |
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
│   │   └── test_health.py             # Pytest automated test cases
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
│   │   │   └── api.js                 # Frontend API client
│   │   ├── App.jsx                    # Route mapping & layout wrapper
│   │   ├── main.jsx                   # React DOM root mounting
│   │   └── index.css                  # Tailwind styles & dark mode definitions
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js             # Brand palette tokens & dark configuration
│   ├── postcss.config.js
│   └── vite.config.js                 # Vite development & build setup
├── data/
│   ├── raw/                           # Raw datasets (e.g. emscad_dataset.csv)
│   └── processed/                     # Cleaned feature matrices and splits
├── models/                            # Trained serialized model artifacts (.joblib)
├── scripts/                           # Standalone training & evaluation scripts
├── notebooks/                         # Exploratory data analysis (EDA) notebooks
├── docs/                              # Architecture diagrams & documentation
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
- **Git** (optional for version control)

---

## 6. Windows PowerShell Setup & Run Instructions

Open two separate Windows PowerShell windows: one for the backend and one for the frontend.

### Terminal 1: Backend Setup & Execution

```powershell
# Navigate to the workspace root
cd "c:\Users\Hp\OneDrive - IFI TECHSOLUTIONS LTD\Desktop\jobsheild ai minor"

# Install backend dependencies (if not already installed)
pip install -r backend/requirements.txt

# Start the FastAPI development server
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at:
- Root API: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Health Check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Interactive OpenAPI Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Terminal 2: Frontend Setup & Execution

```powershell
# Navigate to the frontend directory
cd "c:\Users\Hp\OneDrive - IFI TECHSOLUTIONS LTD\Desktop\jobsheild ai minor\frontend"

# Start the Vite development server
npm run dev
```

The frontend dashboard will be available at:
- Web App: [http://localhost:5173/](http://localhost:5173/)

---

## 7. Running Verification & Automated Tests

### Run Backend Pytest Suite

```powershell
# From the project root
python -m pytest backend/tests/ -v
```

Expected output:
```
backend/tests/test_health.py::test_root_endpoint PASSED
backend/tests/test_health.py::test_health_endpoint_success PASSED
backend/tests/test_health.py::test_health_endpoint_details PASSED
backend/tests/test_health.py::test_cors_headers_allowed PASSED
4 passed in < 1s
```

### Run Frontend Production Build

```powershell
# Inside the frontend/ directory
cd frontend
npm run build
```

This compiles optimized production static assets into `frontend/dist/`.

---

## 8. What Works Now vs. What Is Planned

### What Currently Works (Foundation Phase)
1. **Interactive Navigation**: Seamless routing across `/`, `/analyze`, `/results`, and `/performance`.
2. **Live Backend Communication**: The frontend polls `GET /api/health` to dynamically detect backend connectivity and artifact presence.
3. **Honest System Status Reporting**: Displays real subsystem state without fabricating synthetic models or metrics.
4. **Input Validation**: Minimum character count, live word/character counters, and sample template loaders.
5. **Cybersecurity Design System**: High-contrast, brand-compliant UI.

### What Remains a Placeholder (Pending Subsequent Steps)
1. **Model Training**: EMSCAD data loading, TF-IDF vectorization, and fitting candidate algorithms.
2. **Inference Predictions**: Classification probabilities and risk thresholds based on trained `.joblib` artifacts.
3. **SHAP Waterfall Visualizations**: Shapley value feature attribution computations.

---

## 9. Next Steps (Continuing Part 1)

1. **Step 2**: Inspect and ingest the EMSCAD dataset (17,880 records), perform exploratory data analysis, and establish a leakage-free stratified train/validation/test split.
2. **Step 3**: Train and compare Logistic Regression, Linear SVM, Random Forest, and XGBoost classifiers; evaluate PR-AUC and F1 scores.
3. **Step 4**: Select the top-performing model, serialize pipeline artifacts to `models/`, connect inference endpoints to FastAPI, and integrate SHAP explainability into the frontend.
