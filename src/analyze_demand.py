from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/processed/mrt_station_demand_enriched_202608.csv")
OUTPUT_DIR = Path("outputs/tables")


def main() -> None:
    data = pd.read_csv(DATA_PATH)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    station_summary = (
        data.groupby(["station_code", "station_name", "line_name"], as_index=False)
        .agg(
            total_volume=("total_volume", "sum"),
            avg_hourly_volume=("total_volume", "mean"),
            peak_hour_volume=("total_volume", "max"),
        )
        .sort_values("total_volume", ascending=False)
    )

    line_summary = (
        data.groupby("line_name", as_index=False)
        .agg(
            total_volume=("total_volume", "sum"),
            station_count=("station_code", "nunique"),
            avg_hourly_volume=("total_volume", "mean"),
        )
        .sort_values("total_volume", ascending=False)
    )

    hourly_summary = (
        data.groupby(["day_type", "hour"], as_index=False)
        .agg(
            total_volume=("total_volume", "sum"),
            avg_station_volume=("total_volume", "mean"),
        )
        .sort_values(["day_type", "hour"])
    )

    day_type_summary = (
        data.groupby("day_type", as_index=False)
        .agg(
            total_volume=("total_volume", "sum"),
            avg_hourly_volume=("total_volume", "mean"),
        )
    )

    station_summary.to_csv(OUTPUT_DIR / "station_summary.csv", index=False)
    line_summary.to_csv(OUTPUT_DIR / "line_summary.csv", index=False)
    hourly_summary.to_csv(OUTPUT_DIR / "hourly_summary.csv", index=False)
    day_type_summary.to_csv(OUTPUT_DIR / "day_type_summary.csv", index=False)

    print("TOP 10 STATIONS")
    print(station_summary.head(10).to_string(index=False))
    print("\nLINE SUMMARY")
    print(line_summary.to_string(index=False))
    print("\nDAY TYPE SUMMARY")
    print(day_type_summary.to_string(index=False))
    print(f"\nSaved analysis tables to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
