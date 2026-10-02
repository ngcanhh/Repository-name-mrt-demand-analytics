from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

from download_lta_train_month import download_month


ROOT = Path(__file__).resolve().parents[1]


def previous_month() -> str:
    today = date.today()
    year, month = today.year, today.month - 1
    if month == 0:
        year, month = year - 1, 12
    return f"{year:04d}{month:02d}"


def run(script_name: str) -> None:
    subprocess.run([sys.executable, str(Path(__file__).with_name(script_name))], check=True)


def main() -> None:
    year_month = previous_month()
    target_dir = ROOT / "data" / "raw" / "monthly" / year_month
    target_files = list(target_dir.glob("transport_node_train_*.csv"))

    if target_files:
        print(f"Data for {year_month} already exists; rebuilding processed outputs.")
    else:
        print(f"Downloading LTA data for {year_month}...")
        try:
            download_month(year_month)
        except Exception as exc:
            # LTA may publish the previous month later than the scheduled run.
            # Keep the workflow green until a new month is available.
            print(f"No data available for {year_month}: {exc}")
            print("No update is needed yet; exiting successfully.")
            return

    run("combine_monthly_data.py")
    run("merge_multi_month_metadata.py")
    run("analyze_monthly_growth.py")
    print(f"Monthly pipeline completed for {year_month}.")


if __name__ == "__main__":
    main()
