import pandas as pd
from typing import Optional

SCHEMA = [
    {"name": "brand_id", "type": "INTEGER"},
    {"name": "brand_name", "type": "STRING"},
    {"name": "model_name", "type": "STRING"},
    {"name": "year", "type": "INTEGER"},
    {"name": "fuel_type", "type": "STRING"},
    {"name": "transmission", "type": "STRING"},
    {"name": "price_gbp", "type": "FLOAT"},
    {"name": "mileage_miles", "type": "FLOAT"},
    {"name": "engine_size_cc", "type": "FLOAT"},
    {"name": "mpg", "type": "FLOAT"},
    {"name": "tax_gbp", "type": "FLOAT"},
    {"name": "data_source", "type": "STRING"},
    {"name": "source_file", "type": "STRING"},
]


def get_client(project_id: str):
    from google.cloud import bigquery
    return bigquery.Client(project=project_id)


def ensure_dataset(client, project_id: str, dataset_id: str) -> None:
    from google.cloud import bigquery
    from google.api_core.exceptions import Conflict
    dataset_ref = bigquery.Dataset(f"{project_id}.{dataset_id}")
    dataset_ref.location = "US"
    try:
        client.create_dataset(dataset_ref)
        print(f"Created dataset {project_id}.{dataset_id}")
    except Conflict:
        print(f"Dataset {dataset_id} already exists")


def load_to_bigquery(
    df: pd.DataFrame,
    project_id: str,
    dataset_id: str = "car_data",
    table_id: str = "normalized_cars",
    write_mode: str = "WRITE_TRUNCATE",
) -> int:
    """
    Load normalized DataFrame to BigQuery.

    Args:
        df: Normalized car data
        project_id: GCP project ID
        dataset_id: BigQuery dataset name
        table_id: BigQuery table name
        write_mode: WRITE_TRUNCATE (replace) or WRITE_APPEND

    Returns:
        Number of rows loaded
    """
    from google.cloud import bigquery

    client = get_client(project_id)
    ensure_dataset(client, project_id, dataset_id)

    full_table_id = f"{project_id}.{dataset_id}.{table_id}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=write_mode,
        autodetect=False,
        schema=[bigquery.SchemaField(f["name"], f["type"]) for f in SCHEMA],
    )

    # Only load columns that exist in our schema
    schema_cols = [f["name"] for f in SCHEMA]
    df_to_load = df[[c for c in schema_cols if c in df.columns]]

    job = client.load_table_from_dataframe(df_to_load, full_table_id, job_config=job_config)
    job.result()

    table = client.get_table(full_table_id)
    print(f"Loaded {table.num_rows:,} rows to {full_table_id}")
    return table.num_rows
