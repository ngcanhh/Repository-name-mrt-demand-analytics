from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


DATA_PATH = Path("data/processed/mrt_station_demand_enriched_202608.csv")
TABLE_DIR = Path("outputs/tables")
FIGURE_DIR = Path("outputs/figures")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    data = pd.read_csv(DATA_PATH)
    hourly = pd.read_csv(TABLE_DIR / "hourly_summary.csv")
    stations = pd.read_csv(TABLE_DIR / "station_summary.csv").head(10)
    lines = pd.read_csv(TABLE_DIR / "line_summary.csv")

    plt.figure(figsize=(11, 6))
    sns.lineplot(
        data=hourly,
        x="hour",
        y="total_volume",
        hue="day_type",
        marker="o",
    )
    plt.title("Singapore MRT Activity by Hour - August 2026")
    plt.xlabel("Hour of day")
    plt.ylabel("Tap-in + tap-out activity")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "hourly_demand_by_day_type.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=stations.sort_values("total_volume"),
        x="total_volume",
        y="station_name",
        hue="line_name",
        dodge=False,
        legend=False,
    )
    plt.title("Top 10 MRT Stations by Activity - August 2026")
    plt.xlabel("Tap-in + tap-out activity")
    plt.ylabel("Station")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "top_10_stations.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=lines.sort_values("total_volume"),
        x="total_volume",
        y="line_name",
        color="#2f6f9f",
    )
    plt.title("MRT Activity by Line - August 2026")
    plt.xlabel("Tap-in + tap-out activity")
    plt.ylabel("Line")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "activity_by_line.png", dpi=160)
    plt.close()

    print(f"Saved charts to: {FIGURE_DIR}")
    for path in sorted(FIGURE_DIR.glob("*.png")):
        print(f"- {path.name}")


if __name__ == "__main__":
    main()
