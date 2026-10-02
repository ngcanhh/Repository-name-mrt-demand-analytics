from pathlib import Path

import pandas as pd


RAW_ROOTS = [
    Path("data/raw/monthly"),
    Path("data/raw/lta_train_volume"),
]
OUTPUT_PATH = Path("data/processed/mrt_station_demand_multi_month.csv")


def discover_input_files() -> list[Path]:
    """Find every downloaded monthly LTA CSV without hard-coding month names."""
    files = set()
    for root in RAW_ROOTS:
        if root.exists():
            files.update(root.rglob("transport_node_train_*.csv"))
    return sorted(files)


def main() -> None:
    input_files = discover_input_files()
    if not input_files:
        raise FileNotFoundError(
            "No monthly LTA CSV files found under data/raw/monthly or "
            "data/raw/lta_train_volume"
        )

    frames = []
    for path in input_files:
        frame = pd.read_csv(path)
        frames.append(frame)
        print(f"Loaded {path.name}: {len(frame)} rows")

    data = pd.concat(frames, ignore_index=True)
    data.columns = data.columns.str.strip().str.lower()
    data = data.rename(
        columns={
            "time_per_hour": "hour",
            "pt_type": "transport_type",
            "pt_code": "station_code",
            "total_tap_in_volume": "tap_in_volume",
            "total_tap_out_volume": "tap_out_volume",
        }
    )
    data["year_month"] = pd.to_datetime(data["year_month"], format="%Y-%m")
    data["day_type"] = data["day_type"].str.strip().str.lower()
    data["station_code"] = data["station_code"].str.strip().str.upper()
    data["total_volume"] = data["tap_in_volume"] + data["tap_out_volume"]
    data["hour_label"] = data["hour"].astype(str).str.zfill(2) + ":00"
    data = data.drop_duplicates()
    data = data.sort_values(["year_month", "station_code", "day_type", "hour"])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUTPUT_PATH, index=False)

    print(f"Combined rows: {len(data)}")
    print("Months:", data["year_month"].dt.strftime("%Y-%m").unique().tolist())
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
