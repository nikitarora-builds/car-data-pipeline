from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.trigger_rule import TriggerRule

default_args = {
    "owner": "nikita.arora",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["nikitarora.21@gmail.com"],
}

with DAG(
    dag_id="car_data_categorization_pipeline",
    default_args=default_args,
    description="Daily ETL: ingest, normalize, validate, and load car model data across 35 brands",
    schedule_interval="0 6 * * *",  # 6 AM daily
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["data-engineering", "etl", "cars"],
) as dag:

    def extract(**context):
        from src.extractors.ingestor import load_all_sources
        uk_df, df_2025 = load_all_sources()
        context["ti"].xcom_push(key="uk_rows", value=len(uk_df))
        context["ti"].xcom_push(key="rows_2025", value=len(df_2025))
        print(f"Extracted: {len(uk_df):,} UK rows + {len(df_2025):,} 2025 rows")

    def transform(**context):
        from src.extractors.ingestor import load_all_sources
        from src.transformers.normalizer import normalize_all
        uk_df, df_2025 = load_all_sources()
        normalized = normalize_all(uk_df, df_2025)
        # Save as intermediate parquet for next step
        normalized.to_parquet("/tmp/car_normalized.parquet", index=False)
        context["ti"].xcom_push(key="normalized_rows", value=len(normalized))
        print(f"Transformed: {len(normalized):,} rows")

    def validate(**context):
        import pandas as pd
        from src.validators.quality_checks import run_quality_checks
        normalized = pd.read_parquet("/tmp/car_normalized.parquet")
        report = run_quality_checks(normalized)
        print(report.summary())
        if report.score < 95.0:
            raise ValueError(f"Quality check failed: score {report.score}% is below 95% threshold")
        context["ti"].xcom_push(key="quality_score", value=report.score)
        context["ti"].xcom_push(key="issues", value=report.issues)

    def load(**context):
        import pandas as pd
        from src.loaders.save_output import save_to_csv, save_by_brand
        normalized = pd.read_parquet("/tmp/car_normalized.parquet")
        save_to_csv(normalized, "all_brands_normalized.csv")
        save_by_brand(normalized)
        print(f"Loaded {len(normalized):,} rows to processed output")

    def load_to_bigquery(**context):
        import pandas as pd
        # Requires google-cloud-bigquery + GCP credentials
        # Uncomment when GCP is configured:
        # from google.cloud import bigquery
        # client = bigquery.Client(project="your-gcp-project")
        # normalized = pd.read_parquet("/tmp/car_normalized.parquet")
        # table_id = "your-gcp-project.car_data.normalized_cars"
        # job = client.load_table_from_dataframe(normalized, table_id)
        # job.result()
        print("BigQuery load step — configure GCP credentials to enable")

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract,
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform,
    )

    validate_task = PythonOperator(
        task_id="validate",
        python_callable=validate,
    )

    load_task = PythonOperator(
        task_id="load_to_csv",
        python_callable=load,
    )

    load_bq_task = PythonOperator(
        task_id="load_to_bigquery",
        python_callable=load_to_bigquery,
    )

    notify_failure = EmailOperator(
        task_id="notify_failure",
        to="nikitarora.21@gmail.com",
        subject="[ALERT] Car Data Pipeline Failed — {{ ds }}",
        html_content="""
        <h3>Pipeline run failed on {{ ds }}</h3>
        <p>Check Airflow logs for details.</p>
        """,
        trigger_rule=TriggerRule.ONE_FAILED,
    )

    # DAG flow: extract → transform → validate → load → bigquery
    # notify_failure triggers on any upstream failure
    extract_task >> transform_task >> validate_task >> load_task >> load_bq_task
    [extract_task, transform_task, validate_task, load_task] >> notify_failure
