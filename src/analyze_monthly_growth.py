"""Shared month-over-month calculations for the app and exported tables."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/processed/mrt_station_demand_multi_month_enriched.csv"
OUTPUT_DIR = ROOT / "outputs/tables"
MOVEMENT_COLUMNS = [
    "previous_month", "latest_month", "station_code", "station_name", "line_name",
    "previous_activity", "latest_activity", "absolute_change", "percent_change",
    "growth_quality",
]
SUMMARY_COLUMNS = [
    "previous_month", "latest_month", "previous_codes", "latest_codes", "common_codes",
    "comparable_codes", "previous_only_codes", "latest_only_codes",
    "changed_hour_coverage_codes", "previous_recorded_activity", "latest_recorded_activity",
    "previous_comparable_activity", "latest_comparable_activity", "absolute_change",
    "percent_change",
]


def prepare_data(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    result["month_label"] = pd.to_datetime(result["year_month"]).dt.strftime("%Y-%m")
    keys = ["month_label", "station_code", "day_type", "hour"]
    if result.duplicated(keys).any():
        raise ValueError("Duplicate month/station/day-type/hour records must be resolved first")
    return result


def monthly_coverage(data: pd.DataFrame) -> pd.DataFrame:
    return (
        prepare_data(data).groupby("month_label", as_index=False)
        .agg(station_codes=("station_code", "nunique"), records=("station_code", "size"),
             recorded_activity=("total_volume", "sum"))
        .sort_values("month_label")
    )


def build_monthly_comparisons(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare every consecutive calendar-month pair in the supplied scope.

    Codes must appear in both months with the same observed (day_type, hour)
    cells. Missing rows are never filled with zero. Metadata is taken from the
    later month; a name/line-label change does not change the code's identity.
    """
    data = prepare_data(data)
    months = sorted(data["month_label"].unique())
    movement_rows, summary_rows = [], []
    for previous, latest in zip(months, months[1:]):
        if pd.Period(latest, freq="M") - 1 != pd.Period(previous, freq="M"):
            continue
        before = data[data["month_label"].eq(previous)]
        after = data[data["month_label"].eq(latest)]
        before_totals = before.groupby("station_code")["total_volume"].sum()
        after_totals = after.groupby("station_code")["total_volume"].sum()
        before_codes, after_codes = set(before_totals.index), set(after_totals.index)
        common = before_codes & after_codes
        before_cells = {
            code: frozenset(zip(group["day_type"], group["hour"]))
            for code, group in before.groupby("station_code")
        }
        after_cells = {
            code: frozenset(zip(group["day_type"], group["hour"]))
            for code, group in after.groupby("station_code")
        }
        comparable = {code for code in common if before_cells[code] == after_cells[code]}
        metadata = pd.concat([before, after]).drop_duplicates("station_code", keep="last").set_index("station_code")
        for code in sorted(before_codes | after_codes):
            old = before_totals.get(code, float("nan"))
            new = after_totals.get(code, float("nan"))
            if code not in before_codes:
                quality = "missing_previous_month"
            elif code not in after_codes:
                quality = "missing_latest_month"
            elif code not in comparable:
                quality = "changed_hour_coverage"
            elif old == 0:
                quality = "zero_baseline"
            else:
                quality = "comparable"
            change = new - old if code in comparable else float("nan")
            movement_rows.append({
                "previous_month": previous, "latest_month": latest, "station_code": code,
                "station_name": metadata.loc[code, "station_name"],
                "line_name": metadata.loc[code, "line_name"],
                "previous_activity": old, "latest_activity": new,
                "absolute_change": change,
                "percent_change": change / old * 100 if quality == "comparable" else float("nan"),
                "growth_quality": quality,
            })
        old_total = before_totals.reindex(sorted(comparable)).sum()
        new_total = after_totals.reindex(sorted(comparable)).sum()
        summary_rows.append({
            "previous_month": previous, "latest_month": latest,
            "previous_codes": len(before_codes), "latest_codes": len(after_codes),
            "common_codes": len(common), "comparable_codes": len(comparable),
            "previous_only_codes": len(before_codes - after_codes),
            "latest_only_codes": len(after_codes - before_codes),
            "changed_hour_coverage_codes": len(common - comparable),
            "previous_recorded_activity": before_totals.sum(),
            "latest_recorded_activity": after_totals.sum(),
            "previous_comparable_activity": old_total, "latest_comparable_activity": new_total,
            "absolute_change": new_total - old_total if comparable else float("nan"),
            "percent_change": (new_total - old_total) / old_total * 100 if old_total > 0 else float("nan"),
        })
    return (pd.DataFrame(movement_rows, columns=MOVEMENT_COLUMNS),
            pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS))


def main() -> None:
    data = pd.read_csv(DATA_PATH)
    movement, comparisons = build_monthly_comparisons(data)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    movement.to_csv(OUTPUT_DIR / "station_monthly_growth.csv", index=False)
    comparisons.to_csv(OUTPUT_DIR / "monthly_comparison_summary.csv", index=False)
    monthly_coverage(data).to_csv(OUTPUT_DIR / "monthly_coverage.csv", index=False)
    print(comparisons.to_string(index=False))
    print("Saved all consecutive month pairs, station movement and monthly coverage.")


if __name__ == "__main__":
    main()
