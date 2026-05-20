import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent.parent.parent / "data" / "processed"


def save_to_csv(df: pd.DataFrame, filename: str) -> str:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / filename
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")
    return str(out_path)


def save_by_brand(df: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for brand, group in df.groupby("brand_name"):
        brand_file = brand.lower().replace(" ", "_").replace("-", "_") + "_normalized.csv"
        save_to_csv(group, brand_file)
