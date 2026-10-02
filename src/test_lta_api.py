import os
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("LTA_ACCOUNT_KEY")
API_URL = "https://datamall2.mytransport.sg/ltaodataservice/PV/Train"
OUTPUT_PATH = Path("data/raw/lta_train_volume_response.json")


def main() -> None:
    if not API_KEY:
        raise RuntimeError("LTA_ACCOUNT_KEY was not found in .env")

    response = requests.get(
        API_URL,
        headers={
            "AccountKey": API_KEY,
            "accept": "application/json",
        },
        timeout=30,
    )

    print("HTTP status:", response.status_code)
    print("Response preview:", response.text[:500])

    if response.ok:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(response.text, encoding="utf-8")
        print(f"Saved response to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
