# Interview Prep — Car Data Categorization Pipeline

Use this file to prepare for technical interviews. Each question includes
the answer you should give, the concept being tested, and follow-up traps.

---

## SECTION 1: Project Overview Questions

---

### Q1: "Walk me through this project."

**Your Answer:**
> "I built a production-grade ETL pipeline that ingests vehicle data from two Kaggle datasets — one with 10 brand-specific files in different schemas, and a 2025 global dataset — normalizes all of it into a unified schema, validates data quality, and loads results to GCP BigQuery. The pipeline processes 70,785 deduplicated vehicle records across 35 brands. It runs daily via an Apache Airflow DAG with retry logic and a quality gate that fails the pipeline if quality drops below 95%."

**Concept Tested:** Can you explain a project end-to-end clearly?

**Key Numbers to Remember:**
- 70,785 rows, 35 brands, 2 source datasets
- 4 pipeline stages: Extract → Transform → Validate → Load
- Daily schedule, 2 retries, 95% quality gate

---

### Q2: "Why did you build this? What problem does it solve?"

**Your Answer:**
> "In my work at AutoDap, we ingest car model data from 136 brands — each with different field naming conventions, encodings, and structures. The manual effort to reconcile these was significant and error-prone. This project automates that: given any number of brand-specific datasets with different schemas, the pipeline normalizes them into one standard format, catches data quality issues early, and delivers clean data to downstream consumers automatically."

**Concept Tested:** Business context + motivation.

---

## SECTION 2: Data Engineering Concepts

---

### Q3: "What's the difference between ETL and ELT? Which did you use and why?"

**Your Answer:**
> "ETL transforms data before loading it — good when you need to enforce quality before writing to the warehouse, or when the target system is expensive to query. ELT loads raw data first and transforms inside the warehouse — better when the warehouse (like BigQuery) is powerful and cheap to query. I used ETL here because I wanted the quality gate to run before any data hits BigQuery. If quality fails, nothing gets loaded — not even bad data."

**Follow-up:** "When would you use ELT instead?"
> "When raw data volume is massive and you want to preserve full history. BigQuery handles transformations well with dbt, so ELT with dbt is common in modern stacks."

---

### Q4: "How did you handle the fact that each brand has a different schema?"

**Your Answer:**
> "Each source dataset uses different field names for the same concept — for example, fuel type is called `fuelType`, `energy_type`, `power_source`, and `Fuel Types` across different files. I wrote brand-aware normalization functions that map each source schema to a unified target schema. The UK dataset's 10 files all share one schema, so one normalizer handles all of them. The 2025 dataset has a completely different structure, so it gets its own normalizer. Both output the same standard columns."

**Concept Tested:** Multi-source ETL, schema mapping.

---

### Q5: "Walk me through your data quality checks."

**Your Answer:**
> "I run five checks: null validation on required fields, price range validation (0 to 500,000 GBP), year range validation (1990 to 2026), fuel type enum validation, and duplicate detection on the composite key of brand, model, year, fuel type, and price. Each check returns a list of issues with row counts and percentages. I compute an overall quality score — passed rows divided by total rows. In the Airflow DAG, if this score drops below 95%, the validate task raises an exception and the pipeline fails before touching the load step."

**Follow-up:** "What if a legitimate car costs more than £500,000?"
> "Great catch — that's a configurable threshold, not a hardcoded rule. In production I'd make it configurable per brand, since Rolls-Royce and Lamborghini legitimately exceed that. The 2025 dataset includes Ferrari and Lamborghini, so I'd raise the threshold for those brands."

---

### Q6: "How did you handle deduplication? Why that approach?"

**Your Answer:**
> "I deduplicate on the composite key: brand, model name, year, fuel type, and price. I chose price as part of the key rather than just (brand, model, year, fuel type) because the same model can have multiple trim levels at different prices — and those are legitimate distinct records. This reduced 104,304 raw rows to 70,785 after merging both datasets."

**Follow-up:** "What if the price changes between runs?"
> "That's intentional — a price update would create a new record in an append scenario. In WRITE_TRUNCATE mode (which I use), each run replaces the full table, so updated prices naturally replace old ones."

---

### Q7: "Why did you use Pandas instead of PySpark for this pipeline?"

**Your Answer:**
> "At 70,000 rows, Pandas is faster and simpler — PySpark has significant overhead for small datasets due to JVM startup and cluster coordination. PySpark makes sense at 100M+ rows or when distributing across a cluster. I included PySpark in the original design for scalability, but for this dataset size, Pandas is the right tool. If this pipeline needed to process all 136 brands at AutoDap with millions of records, I'd switch to PySpark or use BigQuery's native SQL transformations."

