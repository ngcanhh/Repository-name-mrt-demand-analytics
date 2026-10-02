from pathlib import Path

import pandas as pd


REFERENCE_DIR = Path("data/raw/reference")
STATION_PATH = REFERENCE_DIR / "station_codes/Train Station Codes and Chinese Names.xls"
LINE_PATH = REFERENCE_DIR / "Train Line Codes.xlsx"


def inspect_file(path):
    print(f"\n--- FILE: {path.name} ---")
    print("Sheets:", pd.ExcelFile(path).sheet_names)

    data = pd.read_excel(path)
    print("Shape:", data.shape)
    print("Columns:", data.columns.tolist())
    print("\nFirst 5 rows:")
    print(data.head().to_string(index=False))


if __name__ == "__main__":
    inspect_file(STATION_PATH)
    inspect_file(LINE_PATH)