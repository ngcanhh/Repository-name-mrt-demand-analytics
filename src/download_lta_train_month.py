import argparse
import json
import os
import zipfile
from pathlib import Path

import requests
from dotenv import load_dotenv


API_URL = "https://datamall2.mytransport.sg/ltaodataservice/PV/Train"
RAW_DIR = Path("data/raw/monthly")


def download_month(year_month: str) -> None:
    load_dotenv()
    api_key = os.getenv("LTA_ACCOUNT_KEY")
    if not api_key:
        raise RuntimeError("LTA_ACCOUNT_KEY was not found in .env")

    response = requests.get(
        API_URL,
        params={"Date": year_month},
        headers={"AccountKey": api_key, "accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    records = payload.get("value", [])
    if not records:
        raise RuntimeError(f"No download link returned for {year_month}: {payload}")

    zip_path = RAW_DIR / f"transport_node_train_{year_month}.zip"
    extract_dir = RAW_DIR / year_month
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    download_url = records[0]["Link"]
    file_response = requests.get(download_url, timeout=120)
    file_response.raise_for_status()
    zip_path.write_bytes(file_response.content)

    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(extract_dir)

    print(f"Downloaded and extracted: {year_month}")
    print(f"Location: {extract_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("year_month", help="Month in YYYYMM format, e.g. 202609")
    args = parser.parse_args()
    download_month(args.year_month)
