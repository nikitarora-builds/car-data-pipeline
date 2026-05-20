import pytest
import pandas as pd
from src.transformers.normalizer import (
    normalize_uk_dataset,
    normalize_2025_dataset,
    _fuel,
    _transmission,
)


def make_uk_row(**overrides):
    base = {
        "model": " golf ",
        "year": 2020,
        "price": 15000,
        "transmission": "Manual",
        "mileage": 30000,
        "fuelType": "Petrol",
        "tax": 150,
        "mpg": 50.2,
        "engineSize": 1.6,
        "_source_brand": "Volkswagen",
        "_source_file": "vw.csv",
    }
    base.update(overrides)
    return base


class TestFuelNormalization:
    def test_petrol_variants(self):
        for val in ["Petrol", "petrol", "PETROL"]:
            assert _fuel(val) == "PETROL"

    def test_diesel_variants(self):
        for val in ["Diesel", "diesel", "DIESEL"]:
            assert _fuel(val) == "DIESEL"

    def test_electric(self):
        assert _fuel("Electric") == "ELECTRIC"

    def test_hybrid(self):
        assert _fuel("Hybrid") == "HYBRID"

    def test_unknown_falls_back(self):
        assert _fuel("CNG") == "UNKNOWN"
        assert _fuel("") == "UNKNOWN"


class TestTransmissionNormalization:
    def test_manual(self):
        assert _transmission("Manual") == "MANUAL"
        assert _transmission("manual") == "MANUAL"

    def test_automatic_variants(self):
        for val in ["Automatic", "Auto", "automatic"]:
            assert _transmission(val) in ("AUTOMATIC",)

    def test_semi_auto(self):
        assert _transmission("Semi-Auto") == "SEMI-AUTO"

    def test_unknown(self):
        assert _transmission("CVT") == "UNKNOWN"


class TestUKDatasetNormalization:
    def test_model_name_stripped_and_titled(self):
        df = pd.DataFrame([make_uk_row(model=" golf ")])
        result = normalize_uk_dataset(df)
        assert result["model_name"].iloc[0] == "Golf"

    def test_engine_size_converted_to_cc(self):
        df = pd.DataFrame([make_uk_row(engineSize=2.0)])
        result = normalize_uk_dataset(df)
        assert result["engine_size_cc"].iloc[0] == 2000.0

    def test_price_is_numeric(self):
        df = pd.DataFrame([make_uk_row(price=25000)])
        result = normalize_uk_dataset(df)
        assert result["price_gbp"].iloc[0] == 25000.0

    def test_invalid_price_becomes_nan(self):
        df = pd.DataFrame([make_uk_row(price="N/A")])
        result = normalize_uk_dataset(df)
        assert pd.isna(result["price_gbp"].iloc[0])

    def test_source_file_preserved(self):
        df = pd.DataFrame([make_uk_row(_source_file="audi.csv")])
        result = normalize_uk_dataset(df)
        assert result["source_file"].iloc[0] == "audi.csv"

    def test_multiple_brands_normalized(self):
        rows = [
            make_uk_row(_source_brand="Audi", model="A4"),
            make_uk_row(_source_brand="BMW", model="3 series"),
            make_uk_row(_source_brand="Ford", model="fiesta"),
        ]
        df = pd.DataFrame(rows)
        result = normalize_uk_dataset(df)
        assert len(result) == 3
        assert set(result["brand_name"]) == {"Audi", "BMW", "Ford"}


class TestQualityChecks:
    def test_no_issues_on_clean_data(self):
        from src.validators.quality_checks import run_quality_checks
        rows = [make_uk_row() for _ in range(10)]
        df = normalize_uk_dataset(pd.DataFrame(rows))
        report = run_quality_checks(df)
        assert report.score == 100.0

    def test_detects_null_price(self):
        from src.validators.quality_checks import run_quality_checks
        rows = [make_uk_row(price="N/A")]
        df = normalize_uk_dataset(pd.DataFrame(rows))
        report = run_quality_checks(df)
        assert any("price_gbp" in issue for issue in report.issues)

    def test_detects_invalid_year(self):
        from src.validators.quality_checks import run_quality_checks, check_year_range
        rows = [make_uk_row(year=1800)]
        df = normalize_uk_dataset(pd.DataFrame(rows))
        issues = check_year_range(df)
        assert len(issues) > 0

    def test_detects_duplicates(self):
        from src.validators.quality_checks import run_quality_checks
        row = make_uk_row()
        df = normalize_uk_dataset(pd.DataFrame([row, row]))
        report = run_quality_checks(df)
        assert any("uplicate" in issue for issue in report.issues)
