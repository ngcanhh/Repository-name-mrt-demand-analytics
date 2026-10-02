import json
import zipfile
from pathlib import Path

import requests


RESPONSE_PATH = Path("data/raw/lta_train_volume_response.json")
ZIP_PATH = Path("data/raw/lta_train_volume.zip")
EXTRACT_DIR = Path("data/raw/lta_train_volume")


def main() -> None:
    payload = json.loads(RESPONSE_PATH.read_text(encoding="utf-8"))
    records = payload.get("value", [])

    if not records:
        raise RuntimeError("The LTA API response did not contain a download link.")

    download_url = records[0]["Link"]
    print("Found LTA download link.")

    response = requests.get(download_url, timeout=120)
    response.raise_for_status()
    ZIP_PATH.write_bytes(response.content)
    print(f"Downloaded ZIP: {ZIP_PATH}")

    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as archive:
        archive.extractall(EXTRACT_DIR)
        print("Files in ZIP:")
        for name in archive.namelist():
            print(f"- {name}")

    print(f"Extracted to: {EXTRACT_DIR}")


if __name__ == "__main__":
    main()
