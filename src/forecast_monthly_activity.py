from pathlib import Path

import numpy as np
import pandas as pd


DATA_PATH = Path("data/processed/mrt_station_demand_multi_month_enriched.csv")
OUTPUT_PATH = Path("outputs/tables/monthly_activity_forecast.csv")


def build_forecast(data: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        data.assign(month=pd.to_datetime(data["year_month"]))
        .groupby("month", as_index=False)["total_volume"]
        .sum()
        .sort_values("month")
    )
    if len(monthly) < 3:
        raise ValueError("At least 3 months are required for the baseline forecast")

    x = np.arange(len(monthly), dtype=float)
    y = monthly["total_volume"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    next_month = monthly["month"].max() + pd.offsets.MonthBegin(1)
    forecast = max(0.0, slope * len(monthly) + intercept)

    result = monthly.rename(columns={"month": "year_month", "total_volume": "activity"})
    result["record_type"] = "actual"
    result = pd.concat(
        [
            result,
            pd.DataFrame(
                {
                    "year_month": [next_month],
                    "activity": [forecast],
                    "record_type": ["baseline_forecast"],
                }
            ),
        ],
        ignore_index=True,
    )
    return result


def main() -> None:
    data = pd.read_csv(DATA_PATH)
    result = build_forecast(data)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)
    print(result.to_string(index=False))
    print(f"Saved to: {OUTPUT_PATH}")
    print("Note: baseline linear trend only; not a production forecast.")


if __name__ == "__main__":
    main()
