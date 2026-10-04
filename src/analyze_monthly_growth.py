from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/processed/mrt_station_demand_multi_month_enriched.csv")
OUTPUT_DIR = Path("outputs/tables")


def main() -> None:
    data = pd.read_csv(DATA_PATH)
    data["month"] = pd.to_datetime(data["year_month"]).dt.strftime("%Y-%m")

    monthly = (
        data.groupby(["month", "station_code", "station_name", "line_name"], as_index=False)
        .agg(total_volume=("total_volume", "sum"))
    )

    pivot = monthly.pivot_table(
        index=["station_code", "station_name", "line_name"],
        columns="month",
        values="total_volume",
    ).reset_index()
    pivot.columns.name = None

    months = sorted(monthly["month"].unique())
    previous_month, latest_month = months[0], months[-1]
    has_previous = pivot[previous_month].notna()
    has_latest = pivot[latest_month].notna()
    pivot["absolute_change"] = pivot[latest_month] - pivot[previous_month]
    pivot["percent_change"] = pivot.apply(
        lambda row: (row["absolute_change"] / row[previous_month] * 100)
        if pd.notna(row[previous_month])
        and pd.notna(row[latest_month])
        and row[previous_month] != 0
        else None,
        axis=1,
    )

    # Growth is not reliable when the previous month is zero or when the
    # station name was inferred from a missing reference mapping.
    pivot["growth_quality"] = "reliable"
    pivot.loc[~has_previous | ~has_latest, "growth_quality"] = "missing_month"
    pivot.loc[pivot[previous_month] == 0, "growth_quality"] = "zero_baseline"
    pivot.loc[pivot[latest_month] == 0, "growth_quality"] = "zero_latest"
    pivot.loc[
        pivot["station_code"].astype(str).str.contains("/"),
        "growth_quality",
    ] = "interchange_code"
    pivot.loc[
        pivot["station_name"].astype(str).str.startswith("Unknown station"),
        "growth_quality",
    ] = "inferred_station"

    pivot = pivot.sort_values("percent_change", ascending=False)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "station_monthly_growth.csv"
    pivot.to_csv(output_path, index=False)

    print(f"Comparison: {previous_month} vs {latest_month}")
    print("\nTOP 10 GROWTH")
    reliable = pivot[pivot["growth_quality"] == "reliable"]
    print(reliable.head(10).to_string(index=False))
    print("\nTOP 10 DECLINES")
    print(reliable.sort_values("percent_change").head(10).to_string(index=False))
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
