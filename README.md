# Car Data Categorization Pipeline

A production-grade ETL pipeline that ingests, normalizes, and validates **70,785 real vehicle records** across **35 brands** from two Kaggle datasets with different schemas — orchestrated with Apache Airflow and loaded to GCP BigQuery.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     DATA SOURCES                         │
│  ┌──────────────────┐      ┌──────────────────────────┐  │
│  │  UK Used Cars    │      │   Cars Dataset 2025      │  │
│  │  (Kaggle)        │      │   (Kaggle)               │  │
│  │  103,086 rows    │      │   1,218 rows             │  │
│  │  10 brand files  │      │   Different schema       │  │
│  └────────┬─────────┘      └────────────┬─────────────┘  │
└───────────┼────────────────────────────┼────────────────┘
            │                            │
            ▼                            ▼
┌─────────────────────────────────────────────────────────┐
│                    EXTRACT (ingestor.py)                  │
│  • Load per-brand CSVs with latin-1 encoding             │
│  • Tag each row with source brand & file                 │
│  • Handle schema differences between datasets            │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  TRANSFORM (normalizer.py)                │
│  • Map brand-specific field names to unified schema      │
│  • Standardize fuel types → PETROL/DIESEL/ELECTRIC/HYBRID│
│  • Standardize transmissions → MANUAL/AUTOMATIC          │
│  • Convert engine size (L) → displacement (CC)           │
│  • Deduplicate on (brand, model, year, fuel, price)      │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  VALIDATE (quality_checks.py)             │
│  • Null checks on all required fields                    │
│  • Price range validation (£0 – £500,000)               │
│  • Year range validation (1990 – 2026)                   │
│  • Fuel type enum validation                             │
│  • Duplicate detection                                   │
│  • Quality score threshold: 95% (pipeline fails if below)│
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     LOAD                                  │
│  ┌──────────────────┐      ┌──────────────────────────┐  │
│  │  CSV Output      │      │   GCP BigQuery           │  │
│  │  (save_output.py)│      │   (bigquery_loader.py)   │  │
│  │  Per-brand files │      │   car_data.normalized    │  │
│  │  + combined CSV  │      │   _cars table            │  │
│  └──────────────────┘      └──────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              ORCHESTRATION (Airflow DAG)                  │
│  • Scheduled: daily at 6 AM                             │
│  • Retries: 2x with 5-min delay                         │
│  • Email alert on failure                               │
│  • XCom metrics passed between tasks                    │
│  • Quality gate: pipeline fails if score < 95%          │
└─────────────────────────────────────────────────────────┘
```

## Dataset

| Source | Rows | Brands | Schema |
|---|---|---|---|
| UK Used Car Dataset (Kaggle) | 103,086 | 9 (Audi, BMW, Ford, Hyundai, Mercedes, Skoda, Toyota, Vauxhall, VW) | model, year, price, transmission, mileage, fuelType, mpg, engineSize |
| Cars Dataset 2025 (Kaggle) | 1,218 | 26 (global, incl. Ferrari, Lamborghini, Tesla) | Company Names, Cars Names, Engines, HorsePower, Fuel Types, Cars Prices |
| **Combined & Deduplicated** | **70,785** | **35** | **Unified normalized schema** |

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.9 |
| Orchestration | Apache Airflow 2.8 |
| Data Processing | Pandas |
| Data Quality | Custom validators (Great Expectations-style) |
| Cloud Warehouse | GCP BigQuery |
| Cloud Storage | GCP Cloud Storage |
| Testing | Pytest (19 tests) |

## Project Structure

```
car-data-pipeline/
├── pipeline.py                      # Main pipeline runner
├── dags/
│   └── categorization_pipeline.py  # Airflow DAG (daily schedule)
├── src/
│   ├── extractors/ingestor.py       # Load & tag raw brand CSVs
│   ├── transformers/normalizer.py   # Normalize to unified schema
│   ├── validators/quality_checks.py # Data quality validation
│   └── loaders/
│       ├── save_output.py           # Save to CSV
│       └── bigquery_loader.py       # Load to GCP BigQuery
├── data/
│   ├── raw/                         # Kaggle source CSVs (10 files)
│   └── processed/                   # Normalized output
└── tests/
    └── test_normalizer.py           # 19 unit tests
```

## Running Locally

```bash
git clone https://github.com/nikitarora-builds/car-data-pipeline.git
cd car-data-pipeline
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run full pipeline
python pipeline.py

# Run tests
python -m pytest tests/ -v
```

## GCP BigQuery Setup

```bash
# 1. Authenticate
gcloud auth application-default login

# 2. Set your project
export GCP_PROJECT_ID="your-gcp-project-id"

# 3. Run pipeline with BigQuery load
python -c "
from pipeline import run_pipeline
from src.loaders.bigquery_loader import load_to_bigquery
import os

df, report = run_pipeline()
load_to_bigquery(df, project_id=os.environ['GCP_PROJECT_ID'])
"
```

## Data Quality Results (Latest Run)

| Check | Result |
|---|---|
| Total rows processed | 70,785 |
| Null required fields | 1 row (0.001%) |
| Invalid price range | 200 rows (0.28%) |
| Invalid year range | 3 rows (0.004%) |
| Duplicate records | 0 |
| **Overall quality score** | **99.7%** |

## Airflow DAG

The pipeline runs daily at 6 AM via Airflow with:
- **4 tasks:** extract → transform → validate → load
- **Quality gate:** fails pipeline if quality score drops below 95%
- **Retry logic:** 2 retries with 5-minute delay
- **Alerting:** email notification on any task failure
- **Observability:** row counts and quality scores passed via XCom

## Key Design Decisions

- **Two-source ingestion:** Handles datasets with completely different schemas in a single pipeline, demonstrating real-world multi-source ETL
- **Quality gate threshold:** Pipeline intentionally fails (not just warns) if quality drops below 95%, matching production SLA expectations
- **Deduplication strategy:** Deduplicates on (brand, model, year, fuel_type, price) rather than a hash to allow intentional price updates across runs
- **Encoding handling:** latin-1 encoding for UK dataset due to special characters in manufacturer names
