# JobShield AI: EMSCAD Dataset Preparation & Exploration

**Document Purpose**: This guide explains the data preparation, exploratory rationale, and leakage-prevention methodology for **JobShield AI**. It is designed to be easily presented to academic mentors and technical evaluators.

---

## 1. What EMSCAD Is & What Important Columns Represent

**EMSCAD** (*Employment Scam Aegean Dataset*) was curated by researchers at the University of the Aegean (Laboratory of Information & Communication Systems Security). It is a standard benchmark dataset for studying fraudulent recruitment activity on the web.

The dataset contains approximately 17,880 real-world job postings across 18 columns, divided into four semantic groups:

| Category | Columns | Description & Role in Fraud Detection |
|---|---|---|
| **Posting Metadata** | `title`, `location`, `department`, `salary_range` | Identifies job scope, geography, and compensation. Deceptive postings often advertise unusually wide or vague salary ranges (e.g. daily wire payouts). |
| **Rich Text Bodies** | `company_profile`, `description`, `requirements`, `benefits` | Unstructured text fields. Fraudulent postings frequently lack a legitimate company profile, use generic copy-pasted requirements, or solicit personal payments. |
| **Structured Attributes** | `telecommuting`, `has_company_logo`, `has_questions`, `employment_type` | Binary indicators and employment types. Scams frequently omit logos, lack custom screening questions, and heavily favor remote work. |
| **Candidate Qualifications** | `required_experience`, `required_education`, `industry`, `function` | Expected applicant seniority and industry domain. Many entry-level scams deliberately state "No experience required" to target students. |
| **Ground Truth & Metadata** | `fraudulent`, `in_balanced_dataset` | `fraudulent` is the target label. `in_balanced_dataset` is benchmark sampling metadata. |

---

## 2. What the `fraudulent` Target Means

The `fraudulent` column represents the ground-truth binary classification label verified by researchers:
- **`0` (Legitimate)**: A verified, lawful employment or internship opportunity.
- **`1` (Fraudulent)**: A deceptive posting, upfront fee trap, identity theft scheme, or money mule solicitation.

