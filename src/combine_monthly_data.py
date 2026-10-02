from pathlib import Path

import pandas as pd


INPUT_FILES = [
    Path("data/raw/monthly/202607/transport_node_train_202607.csv"),
    Path("data/raw/lta_train_volume/transport_node_train_202608.csv"),
]
OUTPUT_PATH = Path("data/processed/mrt_station_demand_multi_month.csv")


def main() -> None:
    frames = []
    for path in INPUT_FILES:
        if not path.exists():
            raise FileNotFoundError(f"Missing input file: {path}")
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
