# Car Data Categorization Pipeline

A production-grade data pipeline that ingests, normalizes, and validates car model data across 15 major automotive brands using Python, with GCP integration (BigQuery + Cloud Storage).

## Architecture

```
Raw Brand CSVs (15 brands)
        │
        ▼
  [Extractor] ──── Load per-brand CSV files
        │
        ▼
  [Transformer] ── Normalize to unified schema
        │           (fuel types, transmissions, categories)
        ▼
  [Validator] ───── Data quality checks
        │           (nulls, ranges, duplicates, enums)
        ▼
  [Loader] ──────── Save to processed output
        │           (per-brand + combined CSV / BigQuery)
        ▼
  Normalized Dataset (1,800+ rows, 15 brands, 7 years)
```

## Dataset

- **15 brands:** VW, Audi, Skoda, SEAT, BMW, Mercedes, Toyota, Honda, Ford, Hyundai, Kia, Renault, Peugeot, Nissan, Volvo
- **1,814 rows** across 105 models, 7 years (2018–2024)
- **Each brand** has its own raw schema — pipeline unifies them

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.9 |
| Orchestration | Apache Airflow 2.8 |
| Data Processing | PySpark, Pandas |
| Data Quality | Great Expectations |
| Cloud Storage | GCP Cloud Storage |
| Data Warehouse | GCP BigQuery |
| Testing | Pytest |

## Project Structure

```
car-data-pipeline/
├── pipeline.py                  # Main pipeline runner
├── dags/                        # Airflow DAGs
│   └── categorization_pipeline.py
├── src/
│   ├── extractors/ingestor.py   # Load raw brand CSVs
│   ├── transformers/normalizer.py # Normalize to unified schema
│   ├── validators/quality_checks.py # Data quality validation
│   └── loaders/save_output.py   # Save processed output
├── data/
│   ├── raw/                     # Per-brand source CSVs
│   └── processed/               # Normalized output
├── tests/                       # Unit & integration tests
└── docs/                        # Architecture & data model docs
```

## Normalized Schema

| Field | Type | Description |
|---|---|---|
| brand_id | int | Unique brand identifier |
| brand_name | str | Standardized brand name |
| model_name | str | Standardized model name |
| variant | str | Trim/variant level |
| year | int | Production year |
| fuel_type | enum | PETROL / DIESEL / ELECTRIC / HYBRID |
| engine_cc | int | Engine displacement (null for EVs) |
| transmission | enum | MANUAL / AUTOMATIC |
| price_usd | float | Listed price in USD |
| fuel_efficiency_kmpl | float | Fuel efficiency (null for EVs) |
| electric_range_km | int | EV range in km (null for ICE) |
| category | enum | HATCHBACK / SEDAN / SUV / COUPE etc. |
| country_of_manufacture | str | Manufacturing country |
| data_source | str | Source schema identifier |

## Running Locally

```bash
# Clone the repo
git clone https://github.com/nikitaarora23/car-data-pipeline.git
cd car-data-pipeline

# Set up virtual environment
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Generate mock data
python data/raw/generate_mock_data.py

# Run the full pipeline
python pipeline.py
```

## Data Quality Checks

The validator runs the following checks on every pipeline run:
- **Null checks** on all required fields
- **Price range** validation (0–500,000 USD)
- **Year range** validation (2000–2025)
- **Fuel type enum** validation
- **Duplicate detection** on (brand, model, variant, year, fuel_type)

## Key Design Decisions

- Each brand has its own raw schema — the normalizer handles brand-specific mappings rather than forcing a rigid input format
- Quality score is computed per-run and surfaced in pipeline logs for monitoring
- Output is saved both as a combined file and per-brand files for flexible downstream consumption

## Next Steps (GCP Integration)

- [ ] Upload raw files to GCP Cloud Storage on ingestion
- [ ] Load normalized output to BigQuery
- [ ] Airflow DAG for scheduled daily runs
- [ ] Alert on quality score drops below 95%
