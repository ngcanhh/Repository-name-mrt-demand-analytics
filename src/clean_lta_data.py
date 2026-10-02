from pathlib import Path

import pandas as pd


RAW_PATH = Path("data/raw/lta_train_volume/transport_node_train_202608.csv")
PROCESSED_PATH = Path("data/processed/mrt_station_demand_202608.csv")


def main() -> None:
    data = pd.read_csv(RAW_PATH)

    data.columns = data.columns.str.strip().str.lower()
    data = data.rename(
        columns={
            "year_month": "year_month",
            "day_type": "day_type",
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
    data["hour"] = data["hour"].astype(int)
    data["tap_in_volume"] = data["tap_in_volume"].astype(int)
    data["tap_out_volume"] = data["tap_out_volume"].astype(int)
    data["total_volume"] = data["tap_in_volume"] + data["tap_out_volume"]
    data["hour_label"] = data["hour"].astype(str).str.zfill(2) + ":00"

    data = data.sort_values(["station_code", "day_type", "hour"])
    data = data.drop_duplicates()

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(PROCESSED_PATH, index=False)

    print(f"Processed rows: {len(data)}")
    print(f"Stations: {data['station_code'].nunique()}")
    print(f"Saved to: {PROCESSED_PATH}")
    print("\nRows by day type:")
    print(data["day_type"].value_counts().to_string())


if __name__ == "__main__":
    main()
