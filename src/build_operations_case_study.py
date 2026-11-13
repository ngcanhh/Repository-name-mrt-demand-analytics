"""Rebuild the four-month review evidence and its static overview figure."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

try:
    from .analyze_monthly_growth import build_monthly_comparisons, monthly_coverage
    from .operations_review import build_review_priorities, hourly_activity, station_activity
except ImportError:
    from analyze_monthly_growth import build_monthly_comparisons, monthly_coverage
    from operations_review import build_review_priorities, hourly_activity, station_activity

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data = pd.read_csv(ROOT / "data/processed/mrt_station_demand_multi_month_enriched.csv")
    tables, figures = ROOT / "outputs/tables", ROOT / "outputs/figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    priorities = build_review_priorities(data)
    hourly = hourly_activity(data)
    stations = station_activity(data)
    coverage = monthly_coverage(data)
    _, comparisons = build_monthly_comparisons(data)
    priorities.to_csv(tables / "operations_review_priorities.csv", index=False)
    hourly.to_csv(tables / "multi_month_hourly_summary.csv", index=False)
    stations.to_csv(tables / "multi_month_station_summary.csv", index=False)

    months = sorted(pd.to_datetime(data["year_month"]).dt.strftime("%Y-%m").unique())
    period = f"{months[0]} to {months[-1]}"
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), layout="constrained")
    fig.suptitle(f"Singapore MRT/LRT activity | {period}", fontsize=20, fontweight="bold")
    for day_type, group in hourly.groupby("day_type"):
        axes[0, 0].plot(group["hour"], group["total_volume"], marker=".", label=day_type)
    axes[0, 0].set(title="Hourly activity summed across all months", xlabel="Hour", ylabel="Recorded activity")
    axes[0, 0].legend(frameon=False)
    axes[0, 0].yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1e6:.0f}M"))
    top = stations.head(10).iloc[::-1]
    axes[0, 1].barh(top["station_name"], top["total_volume"], color="#1674b9")
    axes[0, 1].set(title="Top 10 by activity across all months", xlabel="Recorded activity")
    axes[0, 1].xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1e6:.0f}M"))
    axes[1, 0].plot(coverage["month_label"], coverage["recorded_activity"], marker="o", color="#1674b9")
    for row in coverage.itertuples():
        axes[1, 0].annotate(f"{row.station_codes} codes", (row.month_label, row.recorded_activity),
                            xytext=(0, 10), textcoords="offset points", ha="center")
    axes[1, 0].set(title="Recorded monthly totals and source coverage", xlabel="Month", ylabel="Recorded activity")
    axes[1, 0].margins(y=0.25)
    axes[1, 0].yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1e6:.0f}M"))
    labels = [f"{r.previous_month}\n→ {r.latest_month}" for r in comparisons.itertuples()]
    colors = ["#1b9166" if value >= 0 else "#cb6048" for value in comparisons["percent_change"]]
    axes[1, 1].bar(labels, comparisons["percent_change"], color=colors)
    for label, row in zip(labels, comparisons.itertuples()):
        axes[1, 1].annotate(f"{row.percent_change:+.2f}%\n{row.comparable_codes} comparable codes",
                            (label, row.percent_change), xytext=(0, 7 if row.percent_change >= 0 else -7),
                            textcoords="offset points", ha="center", va="bottom" if row.percent_change >= 0 else "top")
    axes[1, 1].axhline(0, color="#999999", linewidth=0.8)
    axes[1, 1].set(title="Growth on matching codes and hour/day-type cells", ylabel="Change (%)")
    axes[1, 1].margins(y=0.35)
    fig.supxlabel("Activity = tap-ins + tap-outs, not unique passengers. Monthly totals are not adjusted for day counts.", fontsize=10)
    fig.savefig(figures / "operations_case_study.png", dpi=160)
    plt.close(fig)
    print(priorities.to_string(index=False))
    print("Total activity:", int(data["total_volume"].sum()))
    print("Top 3 share (%):", stations.head(3)["total_volume"].sum() / data["total_volume"].sum() * 100)
    print("Top 5 share (%):", priorities["activity_share_pct"].sum())
    print("Hourly peaks by month and day type:")
    per_month = (data.groupby(["year_month", "day_type", "hour"], as_index=False)["total_volume"].sum())
    print(per_month.loc[per_month.groupby(["year_month", "day_type"])["total_volume"].idxmax()].to_string(index=False))


if __name__ == "__main__":
    main()
