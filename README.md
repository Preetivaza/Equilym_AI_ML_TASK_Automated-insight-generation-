# AutoInsight — Automated Insight Generation Engine

> **A configurable Python + Streamlit analytics engine that validates district-level healthcare data, detects statistically meaningful patterns, and converts them into explainable, severity-ranked insights.**

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50%2B-red?logo=streamlit)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Visualization-3F4F75?logo=plotly)](https://plotly.com/python/)
[![Tests](https://img.shields.io/badge/Tests-46-lightgrey)](#testing)

---

## 1. What is this project?

**AutoInsight** is an automated analytics and insight-generation system for district-level healthcare data.

Instead of manually inspecting a CSV and looking for changes, anomalies, or relationships, the application performs the analysis automatically:

```text
CSV Dataset
    ↓
Safe Loading
    ↓
Data Validation & Cleaning
    ↓
┌──────────────────────────────────────────────┐
│ Trend Detection                              │
│ Outlier Detection                            │
│ Pearson Correlation                          │
│ Optional Threshold-Breach Detection          │
└──────────────────────────────────────────────┘
    ↓
Severity Classification
    ↓
Human-Readable Insight Generation
    ↓
Streamlit Dashboard
    ↓
CSV / JSON / Correlation Matrix Exports
```

The system is **data-driven**: district names, indicator values, periods, changes, correlations, and insight counts are generated from the uploaded dataset rather than being hardcoded.

---

## 2. Main objectives

The project is designed to:

- validate incoming CSV data safely;
- clean unusable or invalid records without crashing the application;
- identify significant month-to-month changes;
- detect statistical outliers;
- discover strong relationships between indicators;
- optionally detect values outside user-defined absolute limits;
- assign **Low / Medium / High** severity to findings;
- generate readable explanations containing the actual observed values;
- present results through an interactive Streamlit dashboard;
- export the generated insights for further use.

---

## 3. Key features

### Data validation

The validation layer checks:

- empty datasets;
- required columns;
- missing values;
- valid dates/months;
- numeric indicator columns;
- negative/infinite values;
- values above 100 for percentage-style indicators;
- exact duplicate rows;
- duplicate `(district, month)` keys;
- minimum district/month coverage.

Invalid rows/values are handled and reported rather than causing an uncontrolled application crash.

### Trend detection

For each district and numeric indicator, the engine compares the current observation with the previous observed period:

```text
percentage change = (current - previous) / previous × 100
```

A trend becomes significant when:

```text
|percentage change| >= configured trend threshold
```

Default threshold: **10%**.

The engine also handles:

- first observations with no previous value;
- missing values;
- previous value equal to zero;
- non-consecutive months.

### Outlier detection

Two methods are supported.

#### IQR method

```text
IQR = Q3 - Q1

Lower fence = Q1 - k × IQR
Upper fence = Q3 + k × IQR
```

A value is an outlier when it lies outside the corresponding fence.

Default:

```text
k = 1.5
```

#### Z-score method

```text
z = (x - mean) / standard deviation
```

A value is flagged when:

```text
|z| >= configured z-score threshold
```

Default threshold: **3.0**.

### Pearson correlation

The engine calculates a Pearson correlation matrix across numeric indicators and reports each unordered pair only once.

A pair is flagged when:

```text
|r| >= configured correlation threshold
```

Default threshold: **0.70**.

The generated insight explicitly states:

> Correlation does not imply causation.

The system also warns when the number of districts is below the recommended minimum for stable correlation estimates.

### Optional threshold-breach detection

The dashboard can additionally flag absolute threshold violations defined by the user.

For percentage-style indicators:

```text
value < configured minimum
```

For count-style indicators:

```text
value >= configured maximum
```

This is intentionally separate from the statistical trend/outlier/correlation analysis.

### Severity classification

Findings are classified as:

- **Low**
- **Medium**
- **High**

Severity is based on how strongly the observed result exceeds its configured detection threshold rather than using one hardcoded cutoff for every analysis type.

The dashboard allows the severity cut-offs to be configured.

### Automated explanations

Every generated insight contains:

- unique insight ID;
- analysis type;
- indicator;
- district/entity;
- period;
- observed value;
- comparison/baseline value when applicable;
- percentage change when applicable;
- severity;
- human-readable explanation.

Example structure:

```text
INS-0001
Type: trend
Severity: High
Indicator: ANC Coverage
District: Mehsana
Period: Aug 2026

ANC Coverage in Mehsana decreased by 18.8% in Aug 2026
compared with the previous month (85% → 69%), exceeding
the 10% significant-change threshold.
```

---

## 4. Architecture

The project follows a separation-of-concerns design:

```text
                    ┌──────────────────┐
                    │   Streamlit UI   │
                    │     app.py       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Data Loader    │
                    │ data_loader.py   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Validation     │
                    │ validation.py    │
                    └────────┬─────────┘
                             │ clean DataFrame
                             ▼
              ┌──────────────────────────────┐
              │      Insight Generator      │
              │   insight_generator.py      │
              └──────────────┬───────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Trends    │     │   Outliers   │     │ Correlation  │
│ trend_       │     │ outlier_     │     │ correlation  │
│ detection.py │     │ detection.py │     │ .py          │
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                    ┌──────────────────┐
                    │ Severity Engine  │
                    │   severity.py    │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ Insight Results  │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ Dashboard/Export │
                    └──────────────────┘
```

### Important architectural rule

`src/` contains the analytics/business logic and does **not** depend on Streamlit.

This makes the analysis engine reusable from:

- the Streamlit application;
- the headless export script;
- automated tests;
- future APIs or other frontends.

---

## 5. Project structure

```text
auto_insight/
│
├── app.py                         # Streamlit dashboard / presentation layer
├── run_export.py                  # Headless analysis + export script
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Pytest configuration
│
├── .streamlit/
│   └── config.toml                # Streamlit theme/server configuration
│
├── data/
│   └── district_data.csv          # Sample input dataset
│
├── outputs/
│   ├── insights.csv               # Generated insights
│   ├── insights.json              # Generated insights in JSON
│   └── correlation_matrix.csv     # Pearson correlation matrix
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py             # Safe CSV loading
│   ├── validation.py              # Data validation + cleaning
│   ├── trend_detection.py         # Month-to-month trend detection
│   ├── outlier_detection.py       # IQR / Z-score detection
│   ├── correlation.py             # Pearson correlation analysis
│   ├── severity.py                # Severity rules
│   ├── insight_generator.py       # Combines analyses into insights
│   └── utils.py                   # Shared constants/helpers
│
└── tests/
    ├── helpers.py
    ├── test_app_smoke.py
    ├── test_validation.py
    ├── test_trend.py
    ├── test_outlier.py
    ├── test_correlation.py
    ├── test_severity.py
    └── test_insights.py
```

---

## 6. Input dataset format

The sample dataset is:

```text
data/district_data.csv
```

### Required columns

```text
month
district
anc_coverage
institutional_delivery
immunization
high_risk_cases
```

Conceptually:

| Column | Meaning | Typical type |
|---|---|---|
| `month` | Observation month | Date / `YYYY-MM` |
| `district` | District/entity name | String |
| `anc_coverage` | ANC coverage | Percentage |
| `institutional_delivery` | Institutional delivery coverage | Percentage |
| `immunization` | Immunization coverage | Percentage |
| `high_risk_cases` | High-risk cases | Count |

The engine can also analyze **additional numeric columns** automatically. Non-numeric extra columns are ignored by the analysis layer.

### Data assumptions

The intended grain is:

```text
one row = one district + one month
```

The validation layer normalizes date values to monthly periods such as:

```text
2026-07
2026-08
```

---

## 7. Data processing pipeline

### Step 1 — Read CSV

`src/data_loader.py` safely reads the input file.

Read errors are converted into a validation report instead of allowing the UI to crash.

### Step 2 — Normalize column names

Column names are stripped and converted to lowercase.

### Step 3 — Validate schema

Required columns are checked before analysis begins.

### Step 4 — Validate dates and districts

Invalid/missing months and blank districts are removed with warnings.

### Step 5 — Convert numeric indicators

Required indicator columns are converted to numeric values where possible.

Non-numeric values are treated as missing and reported.

### Step 6 — Validate numeric ranges

Negative and infinite values are invalid.

For percentage-style indicators, values above 100 are also invalid.

### Step 7 — Remove duplicates

The engine checks:

1. exact duplicate rows;
2. duplicate `(district, month)` keys.

### Step 8 — Check coverage

The engine warns when there are:

- fewer than 3 months available for a district;
- fewer than 10 districts for correlation stability.

These are warnings rather than universal blocking conditions.

### Step 9 — Run analytics

The cleaned dataset is passed to the trend, outlier, correlation, and optional breach detectors.

### Step 10 — Generate insights

Findings are converted into standardized insight records and sorted by severity/type.

---

## 8. Insight generation model

The central orchestration function is:

```python
from src.insight_generator import generate_insights

result = generate_insights(df)
```

It returns an `AnalysisResult` containing:

```text
insights
corr_matrix
corr_pairs
trends
outliers
breaches
indicators
count_indicators
```

The `insights` DataFrame uses this schema:

```text
insight_id
type
indicator
entity
period
value
prev_value
change_pct
severity
explanation
```

### Insight types

```text
trend
outlier
correlation
threshold_breach
```

Insight IDs are generated dynamically:

```text
INS-0001
INS-0002
INS-0003
...
```

---

## 9. Severity logic

Severity is threshold-relative.

For ratio-based findings, conceptually:

```text
ratio = observed magnitude / configured threshold
```

Default ratio cut-offs:

```text
Low      < 1.20
Medium   >= 1.20
High     >= 1.50
```

For correlation, severity uses threshold headroom so the classification scales with the selected correlation threshold.

The exact implementation is centralized in:

```text
src/severity.py
```

This prevents severity rules from being duplicated across trend/outlier/correlation logic.

---

## 10. Streamlit dashboard

Run the dashboard with:

```bash
python -m streamlit run app.py
```

The dashboard provides:

### Control Panel

- Sample dataset / uploaded CSV
- Trend threshold
- IQR / Z-score selection
- IQR multiplier
- Z-score threshold
- Correlation threshold
- Severity cut-offs
- Optional threshold breach settings
- District filter
- Month filter
- Indicator filter
- Severity filter
- Insight-type filter

### Executive summary

Displays:

- total insights;
- high-severity findings;
- medium-severity findings;
- low-severity findings;
- selected districts;
- detected trends;
- detected outliers;
- strong correlations.

### Insights tab

Provides:

- severity distribution;
- insight-type distribution;
- per-district indicator line chart;
- detailed insight cards;
- severity explanation.

### Trends tab

Shows trend findings and the configured significant-change threshold.

### Outliers tab

Shows detected anomalies and the selected IQR/Z-score method.

### Correlation tab

Shows:

- Pearson correlation matrix;
- strong correlation pairs;
- sample-size warnings;
- causation warning.

### Data & Validation tab

Shows:

- dataset information;
- validation checks;
- missing-value information;
- cleaned data preview.

---

## 11. Filtering vs analysis

A key design decision is that **sidebar filters primarily control what is displayed**, while the analytics are computed from the cleaned dataset.

In other words:

```text
Uploaded data
    ↓
Validation
    ↓
Analysis
    ↓
Generated insights
    ↓
UI filters
    ↓
Displayed subset
```

This avoids silently changing statistical calculations merely because a user changed a display filter.

---

## 12. Exports

The application provides three downloads from the sidebar.

### Insights CSV

```text
outputs/insights.csv
```

Contains the standardized insight schema.

### Insights JSON

```text
outputs/insights.json
```

Contains the same insight records in JSON format.

### Correlation matrix

```text
outputs/correlation_matrix.csv
```

Contains the complete Pearson correlation matrix.

---

## 13. Headless execution

The project can also run without Streamlit using:

```bash
python run_export.py
```

This script:

1. loads `data/district_data.csv`;
2. validates the dataset;
3. prints the validation report;
4. generates insights;
5. writes the three output files under `outputs/`.

This is useful for batch execution, testing, demonstrations, and future automation.

---

## 14. Installation

### Prerequisites

- Python 3.x
- pip
- virtual environment recommended

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Dependencies

```text
pandas
numpy
streamlit>=1.50
plotly
pytest
```

---

## 15. Run the project

### Start the dashboard

```bash
python -m streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal, normally:

```text
http://localhost:8501
```

### Generate exports without the dashboard

```bash
python run_export.py
```

### Run tests

```bash
python -m pytest -q
```

---

## 16. Testing

The project contains **46 automated tests** covering the main analytics and validation behavior.

Test areas include:

| Test module | Purpose |
|---|---|
| `test_validation.py` | Schema, missing values, invalid values, duplicates, dates, coverage |
| `test_trend.py` | Percentage-change formula, thresholds, missing/zero previous values, month gaps |
| `test_outlier.py` | IQR, Z-score, missing values, small samples, explanations |
| `test_correlation.py` | Pearson correlation, unique pairs, thresholds, sign, sample warnings |
| `test_severity.py` | Severity ratios, configurable cut-offs, correlation headroom |
| `test_insights.py` | End-to-end insight generation, dynamic values, exports, threshold breaches |
| `test_app_smoke.py` | Streamlit dashboard startup, filters, displayed values |

### Important

Run tests after installing dependencies from `requirements.txt`.

---

## 17. Configuration

The Streamlit theme is configured in:

```text
.streamlit/config.toml
```

Current configuration uses a light dashboard theme with an indigo primary color and wide layout.

Analysis parameters are configured at runtime through `AnalysisConfig`:

```python
AnalysisConfig(
    trend_threshold=10.0,
    outlier_method="IQR",
    iqr_k=1.5,
    z_threshold=3.0,
    corr_threshold=0.70,
    enable_breach=True,
    breach_floor=70.0,
    breach_ceiling=20.0,
)
```

---

## 18. Important statistical limitations

### Small datasets

The sample data contains only a small number of district/month observations. Correlations calculated from very small samples can be unstable.

The application therefore reports a warning when fewer than **10 districts** or **3 months** are available according to the project recommendations.

### Trend limitations

With only two months, a trend represents only one month-to-month comparison.

### Z-score limitations

For very small samples, Z-score behavior is constrained by sample size. IQR is generally the safer default for small datasets.

### Missing values

A trend cannot be computed when either the current or previous observation is missing, and percentage change is undefined when the previous value is zero.

### Correlation is not causation

A high Pearson correlation indicates linear association, not a causal relationship.

### No causal or predictive modeling

This project is an **automated descriptive analytics and insight-generation engine**. It does not claim to perform causal inference, forecasting, or clinical diagnosis.

---

## 19. Design principles

### Data-driven

No district, indicator, insight count, or observed numeric result is hardcoded into the analytics logic.

### Explainable

Every finding has a human-readable explanation that exposes the underlying comparison or statistical evidence.

### Configurable

Thresholds can be adjusted without modifying the core algorithms.

### Modular

Each analytical task is isolated into its own module.

### Safe

Bad files and malformed records are reported through validation instead of causing uncontrolled failures.

### Testable

The analytics layer is independent from Streamlit, making it straightforward to test independently.

---

## 20. How the modules work together

### `data_loader.py`

Responsible for safely reading CSV files and returning a `ValidationReport`.

### `validation.py`

Responsible for schema validation, cleaning, type conversion, range checks, duplicates, and coverage warnings.

### `trend_detection.py`

Responsible only for calculating month-to-month percentage changes and identifying significant changes.

### `outlier_detection.py`

Responsible for IQR and Z-score anomaly detection.

### `correlation.py`

Responsible for Pearson correlation matrices, unique strong-correlation pairs, and sample-size warnings.

### `severity.py`

Responsible for converting statistical magnitude into Low/Medium/High severity.

### `insight_generator.py`

The orchestration layer. It calls the individual detectors, converts findings into standardized insight records, and generates explanations.

### `utils.py`

Contains shared constants, indicator detection, formatting helpers, and month utilities.

### `app.py`

Presentation layer only: controls, filters, charts, insight cards, validation display, and exports.

### `run_export.py`

Headless entry point for regenerating output files without starting Streamlit.

---

## 21. Example end-to-end usage

1. Start the dashboard.
2. Select **Sample dataset** or upload a CSV.
3. The application validates the data automatically.
4. Review warnings in **Data & Validation**.
5. Configure detection thresholds in the sidebar.
6. Review the executive summary.
7. Inspect individual findings under **Insights**.
8. Investigate trends and outliers.
9. Review the Pearson correlation matrix.
10. Apply filters to focus on specific districts/indicators.
11. Export the filtered insights as CSV/JSON.

---

## 22. Interview-ready explanation

### What does this project do?

> AutoInsight is a Python-based automated analytics engine that takes district-level healthcare data, validates and cleans it, detects significant trends, statistical outliers, and strong correlations, assigns severity levels, and converts the findings into explainable insights. I built the analytics as modular Python components and used Streamlit for the interactive dashboard and exports.

### Why did you separate `src/` from `app.py`?

> I separated the business logic from the presentation layer so the analytics engine is independent of Streamlit. This makes the algorithms reusable, testable, and easier to integrate later with an API or another frontend.

### How do you detect trends?

> For each district and indicator, I calculate percentage change from the previous observed period. If the absolute percentage change is greater than or equal to the configured threshold, I generate a trend insight.

### How do you detect outliers?

> I support both IQR and Z-score methods. IQR flags observations outside Q1 minus k times IQR and Q3 plus k times IQR, while Z-score flags observations whose absolute standardized score exceeds the configured threshold.

### How do you handle correlation?

> I calculate a Pearson correlation matrix for numeric indicators and report each unordered pair once when its absolute correlation exceeds the configured threshold. I also explicitly warn that correlation does not imply causation and flag small-sample situations.

### How are insights generated?

> The individual detectors return structured results. The insight generator converts those results into a common schema containing the type, entity, period, value, severity, and a data-driven explanation. This makes the output consistent and exportable.

### How do you avoid hardcoding results?

> District names, indicator names, values, periods, and insight counts come directly from the validated dataset. The tests also verify that district-specific hardcoding is not present in the source.

---

## 23. Future improvements

Possible extensions include:

- REST API using FastAPI;
- database persistence;
- role-based access control;
- scheduled/batch analysis;
- richer anomaly detection methods;
- time-series forecasting;
- confidence intervals and statistical significance tests;
- configurable domain-specific validation rules;
- dashboard authentication;
- cloud deployment;
- alerting through email/SMS/webhooks;
- experiment tracking and model monitoring if predictive ML is added.

These are future extensions and are **not required for the current descriptive analytics engine**.

---

## 24. Project status

**Current scope:** Automated descriptive analytics + explainable insight generation.

**Core analysis:** Validation, trends, outliers, Pearson correlation, severity classification, optional threshold breaches.

**Interface:** Streamlit dashboard.

**Exports:** CSV, JSON, correlation matrix CSV.

**Testing:** 46 automated tests covering validation, analytics, insight generation, exports, and dashboard smoke behavior.

---

## 25. Quick command reference

```bash
# Install
pip install -r requirements.txt

# Run dashboard
python -m streamlit run app.py

# Generate exports
python run_export.py

# Run tests
python -m pytest -q
```

---

## License

Add the appropriate license before public distribution if required by the project or organization.
