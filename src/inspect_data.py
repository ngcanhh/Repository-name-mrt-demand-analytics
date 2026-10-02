from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/raw/public_transport_ridership.csv")


def inspect_data() -> None:
    data = pd.read_csv(DATA_PATH)

    print("\n--- SHAPE ---")
    print(f"Rows: {data.shape[0]}")
    print(f"Columns: {data.shape[1]}")

    print("\n--- COLUMNS ---")
    print(data.columns.tolist())

    print("\n--- FIRST 5 ROWS ---")
    print(data.head().to_string(index=False))

    print("\n--- DATA TYPES ---")
    print(data.dtypes)

    print("\n--- MISSING VALUES ---")
    print(data.isna().sum())

    print("\n--- UNIQUE VALUES ---")
    for column in data.columns:
        if data[column].nunique() <= 20:
            print(f"{column}: {data[column].dropna().unique().tolist()}")


if __name__ == "__main__":
    inspect_data()
