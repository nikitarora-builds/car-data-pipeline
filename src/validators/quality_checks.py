import pandas as pd
from dataclasses import dataclass, field
from typing import List


@dataclass
class QualityReport:
    total_rows: int
    passed_rows: int
    failed_rows: int
    issues: List[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        return round((self.passed_rows / self.total_rows) * 100, 2) if self.total_rows else 0.0

    def summary(self) -> str:
        return (
            f"Quality Score: {self.score}% | "
            f"Passed: {self.passed_rows:,}/{self.total_rows:,} | "
            f"Issues: {len(self.issues)}"
        )


def check_nulls(df: pd.DataFrame, required_cols: List[str]) -> List[str]:
    issues = []
    for col in required_cols:
        if col not in df.columns:
            continue
        null_count = df[col].isnull().sum()
        if null_count > 0:
            pct = round(null_count / len(df) * 100, 1)
            issues.append(f"NULLs in '{col}': {null_count:,} rows ({pct}%)")
    return issues


def check_price_range(df: pd.DataFrame) -> List[str]:
    invalid = df[df["price_gbp"].notna() & ((df["price_gbp"] <= 0) | (df["price_gbp"] > 500000))]
    if len(invalid) > 0:
        return [f"Invalid price_gbp: {len(invalid):,} rows outside (0, 500000]"]
    return []


def check_year_range(df: pd.DataFrame) -> List[str]:
    invalid = df[df["year"].notna() & ((df["year"] < 1990) | (df["year"] > 2026))]
    if len(invalid) > 0:
        return [f"Invalid year: {len(invalid):,} rows outside [1990, 2026]"]
    return []


def check_fuel_type_values(df: pd.DataFrame) -> List[str]:
    valid = {"PETROL", "DIESEL", "ELECTRIC", "HYBRID", "OTHER", "UNKNOWN"}
    unknown = df[~df["fuel_type"].isin(valid)]
    if len(unknown) > 0:
        return [f"Unexpected fuel_type values: {unknown['fuel_type'].unique().tolist()}"]
    return []


def check_duplicates(df: pd.DataFrame) -> List[str]:
    dupes = df.duplicated(subset=["brand_name", "model_name", "year", "fuel_type", "price_gbp"]).sum()
    if dupes > 0:
        return [f"Duplicate records: {dupes:,} rows"]
    return []


def run_quality_checks(df: pd.DataFrame) -> QualityReport:
    required_cols = ["brand_name", "model_name", "year", "fuel_type", "transmission", "price_gbp"]
    all_issues = []
    all_issues.extend(check_nulls(df, required_cols))
    all_issues.extend(check_price_range(df))
    all_issues.extend(check_year_range(df))
    all_issues.extend(check_fuel_type_values(df))
    all_issues.extend(check_duplicates(df))

    null_rows = df[required_cols].isnull().any(axis=1).sum()
    failed = null_rows
    passed = len(df) - failed

    return QualityReport(
        total_rows=len(df),
        passed_rows=passed,
        failed_rows=failed,
        issues=all_issues,
    )