### Label Verification & Mapping Policy
In raw EMSCAD distribution files, this target is commonly encoded as characters (`'f'` for false/legitimate, `'t'` for true/fraudulent) or numeric strings (`'0'` and `'1'`). 
Our pipeline ([scripts/prepare_dataset.py](file:///c:/Users/Hp/OneDrive%20-%20IFI%20TECHSOLUTIONS%20LTD/Desktop/jobsheild%20ai%20minor/scripts/prepare_dataset.py)):
1. Inspects raw values before any conversion.
2. Validates that every record belongs to `{f, t}` or `{0, 1}`.
3. Maps legitimate to `0` and fraudulent to `1`.
4. Halts execution with an explicit error if missing labels or unexpected categories are encountered.

---

## 3. Why the Dataset Is Imbalanced

Real-world employment fraud is an asymmetric threat: legitimate postings outnumber scam advertisements.
- **Total Postings**: ~17,880
- **Legitimate Postings (Class 0)**: ~17,014 (~95.16%)
- **Fraudulent Postings (Class 1)**: ~866 (~4.84%)
- **Imbalance Ratio**: Approximately **19.6 to 1** (only ~1 out of every 20 postings is fraudulent).

This severe imbalance mirrors production cybersecurity environments (e.g. credit card fraud, malware detection, network intrusions).

---

## 4. Why Accuracy Alone Is Not Sufficient

Standard **Classification Accuracy** measures:
$$\text{Accuracy} = \frac{\text{True Positives} + \text{True Negatives}}{\text{Total Predictions}}$$

Under a 95.16% legitimate class balance:
> A naive or trivial "dummy" model that predicts **every single job is legitimate (0)** achieves **95.16% accuracy**, yet detects **0% of fraudulent postings** (Recall = 0.0).

For job-seekers and college graduates, failing to catch a scam (**False Negative**) can result in severe financial and identity theft. Conversely, flagging a legitimate job (**False Positive**) causes minor inconvenience.

Therefore, JobShield AI prioritizes:
1. **PR-AUC (Precision-Recall Area Under Curve)**: Evaluates the tradeoff across thresholds focusing strictly on the minority fraud class.
2. **F1-Score (Minority Class)**: Harmonic mean of Precision and Recall on the fraud class:
   $$F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
3. **Confusion Matrix Analysis**: Directly inspecting False Negatives (missed scams) and False Positives.

---

## 5. Why `in_balanced_dataset` Must Be Excluded

In the original Aegean study, researchers generated a secondary balanced sub-sample (e.g., 866 fraud and 866 legitimate postings) for exploratory experiments and marked included rows with `in_balanced_dataset = 1`.

- **Data Leakage Risk**: Because all 866 fraudulent postings were automatically included in that balanced subset, having `in_balanced_dataset` in the feature matrix gives any model an artificial, cheating hint regarding label probability.
- **Production Policy**: Real-world job postings submitted to the JobShield AI inference engine will never have an `in_balanced_dataset` flag. Keeping this column would cause the model to learn benchmark artifacts rather than genuine fraud characteristics.
- **Pipeline Implementation**: `remove_leakage_columns()` automatically drops `in_balanced_dataset` from all processed datasets and feature spaces.

---

## 6. Why Duplicate Records Cause Data Leakage

Job boards frequently contain identical reposts (the same company posting the same description multiple times across different days or cities).

If identical rows exist in the raw dataset:
1. **Cross-Partition Contamination**: If one copy lands in the training set and another copy lands in the test set, the classifier will simply memorize the text tokens and predict the test sample with near-100% confidence.
2. **Over-Optimistic Metrics**: The test metrics will reflect memorization rather than generalization to unseen future scams.

### Pipeline Deduplication Policy
- [scripts/prepare_dataset.py](file:///c:/Users/Hp/OneDrive%20-%20IFI%20TECHSOLUTIONS%20LTD/Desktop/jobsheild%20ai%20minor/scripts/prepare_dataset.py) scans for exact duplicate rows across all features using `df.duplicated()`.
- Exact duplicates are pruned (retaining the first occurrence) prior to dataset partitioning.
- The exact count and percentage of pruned duplicates are logged in `data/processed/split_summary.json`.
- The raw source file in `data/raw/` remains completely unmodified.

---

## 7. Why We Need Three Disjoint Sets (Train, Validation, Test)

A simple two-way split (Train / Test) is insufficient when selecting among multiple algorithms (Logistic Regression, Linear SVM, Random Forest, XGBoost) and tuning hyper-parameters.

```
Total Cleaned Dataset (100%)
├── Training Partition (80%)      -> Used ONLY to fit model parameters & TF-IDF vocabulary
├── Validation Partition (10%)    -> Used to compare the 4 candidate models & tune decision thresholds
└── Test Partition (10%)          -> HELD OUT: Evaluated ONCE on the selected winning model
```

- **Training Set (80%)**: The algorithm learns associations between words/features and fraud labels.
- **Validation Set (10%)**: Provides an unbiased evaluation during model development to pick the best algorithm without leaking test data.
- **Test Set (10%)**: A sealed, untouched dataset simulating the real world. Testing on this split gives the true final generalization performance.

---

## 8. Why Transformations Must Be Fitted on Training Data Only

Any data transformation that learns statistics from the dataset—such as:
- **TF-IDF Vectorizer**: Token vocabulary, document frequency ($df_t$), and inverse document frequency ($IDF_t$) weights.
- **Standard Scaler / MinMax Scaler**: Mean ($\mu$) and standard deviation ($\sigma$).
- **Categorical Encoders**: Frequency counts and category mappings.

**Must be fitted strictly on the Training Partition (`train.csv`)**, and then used only to `.transform()` the validation and test sets.

> If a TF-IDF vectorizer is fitted on the entire dataset before splitting, words and inverse document frequencies from the test set leak into the training vocabulary (**lookahead bias**). In this phase, we purposefully generate only CSV partitions without fitting any vectorizer or preprocessor.

---

## 9. Missing-Value Handling Strategy

In EMSCAD, missing values (`NaN`) are common in optional fields such as `salary_range`, `company_profile`, and `requirements`.

### Strategy: Preserve Missingness in Partitioning
- **No Arbitrary Imputation**: Blindly filling text columns with arbitrary tokens like `"None"` or `"Unknown"` can mislead NLP algorithms into treating those words as meaningful signals.
- In `data/processed/` partitions (`train.csv`, `validation.csv`, `test.csv`), missing values are preserved as nulls.
- In Phase 3 (Feature Engineering & ML Training), textual fields will be safely converted into concatenated text matrices where missing components simply contribute zero tokens to the TF-IDF representation, and structured indicators (e.g. `has_company_logo == 0`) naturally capture absent attributes.

---

## 10. Split Configuration & Execution Status

### Configured Protocol
- **Stratified Partitioning**: `StratifiedShuffleSplit` logic preserving the target class ratio across all splits.
- **Fixed Random Seed**: `42` (ensures identical subsets on every run).
- **Partition Proportions**:
  - Training: **80.0%**
  - Validation: **10.0%**
  - Test: **10.0%**

### Execution Status
- All preparation scripts, target mappers, leakage exclusion policies, and stratified partitioners are implemented and verified via automated unit tests ([backend/tests/test_dataset_preparation.py](file:///c:/Users/Hp/OneDrive%20-%20IFI%20TECHSOLUTIONS%20LTD/Desktop/jobsheild%20ai%20minor/backend/tests/test_dataset_preparation.py)).
- **Real Dataset Status**: The physical raw EMSCAD CSV file is not yet present in `data/raw/` (e.g. `data/raw/DataSet.csv`). As mandated by safety protocols, no synthetic data was fabricated to substitute for the real benchmark.
- Once the real `DataSet.csv` is placed in `data/raw/`, running `python scripts/prepare_dataset.py` will generate the exact splits and populate `data/processed/split_summary.json` with the measured row counts and class distributions.
