AutoInsight — Automated Insight Generation

> **A configurable Python + Streamlit analytics engine that transforms district-level healthcare data into validated, explainable, severity-ranked insights.**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/python/)
[![Tests](https://img.shields.io/badge/Tests-46-success)](#testing)

---

## 📌 What is AutoInsight?

**AutoInsight** is an automated data-analysis and insight-generation application.
It accepts a CSV containing monthly district-level indicators, validates the data, performs multiple analytical checks, and converts the findings into human-readable insights.

Instead of manually inspecting rows and charts, a user can upload a dataset and immediately answer questions such as:

- Which indicators changed significantly?
- Which districts contain unusual values?
- Which indicators have strong relationships?
- Which findings deserve the highest attention?
- Are there data-quality problems before analysis?
- Can the findings be exported for reporting?

### Core pipeline

```text
                    CSV / Uploaded Dataset
                              │
                              ▼
                     ┌─────────────────┐
                     │  Safe Loading   │
                     └────────┬────────┘
                              ▼
                     ┌─────────────────┐
                     │ Data Validation │
                     │ + Cleaning      │
                     └────────┬────────┘
                              ▼
             ┌─────────────────────────────────┐
             │       Analytics Engine         │
             │                                 │
             │  • Trend Detection             │
             │  • Outlier Detection           │
             │  • Pearson Correlation         │
             │  • Threshold Breaches           │
             └────────────────┬────────────────┘
                              ▼
                     ┌─────────────────┐
                     │ Severity Engine │
                     └────────┬────────┘
                              ▼
                     ┌─────────────────┐
                     │ Insight Builder │
                     └────────┬────────┘
                              ▼
                  ┌───────────────────────┐
                  │ Streamlit Dashboard  │
                  │ + Filters + Charts   │
                  └───────────┬───────────┘
                              ▼
                     CSV / JSON / Reports
```

---

# ✨ Key Features

| Feature | What it does |
|---|---|
| 📥 CSV Upload | Accepts the sample dataset or a user-provided CSV |
| 🛡️ Data Validation | Checks schema, dates, numeric values, duplicates and ranges |
| 📈 Trend Detection | Finds significant period-to-period changes |
| 🎯 Outlier Detection | Supports IQR and Z-score methods |
| 🔗 Correlation Analysis | Calculates Pearson correlations between indicators |
| 🚨 Threshold Breaches | Detects user-defined absolute limits |
| ⚠️ Severity Ranking | Classifies findings as Low, Medium or High |
| 💡 Automated Insights | Converts analytical findings into explanations |
| 🔎 Filtering | Filters insights by district, period, indicator, type and severity |
| 📊 Interactive Charts | Uses Plotly for analytical visualization |
| 📤 Export | Generates CSV, JSON and correlation-matrix files |
| 🧪 Automated Tests | Includes unit and smoke tests for the analytics pipeline |

---

# 🧠 How the System Works

## 1. Data Loading

`src/data_loader.py`

The loader safely reads CSV input and converts file/read failures into controlled errors instead of allowing an uncontrolled application crash.

---

## 2. Data Validation

`src/validation.py`

Before analysis, the dataset is checked for data-quality issues.

### Required columns

The current sample schema requires:

```text
month
district
anc_coverage
institutional_delivery
immunization
high_risk_cases
```

### Validation checks

The validation layer checks:

- required columns are present;
- empty datasets;
- missing values;
- invalid month/date values;
- blank district values;
- numeric conversion;
- negative values;
- infinite values;
- percentage values greater than 100;
- exact duplicate rows;
- duplicate `(month, district)` records;
- minimum temporal coverage;
- minimum district coverage for correlation stability.

Invalid records are handled through the validation/cleaning pipeline and surfaced to the user as warnings or errors.

---

# 📈 3. Trend Detection

`src/trend_detection.py`

For each district and numeric indicator, the engine compares an observation with the previous available observation.

### Percentage-change formula

```text
Change % = ((Current Value - Previous Value) / Previous Value) × 100
```

A trend is significant when:

```text
abs(Change %) >= Trend Threshold
```

Default:

```text
Trend Threshold = 10%
```

### Example

```text
Previous ANC Coverage = 85
Current ANC Coverage  = 69

Change = ((69 - 85) / 85) × 100
       = -18.82%
```

Since:

```text
18.82% > 10%
```

the change is flagged as significant.

The engine also handles:

- first observations;
- missing values;
- zero previous values;
- non-consecutive months.

---

# 🎯 4. Outlier Detection

`src/outlier_detection.py`

Two statistical methods are available.

## IQR Method

```text
IQR = Q3 - Q1

Lower Bound = Q1 - k × IQR
Upper Bound = Q3 + k × IQR
```

Default:

```text
k = 1.5
```

A value outside the lower or upper bound is flagged as an outlier.

## Z-score Method

```text
z = (x - mean) / standard deviation
```

A value is flagged when:

```text
abs(z) >= Z-score Threshold
```

Default:

```text
Z-score Threshold = 3.0
```

The method and thresholds are configurable from the dashboard.

---

# 🔗 5. Pearson Correlation

`src/correlation.py`

The engine calculates Pearson correlation between numeric indicators.

```text
r ∈ [-1, +1]
```

Interpretation:

| Correlation | Meaning |
|---:|---|
| `+1` | Perfect positive linear relationship |
| `0` | No linear relationship |
| `-1` | Perfect negative linear relationship |

A relationship is considered strong when:

```text
abs(r) >= Correlation Threshold
```

Default:

```text
Correlation Threshold = 0.70
```

The system reports each indicator pair only once.

### Important statistical limitation

A strong correlation **does not imply causation**.

The application therefore presents correlation as an association, not proof that one indicator causes another.

It also warns when the number of districts is too small for reliable correlation interpretation.

---

# 🚨 6. Threshold-Breach Detection

In addition to statistical detection, the application supports user-defined absolute thresholds.

Examples:

### Percentage indicator

```text
ANC Coverage < configured minimum
```

### Count indicator

```text
High Risk Cases >= configured maximum
```

This is intentionally separate from:

- trends;
- outliers;
- correlations.

A value can therefore be normal statistically but still violate an operational threshold.

---

# ⚠️ 7. Severity Classification

`src/severity.py`

Every finding receives one of:

```text
LOW
MEDIUM
HIGH
```

Severity is **relative to the configured detection threshold** rather than being based on one arbitrary fixed number for every analysis type.

Conceptually:

```text
Observed Magnitude
        ÷
Detection Threshold
        =
Severity Ratio
```

Default ratio behavior:

```text
Low      < 1.20 × threshold
Medium   >= 1.20 × threshold
High     >= 1.50 × threshold
```

The dashboard allows severity cut-offs to be configured.

---

# 💡 8. Automated Insight Generation

`src/insight_generator.py`

The insight generator combines the outputs of the analytical modules into standardized insight records.

Each insight contains:

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

### Supported insight types

```text
trend
outlier
correlation
threshold_breach
```

### Example

```text
INS-0001

Type: Trend
Severity: HIGH

Indicator: ANC Coverage
District: Ahmedabad
Period: Aug 2026

Previous Value: 85
Current Value: 69
Change: -18.82%

Explanation:
ANC Coverage in Ahmedabad decreased significantly compared
with the previous period and exceeded the configured
10% change threshold.
```

The goal is not simply to return a statistical number; it is to produce a finding that a non-technical user can understand.

---

# 🏗️ Architecture

The project follows a **separation-of-concerns architecture**.

```text
                         app.py
                   Streamlit Presentation
                            │
                            ▼
                    data_loader.py
                       CSV Loading
                            │
                            ▼
                     validation.py
                    Validation/Cleaning
                            │
                            ▼
                 insight_generator.py
                    Analysis Orchestrator
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
    trend_detection   outlier_detection   correlation
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                       severity.py
                            │
                            ▼
                       Insight Records
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
          Streamlit Dashboard       Exports
```

### Design principle

The analytical engine is kept separate from Streamlit.

That means the same analysis logic can be used by:

- the dashboard;
- `run_export.py`;
- automated tests;
- a future REST API;
- another frontend.

---

# 📂 Project Structure

```text
auto_insight/
│
├── app.py
│   └── Streamlit dashboard and user interaction
│
├── run_export.py
│   └── Headless analysis + file export
│
├── requirements.txt
│   └── Python dependencies
│
├── pytest.ini
│   └── Pytest configuration
│
├── .streamlit/
│   └── config.toml
│
├── data/
│   └── district_data.csv
│       └── Sample healthcare dataset
│
├── outputs/
│   ├── insights.csv
│   ├── insights.json
│   └── correlation_matrix.csv
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── validation.py
│   ├── trend_detection.py
│   ├── outlier_detection.py
│   ├── correlation.py
│   ├── severity.py
│   ├── insight_generator.py
│   └── utils.py
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

# 📊 Dataset

The included sample dataset is:

```text
data/district_data.csv
```

Current columns:

| Column | Description | Type |
|---|---|---|
| `month` | Observation month | Period/Date |
| `district` | District name | Categorical |
| `anc_coverage` | ANC coverage percentage | Numeric |
| `institutional_delivery` | Institutional delivery percentage | Numeric |
| `immunization` | Immunization percentage | Numeric |
| `high_risk_cases` | High-risk case count | Numeric |

### Data grain

The intended observation grain is:

```text
1 row = 1 district + 1 month
```

Example:

```text
2026-07 | Ahmedabad | 85 | 91 | 93 | 10
2026-08 | Ahmedabad | 69 | 90 | 92 | 13
```

The architecture also supports additional numeric indicator columns through the indicator-discovery utilities.

---

# 🔄 End-to-End Processing

```text
1. User uploads/selects CSV
             ↓
2. CSV is loaded safely
             ↓
3. Column names are normalized
             ↓
4. Required schema is validated
             ↓
5. Dates and numeric fields are cleaned
             ↓
6. Duplicate/invalid records are checked
             ↓
7. Clean dataset is produced
             ↓
8. Trend analysis runs
             ↓
9. Outlier analysis runs
             ↓
10. Correlation analysis runs
             ↓
11. Optional threshold checks run
             ↓
12. Findings receive severity
             ↓
13. Explanations are generated
             ↓
14. Results are filtered/displayed
             ↓
15. Results can be exported
```

---

# 🖥️ Dashboard

The Streamlit interface is organized around the complete analytical workflow.

## Executive Summary

Provides a quick view of:

- total insights;
- high/medium/low severity;
- detected trends;
- detected outliers;
- strong correlations;
- dataset health.

## Insights

Provides:

- insight distribution;
- severity distribution;
- detailed insight cards;
- district/indicator/month information;
- explanations;
- filtering.

## Trends

Displays significant changes and their thresholds using interactive charts.

## Outliers

Displays detected anomalies and the selected statistical method.

## Correlation

Displays:

- correlation matrix;
- strong correlation pairs;
- sample-size warnings;
- interpretation warning about causation.

## Data & Validation

Displays:

- dataset information;
- validation status;
- data-quality issues;
- cleaned/processed data preview.

---

# ⚙️ Configuration

The dashboard exposes the main analytical parameters.

| Parameter | Default | Purpose |
|---|---:|---|
| Trend threshold | `10%` | Minimum percentage change for a trend |
| IQR multiplier | `1.5` | Outlier fence multiplier |
| Z-score threshold | `3.0` | Z-score outlier cutoff |
| Correlation threshold | `0.70` | Minimum absolute Pearson correlation |
| Severity thresholds | Configurable | Low/Medium/High classification |
| Breach thresholds | Configurable | Operational threshold detection |

This makes the engine reusable for different datasets without changing the core source code.

---

# 🚀 Installation

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd auto_insight
```

## 2. Create a virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Run the Dashboard

From the `auto_insight` directory:

```bash
python -m streamlit run app.py
```

Streamlit will provide a local URL, normally:

```text
http://localhost:8501
```

---

# 📤 Run Headless Export

For analysis without opening the dashboard:

```bash
python run_export.py
```

Generated files are written to:

```text
outputs/
├── insights.csv
├── insights.json
└── correlation_matrix.csv
```

This is useful for:

- automated workflows;
- batch analysis;
- CI/testing;
- downstream reporting.

---

# 🧪 Testing

The project contains tests covering the major analytical components.

Run:

```bash
python -m pytest -q
```

The test suite includes:

```text
test_validation.py
test_trend.py
test_outlier.py
test_correlation.py
test_severity.py
test_insights.py
test_app_smoke.py
```

### Test philosophy

Tests verify both:

1. **normal analytical behavior**
2. **edge cases**

Examples include:

- missing required columns;
- invalid values;
- duplicate records;
- zero previous values;
- no previous observation;
- outlier boundaries;
- constant-value correlation;
- correlation pair uniqueness;
- severity boundaries;
- generated insight schema.

---

# 📦 Dependencies

The project intentionally uses a lightweight Python stack:

```text
pandas
numpy
streamlit
plotly
pytest
```

### Why these libraries?

| Library | Purpose |
|---|---|
| Pandas | DataFrames, cleaning and analytical transformations |
| NumPy | Numerical/statistical operations |
| Streamlit | Interactive dashboard |
| Plotly | Interactive charts |
| Pytest | Automated testing |

No heavy ML framework is required because this project focuses on **statistical analytics and automated insight generation**, rather than predictive model training.

---

# 🔬 Statistical Methodology

## Trend

```text
Δ% = ((current - previous) / previous) × 100
```

Used to identify significant temporal changes.

## IQR

```text
IQR = Q3 - Q1

Lower = Q1 - 1.5 × IQR
Upper = Q3 + 1.5 × IQR
```

Used for robust outlier detection.

## Z-score

```text
z = (x - μ) / σ
```

Used to identify observations far from the mean.

## Pearson correlation

```text
r = Cov(X,Y) / (σX × σY)
```

Used to measure linear association between indicators.

---

# ⚠️ Important Limitations

AutoInsight is an **analytics and decision-support system**, not a causal inference or medical decision-making system.

### Correlation

A strong correlation does not establish causation.

### Small samples

Correlation and statistical summaries can be unstable with small sample sizes.

### Missing data

Removing invalid observations can change the resulting analysis.

### Thresholds

Thresholds are configuration choices and should be selected according to the domain/business context.

### Outliers

An outlier is not automatically an error. It may represent:

- a genuine event;
- a measurement problem;
- a data-entry issue;
- an unusual but valid observation.

The system flags observations for investigation rather than automatically declaring them incorrect.

---

# 🎯 Why This Architecture?

A major design goal is to keep **data processing, analytics, insight generation, and presentation separate**.

Instead of placing everything inside the Streamlit UI:

```text
Bad pattern:
app.py
 ├── load data
 ├── validate data
 ├── calculate trends
 ├── calculate outliers
 ├── calculate correlation
 ├── generate text
 └── render UI
```

the project uses:

```text
app.py
   │
   └── calls reusable analysis modules

src/
   ├── validation.py
   ├── trend_detection.py
   ├── outlier_detection.py
   ├── correlation.py
   ├── severity.py
   └── insight_generator.py
```

This improves:

- testability;
- maintainability;
- reusability;
- debugging;
- future API integration;
- separation of responsibilities.

---

# 🔮 Future Improvements

Potential next steps:

- [ ] REST API using FastAPI
- [ ] Database persistence
- [ ] Authentication and user roles
- [ ] Historical insight tracking
- [ ] Scheduled automated reports
- [ ] Email/SMS alerting
- [ ] More robust time-series methods
- [ ] Confidence intervals
- [ ] Statistical significance testing
- [ ] Forecasting
- [ ] ML-based anomaly detection
- [ ] Role-specific dashboards
- [ ] PDF report generation
- [ ] Cloud deployment
- [ ] CI/CD pipeline
- [ ] Docker support

---

# 🧑‍💻 Developer / Interview Explanation

### One-line explanation

> **AutoInsight is a configurable analytics engine that validates district-level healthcare data, detects trends, outliers and correlations, ranks findings by severity, and converts them into explainable insights through a Streamlit dashboard.**

### Explain the architecture

> I separated the project into a presentation layer and an analytics layer. Streamlit handles the UI, while the `src` modules independently handle validation, trend detection, outlier detection, correlation, severity and insight generation. This makes the core engine reusable and testable without depending on Streamlit.

### Why not machine learning?

> The problem is primarily descriptive and diagnostic analytics rather than prediction. Statistical techniques such as percentage-change analysis, IQR, Z-score and Pearson correlation are more interpretable and appropriate for automatically identifying current patterns and anomalies.

### How do you handle bad data?

> The validation layer checks schema, missing values, invalid dates, numeric conversion, negative/infinite values, duplicates and invalid ranges before analysis. The system reports issues and produces a cleaned dataset instead of allowing invalid data to silently propagate.

### How are insights generated?

> Individual analytical modules produce structured findings. The insight generator combines those findings, assigns severity based on configurable thresholds, attaches the relevant values and metadata, and generates a human-readable explanation.

---

# 📁 Output Files

After running the export workflow:

### `outputs/insights.csv`

Tabular version of generated insights.

### `outputs/insights.json`

Machine-readable version of generated insights.

### `outputs/correlation_matrix.csv`

Pearson correlation matrix between numeric indicators.

---

# 🔐 Data & Privacy

The repository is designed around local CSV processing.

No external database or cloud analytics service is required for the core workflow.

For real healthcare datasets, sensitive or personally identifiable information should **not** be committed to GitHub. Use anonymized/sample data and appropriate access controls.

---

# 📜 Project Status

**Status:** Functional analytics application with interactive Streamlit dashboard, automated insight generation, exports and automated tests.

The project is designed to be extended rather than rewritten: new analytical modules can be added to the engine while the existing dashboard and export workflows remain reusable.

---

## ⭐ Summary

```text
AutoInsight
│
├── Validate data
│
├── Clean data
│
├── Detect significant trends
│
├── Detect statistical outliers
│
├── Calculate correlations
│
├── Detect configurable threshold breaches
│
├── Rank findings by severity
│
├── Generate human-readable explanations
│
├── Visualize results
│
└── Export actionable insights
```

**AutoInsight turns raw tabular data into structured, explainable analytical findings.**
"""

path = Path("/mnt/data/README_AutoInsight_Professional.md")
path.write_text(readme, encoding="utf-8")
print(f"Created: {path}")
print(f"Size: {path.stat().st_size:,} bytes")