**Concept Tested:** Right tool for the right scale.

---

## SECTION 3: Airflow Questions

---

### Q8: "Why did you use Airflow? What does it give you over a cron job?"

**Your Answer:**
> "A cron job runs a script — if it fails, you get nothing. Airflow gives you: task-level visibility (which exact step failed), automatic retries with configurable delay, dependency management between tasks, email alerts on failure, execution history and logs, and the ability to backfill missed runs. My DAG has 5 tasks — if validate fails, load never runs. With a cron job running a single script, you'd need to build all that logic yourself."

---

### Q9: "What is an Airflow DAG?"

**Your Answer:**
> "DAG stands for Directed Acyclic Graph. Directed means tasks have a defined order. Acyclic means there are no loops — tasks don't cycle back. In my pipeline, the DAG is: extract → transform → validate → load → BigQuery, with a notify_failure task that triggers if any upstream task fails. Airflow executes this graph on a schedule, manages retries, and tracks state for each run."

---

### Q10: "What is XCom in Airflow and how did you use it?"

**Your Answer:**
> "XCom (cross-communication) lets tasks pass small values to each other. I use it to pass metrics between tasks — the extract task pushes row counts, the validate task pushes the quality score. This lets the next task make decisions based on upstream results and makes these metrics visible in the Airflow UI without writing to a database."

**Follow-up:** "What's the size limit for XCom?"
> "XCom stores values in Airflow's metadata database, so large objects (DataFrames, files) should not go through XCom. For passing data between tasks, I write to a shared location — in my pipeline, the transform task writes a Parquet file to /tmp/ and the validate/load tasks read from there."

---

## SECTION 4: System Design Questions

---

### Q11: "How would you scale this pipeline to handle 10x more data?"

**Your Answer:**
> "Three levers: First, switch from Pandas to PySpark or use BigQuery native SQL for transformations — both scale horizontally. Second, move from batch to incremental processing — only ingest new/changed records rather than full reloads each day. Third, partition the BigQuery table by date or brand so queries stay fast as data grows. On the Airflow side, I'd move from a single worker to a distributed executor like Celery or Kubernetes."

---

### Q12: "How would you add a new brand to this pipeline?"

**Your Answer:**
> "Two steps: add the brand's file to `BRAND_FILE_MAP` in `ingestor.py` if it shares the UK schema, or write a new `normalize_{brand}_dataset()` function if it has a unique schema. Then add the brand to the quality check configurations. The Airflow DAG and everything else picks it up automatically on the next run. No DAG changes needed."

**Concept Tested:** Extensibility of design.

---

### Q13: "What would you add to make this production-ready?"

**Your Answer:**
> "Five things: First, data lineage tracking — record where each row came from and what transformations were applied. Second, schema versioning — store and compare schemas across runs to detect drift. Third, alerting via Slack/PagerDuty, not just email. Fourth, data contracts — formal agreements between source and target on field types and nullability. Fifth, monitoring with Prometheus and Grafana — pipeline latency, row counts, and quality score over time."

---

## SECTION 5: Tricky / Behavioural Questions

---

### Q14: "What was the hardest part of building this?"

**Your Answer:**
> "Handling the encoding issue in the UK dataset — some brand names contained special characters that caused UnicodeDecodeError with UTF-8. The fix was switching to latin-1 encoding, but the harder part was recognising the root cause: the data was exported from a Windows system that used Windows-1252 encoding, which is a superset of latin-1. It's a common real-world data engineering problem that doesn't show up in tutorials."

---

### Q15: "If you had one more week, what would you add?"

**Your Answer:**
> "An incremental load strategy. Currently the pipeline does a full reload (WRITE_TRUNCATE) every day — it replaces the entire BigQuery table. That's fine at 70K rows but won't scale. I'd add a watermark column (e.g., `ingested_at`) and only process records newer than the last successful run. This reduces processing time and cost as data grows."

---

## Quick Reference — Key Numbers

| Metric | Value |
|---|---|
| Raw rows ingested | 104,304 |
| After deduplication | 70,785 |
| Brands | 35 |
| Source datasets | 2 (UK used cars + 2025 global) |
| Quality score | 99.7% |
| Pipeline schedule | Daily at 6 AM |
| Retry attempts | 2 |
| Quality gate threshold | 95% |
| Unit tests | 19 (all passing) |
| BigQuery table | car_data.normalized_cars |
