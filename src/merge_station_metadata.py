from pathlib import Path

import pandas as pd


DEMAND_PATH = Path("data/processed/mrt_station_demand_202608.csv")
STATION_PATH = Path(
    "data/reference/Train Station Codes and Chinese Names.xls"
)
OUTPUT_PATH = Path("data/processed/mrt_station_demand_enriched_202608.csv")


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

    # Keep original interchange codes and also create aliases for each
    # individual code, e.g. BP6/DT1 -> BP6 and DT1.
    aliases = station.assign(station_code=station["station_code"].str.split("/")).explode(
        "station_code"
    )
    aliases["station_code"] = aliases["station_code"].str.strip().str.upper()
    station = pd.concat([station, aliases], ignore_index=True)
    station = station.drop_duplicates(subset=["station_code"])

    # Demand data may store an interchange as BP6/DT1 while the reference
    # file stores the individual station codes. Use the first code only for
    # the metadata lookup and preserve the original demand code.
    demand["metadata_code"] = demand["station_code"].str.split("/").str[0]
    enriched = demand.merge(
        station.rename(columns={"station_code": "metadata_code"}),
        on="metadata_code",
        how="left",
    )

    # A few newer stations may not exist in the older reference file.
    # Preserve them with an explicit inferred line label instead of dropping
    # their demand records.
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

    unmatched = enriched[enriched["station_name"].isna()]["station_code"].unique()
    if len(unmatched) > 0:
        print("Unmatched station codes:", unmatched.tolist())
    else:
        print("All station codes matched successfully.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    enriched = enriched.drop(columns=["metadata_code"])
    enriched.to_csv(OUTPUT_PATH, index=False)

    print(f"Rows: {len(enriched)}")
    print(f"Stations: {enriched['station_code'].nunique()}")
    print(f"Lines: {enriched['line_name'].nunique()}")
    print(f"Saved to: {OUTPUT_PATH}")
    print("\nSample enriched rows:")
    print(
        enriched[
            ["station_code", "station_name", "line_name", "hour", "day_type", "total_volume"]
        ]
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
