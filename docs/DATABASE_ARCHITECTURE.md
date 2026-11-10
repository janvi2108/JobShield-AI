# JobShield AI — Database Architecture & Persistence Specification

This document details the multi-table database architecture, entity relationships, transaction guarantees, and no-API-key lifecycle for **JobShield AI: Explainable AI-Based Fraud Detection for Job & Internship Opportunities**.

---

## 1. Architectural Overview

JobShield AI uses **SQLAlchemy 2.0 ORM** with **SQLite** for zero-dependency local development and out-of-the-box offline operation. The architecture is fully compatible with **PostgreSQL** by updating the `DATABASE_URL` environment variable.

The application operates in **100% offline mode** by default without requiring an external API key (Groq or otherwise). All predictions, heuristic findings, linear feature attributions (SHAP-aligned), and deterministic explanations are calculated locally and stored transactionally.

---

## 2. Entity-Relationship Diagram

```mermaid
erDiagram
    job_analyses ||--o| fraud_predictions : "evaluates (1:1)"
    job_analyses ||--o| extracted_details : "parses (1:1)"
    job_analyses ||--o{ evidence_findings : "identifies (1:N)"
    job_analyses ||--o| ai_explanations : "synthesizes (1:1)"

    job_analyses {
        int id PK "Auto-incrementing Analysis ID"
        datetime created_at "UTC timestamp"
        datetime updated_at "UTC timestamp"
        string title "Job title (sanitized)"
        string company "Company or recruitment agency"
        text description "Raw or cleaned job description text"
        string source_url "Original URL if extracted"
        string input_type "manual | url | text"
        string status "completed | failed"
    }

    fraud_predictions {
        int id PK
        int analysis_id FK "Cascade on delete"
        boolean is_fraudulent "Binary classification verdict"
        float fraud_probability "Calibrated risk score [0.0 - 1.0]"
        string risk_level "CRITICAL | HIGH | MODERATE | LOW"
        string verdict "Human-readable verdict string"
        float decision_threshold "Model decision threshold (0.48)"
        string model_name "Linear Support Vector Machine"
        string model_version "Trained champion model"
        text heuristic_signals "JSON serialized warning indicators"
        text shap_values "JSON linear attribution tokens"
        datetime predicted_at "UTC timestamp"
    }

    extracted_details {
        int id PK
        int analysis_id FK "Cascade on delete"
        string job_title "Extracted official role title"
        string company_name "Complete organizational name"
        string location "Geographic location or tech hub"
        string employment_type "Full-time | Internship | etc."
        string required_experience "Entry | Mid | Internship"
        string required_education "Bachelors | Masters | High School"
        string compensation "Salary range or monthly stipend"
        string duration "Duration for internships/contracts"
        string work_arrangement "Remote | Hybrid | On-site"
        text required_skills "JSON array of matched skill tags"
        text requirements "Extracted qualifications"
        text responsibilities "Extracted core duties"
        float extraction_confidence "Dynamic extraction quality"
        float completeness_score "Score against core attributes"
        text missing_fields "JSON array of unpopulated fields"
        string extraction_method "deterministic | url | llm"
    }

    evidence_findings {
        int id PK
        int analysis_id FK "Cascade on delete"
        string category "financial | communication | urgency | claim"
        string indicator_name "Short name of threat signal"
        text description "Diagnostic explanation"
        string severity "critical | high | medium | low"
        text evidence_text "Matched text excerpt"
        string source_type "heuristic_scan"
        datetime detected_at "UTC timestamp"
    }

    ai_explanations {
        int id PK
        int analysis_id FK "Cascade on delete"
        text overall_summary "Grounded analysis summary"
        text primary_reasons "JSON array of key decision drivers"
        text verification_checklist "JSON array of candidate safety steps"
        text applicant_safety_verdict "Final action recommendation"
        string generation_method "deterministic_grounded_fallback | llm_groq"
        string provider_name "local | groq"
        string model_identifier "local_deterministic | llama-3.3-70b-versatile"
        datetime generated_at "UTC timestamp"
    }
```

---

## 3. Database Tables & Columns

| Table | Purpose | Cascading Deletion |
|---|---|---|
| `job_analyses` | Top-level job analysis session record | Parent |
| `fraud_predictions` | Linear SVM output, calibrated score, SHAP attributions | `ON DELETE CASCADE` |
| `extracted_details` | Context-aware NLP extracted structured job fields | `ON DELETE CASCADE` |
| `evidence_findings` | One row per heuristic threat signal detected | `ON DELETE CASCADE` |
| `ai_explanations` | Structured grounded rationale with honest generation method | `ON DELETE CASCADE` |
| `extraction_results` | Historical audit logs of standalone raw extractions | Independent |

---

## 4. File Location & Initialization

- **Default Location**: `jobshield.db` in the repository root (`C:\Users\Hp\Projects\JobShieldAI\jobshield.db`).
- **Initialization**: Automatically triggered on FastAPI startup via `backend/app/main.py`:
  ```python
  from .db.database import init_db
  init_db()
  ```
- **Alembic Migrations**: Managed via Alembic (`alembic upgrade head`).

---

## 5. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze` | Evaluates job, persists to SQLite, returns `analysis_id` in metadata |
| `GET` | `/api/analyses` | Paginated listing with search by title/company and risk filtering |
| `GET` | `/api/analyses/stats` | Live SQLite counts of total, scam, legit, and high-risk analyses |
| `GET` | `/api/analyses/{id}` | Full relational tree (prediction, details, findings, explanation) |
| `DELETE` | `/api/analyses/{id}` | Cascading deletion of an analysis and all linked records |
| `GET` | `/api/history` | Legacy-compatible endpoint for fast list queries |

---

## 6. Offline / No-API-Key Guarantees

1. When `LLM_PROVIDER=none` (the default), no external HTTP requests are made.
2. Explanations are produced by the local grounded engine and labeled as `generation_method="deterministic_grounded_fallback"`.
3. If Groq is enabled later, any network failure or timeout gracefully falls back to the deterministic engine without breaking the prediction or database persistence.

