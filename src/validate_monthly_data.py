from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/processed/mrt_station_demand_multi_month_enriched.csv")
REPORT_PATH = Path("outputs/tables/data_quality_report.csv")
REQUIRED_COLUMNS = {
    "year_month",
    "day_type",
    "hour",
    "station_code",
    "station_name",
    "line_name",
    "tap_in_volume",
    "tap_out_volume",
    "total_volume",
}


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing processed data: {DATA_PATH}")

    data = pd.read_csv(DATA_PATH)
    missing_columns = REQUIRED_COLUMNS - set(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    critical_columns = [
        "year_month",
        "day_type",
        "station_code",
        "station_name",
        "line_name",
    ]
    null_counts = data[critical_columns].isna().sum()
    if null_counts.any():
        raise ValueError(f"Null values in critical columns: {null_counts[null_counts > 0].to_dict()}")

    numeric_columns = ["hour", "tap_in_volume", "tap_out_volume", "total_volume"]
    if (data[numeric_columns] < 0).any().any():
        raise ValueError("Negative values found in numeric demand columns")

    expected_total = data["tap_in_volume"] + data["tap_out_volume"]
    if not data["total_volume"].equals(expected_total):
        raise ValueError("total_volume does not equal tap_in_volume + tap_out_volume")

    report = pd.DataFrame(
        [
            {
                "rows": len(data),
                "months": data["year_month"].nunique(),
                "month_min": data["year_month"].min(),
                "month_max": data["year_month"].max(),
                "stations": data["station_code"].nunique(),
                "lines": data["line_name"].nunique(),
                "null_critical_values": int(null_counts.sum()),
                "quality_status": "PASS",
            }
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(REPORT_PATH, index=False)
    print(report.to_string(index=False))
    print(f"Saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
