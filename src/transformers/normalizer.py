import pandas as pd

FUEL_TYPE_MAP = {
    "petrol": "PETROL",
    "diesel": "DIESEL",
    "electric": "ELECTRIC",
    "hybrid": "HYBRID",
    "other": "OTHER",
}

TRANSMISSION_MAP = {
    "manual": "MANUAL",
    "automatic": "AUTOMATIC",
    "semi-auto": "SEMI-AUTO",
    "auto": "AUTOMATIC",
}

BRAND_ID_MAP = {
    "Audi": 1, "BMW": 2, "Ford": 3, "Hyundai": 4,
    "Mercedes-Benz": 5, "Skoda": 6, "Toyota": 7,
    "Vauxhall": 8, "Volkswagen": 9,
}


def _fuel(val: str) -> str:
    return FUEL_TYPE_MAP.get(str(val).lower().strip(), "UNKNOWN")


def _transmission(val: str) -> str:
    return TRANSMISSION_MAP.get(str(val).lower().strip(), "UNKNOWN")


def normalize_uk_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize the UK used car dataset.
    Input columns: model, year, price, transmission, mileage,
                   fuelType, tax, mpg, engineSize, _source_brand
    """
    normalized = pd.DataFrame({
        "brand_id": df["_source_brand"].map(BRAND_ID_MAP).fillna(0).astype(int),
        "brand_name": df["_source_brand"],
        "model_name": df["model"].str.strip().str.title(),
        "year": pd.to_numeric(df["year"], errors="coerce"),
        "fuel_type": df["fuelType"].apply(_fuel),
        "transmission": df["transmission"].apply(_transmission),
        "price_gbp": pd.to_numeric(df["price"], errors="coerce"),
        "mileage_miles": pd.to_numeric(df["mileage"], errors="coerce"),
        "engine_size_cc": (pd.to_numeric(df["engineSize"], errors="coerce") * 1000).round(0),
        "mpg": pd.to_numeric(df.get("mpg", pd.Series(dtype=float)), errors="coerce"),
        "tax_gbp": pd.to_numeric(df.get("tax", pd.Series(dtype=float)), errors="coerce"),
        "data_source": "uk_used_cars",
        "source_file": df["_source_file"],
    })
    return normalized


def normalize_2025_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize the 2025 global dataset (different schema).
    Input columns: Company Names, Cars Names, Engines, CC/Battery Capacity,
                   HorsePower, Total Speed, Cars Prices, Fuel Types, Seats, Torque
    """
    normalized = pd.DataFrame({
        "brand_id": df["Company Names"].map(
            lambda x: BRAND_ID_MAP.get(str(x).strip().title(), 99)
        ),
        "brand_name": df["Company Names"].str.strip().str.title(),
        "model_name": df["Cars Names"].str.strip().str.title(),
        "year": 2025,
        "fuel_type": df["Fuel Types"].apply(_fuel),
        "transmission": "UNKNOWN",
        "price_gbp": pd.to_numeric(
            df["Cars Prices"].astype(str).str.replace(r"[^\d.]", "", regex=True),
            errors="coerce"
        ),
        "mileage_miles": None,
        "engine_size_cc": pd.to_numeric(
            df["CC/Battery Capacity"].astype(str).str.replace(r"[^\d.]", "", regex=True),
            errors="coerce"
        ),
        "mpg": None,
        "tax_gbp": None,
        "data_source": "global_2025",
        "source_file": df["_source_file"],
    })
    return normalized


def normalize_all(uk_df: pd.DataFrame, df_2025: pd.DataFrame) -> pd.DataFrame:
    print("[TRANSFORM] Normalizing UK dataset...")
    uk_normalized = normalize_uk_dataset(uk_df)
    print(f"  UK normalized: {len(uk_normalized):,} rows")

    print("[TRANSFORM] Normalizing 2025 dataset...")
    normalized_2025 = normalize_2025_dataset(df_2025)
    print(f"  2025 normalized: {len(normalized_2025):,} rows")

    combined = pd.concat([uk_normalized, normalized_2025], ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["brand_name", "model_name", "year", "fuel_type", "price_gbp"]
    )
    print(f"\n  Combined & deduplicated: {len(combined):,} rows")
    return combined
