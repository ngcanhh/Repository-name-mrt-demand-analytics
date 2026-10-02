from pathlib import Path

import pandas as pd
import requests


DATASET_ID = "d_75248cf2fbf340de6a746dc91ec9223c"
API_URL = "https://api-open.data.gov.sg/v1/public/api/datasets/{}/poll-download"
OUTPUT_PATH = Path("data/raw/public_transport_ridership.csv")


def download_dataset() -> None:
    """Download the public transport ridership dataset from data.gov.sg."""
    response = requests.get(API_URL.format(DATASET_ID), timeout=30)
    response.raise_for_status()

    payload = response.json()
    if payload.get("code") != 0:
        raise RuntimeError(payload.get("errMsg", "Unknown data.gov.sg error"))

    download_url = payload["data"]["url"]
    csv_response = requests.get(download_url, timeout=30)
    csv_response.raise_for_status()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(csv_response.content)

    data = pd.read_csv(OUTPUT_PATH)
    print(f"Downloaded {len(data)} rows.")
    print(f"Saved to: {OUTPUT_PATH}")
    print("Columns:", list(data.columns))


if __name__ == "__main__":
    download_dataset()
