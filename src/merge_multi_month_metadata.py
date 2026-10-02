from pathlib import Path

import pandas as pd


DEMAND_PATH = Path("data/processed/mrt_station_demand_multi_month.csv")
STATION_PATH = Path(
    "data/reference/Train Station Codes and Chinese Names.xls"
)
OUTPUT_PATH = Path("data/processed/mrt_station_demand_multi_month_enriched.csv")


def main() -> None:
    demand = pd.read_csv(DEMAND_PATH)
    station = pd.read_excel(STATION_PATH)

    demand["station_code"] = (
        demand["station_code"].astype(str).str.strip().str.upper().str.replace(" ", "", regex=False)
    )
    station = station.rename(
        columns={
            "stn_code": "station_code",
            "mrt_station_english": "station_name",
            "mrt_line_english": "line_name",
        }
    )
    station = station[["station_code", "station_name", "line_name"]]
    station["station_code"] = (
        station["station_code"].astype(str).str.strip().str.upper().str.replace(" ", "", regex=False)
    )

    station["metadata_code"] = station["station_code"].str.split("/").str[0]
    station = station.drop_duplicates(subset=["metadata_code"])

    demand["metadata_code"] = demand["station_code"].str.split("/").str[0]
    enriched = demand.merge(
        station[["metadata_code", "station_name", "line_name"]],
        on="metadata_code",
        how="left",
    )

    line_by_prefix = {
        "BP": "Bukit Panjang LRT (inferred)",
        "CC": "Circle Line (inferred)",
        "CE": "Circle Line Extension (inferred)",
        "DT": "Downtown Line (inferred)",
        "EW": "East-West Line (inferred)",
        "NE": "North-East Line (inferred)",
        "NS": "North-South Line (inferred)",
        "TE": "Thomson-East Coast Line (inferred)",
        "SW": "Sengkang LRT (inferred)",
        "SE": "Sengkang LRT (inferred)",
        "PE": "Punggol LRT (inferred)",
        "PW": "Punggol LRT (inferred)",
    }
    prefix = enriched["metadata_code"].str.extract(r"^([A-Z]+)")[0]
    enriched["station_name"] = enriched["station_name"].fillna(
        "Unknown station " + enriched["station_code"]
    )
    enriched["line_name"] = enriched["line_name"].fillna(prefix.map(line_by_prefix))
    enriched = enriched.drop(columns=["metadata_code"])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(OUTPUT_PATH, index=False)
    print(f"Rows: {len(enriched)}")
    print(f"Months: {enriched['year_month'].nunique()}")
    print(f"Stations: {enriched['station_code'].nunique()}")
    print("All station rows have names:", enriched["station_name"].notna().all())
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
