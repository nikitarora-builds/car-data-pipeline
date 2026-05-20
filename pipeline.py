from src.extractors.ingestor import load_all_sources
from src.transformers.normalizer import normalize_all
from src.validators.quality_checks import run_quality_checks
from src.loaders.save_output import save_to_csv, save_by_brand


def run_pipeline():
    print("=" * 60)
    print("CAR DATA CATEGORIZATION PIPELINE")
    print("=" * 60)

    # 1. Extract
    uk_df, df_2025 = load_all_sources()

    # 2. Transform
    print()
    normalized_df = normalize_all(uk_df, df_2025)

    # 3. Validate
    print("\n[VALIDATE] Running data quality checks...")
    report = run_quality_checks(normalized_df)
    print(f"  {report.summary()}")
    if report.issues:
        for issue in report.issues:
            print(f"  WARNING: {issue}")

    # 4. Load
    print("\n[LOAD] Saving processed output...")
    save_to_csv(normalized_df, "all_brands_normalized.csv")
    save_by_brand(normalized_df)

    print("\n" + "=" * 60)
    print(f"Pipeline complete. {len(normalized_df):,} rows. Quality: {report.score}%")
    print("=" * 60)
    return normalized_df, report


if __name__ == "__main__":
    run_pipeline()
