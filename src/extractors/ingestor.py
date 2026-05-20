import pandas as pd
import os
from pathlib import Path

RAW_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"

# Maps filename → brand name
BRAND_FILE_MAP = {
    "audi.csv": "Audi",
    "bmw.csv": "BMW",
    "ford.csv": "Ford",
    "hyundi.csv": "Hyundai",
    "merc.csv": "Mercedes-Benz",
    "skoda.csv": "Skoda",
    "toyota.csv": "Toyota",
    "vauxhall.csv": "Vauxhall",
    "vw.csv": "Volkswagen",
    "cclass.csv": "Mercedes-Benz",
}

# 2025 dataset has a completely different schema
DATASET_2025_FILE = "Cars Datasets 2025.csv"


def load_uk_brand_files() -> pd.DataFrame:
    """Load all UK used car brand CSVs (same schema, different brands)."""
    dfs = []
    for filename, brand in BRAND_FILE_MAP.items():
        path = RAW_DATA_DIR / filename
        if not path.exists():
            print(f"  Skipping {filename} — not found")
            continue
        df = pd.read_csv(path, encoding="latin-1")
        df["_source_brand"] = brand
        df["_source_file"] = filename
        dfs.append(df)
        print(f"  Loaded {len(df):>6} rows from {filename} ({brand})")

    combined = pd.concat(dfs, ignore_index=True)
    print(f"\n  UK dataset total: {len(combined):,} rows from {len(dfs)} files")
    return combined


def load_2025_dataset() -> pd.DataFrame:
    """Load the 2025 multi-brand dataset (different schema)."""
    path = RAW_DATA_DIR / DATASET_2025_FILE
    if not path.exists():
        raise FileNotFoundError(f"2025 dataset not found: {path}")
    df = pd.read_csv(path, encoding="latin-1")
    df["_source_file"] = DATASET_2025_FILE
    print(f"  Loaded {len(df):,} rows from {DATASET_2025_FILE}")
    return df


def load_all_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load both data sources separately (they have different schemas)."""
    print("[EXTRACT] Loading UK brand files...")
    uk_df = load_uk_brand_files()

    print("\n[EXTRACT] Loading 2025 dataset...")
    df_2025 = load_2025_dataset()

    return uk_df, df_2025
