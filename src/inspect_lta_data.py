from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/raw/lta_train_volume/transport_node_train_202608.csv")


def main() -> None:
    data = pd.read_csv(DATA_PATH)

    print("--- SHAPE ---")
    print(f"Rows: {data.shape[0]}")
    print(f"Columns: {data.shape[1]}")

    print("\n--- COLUMNS ---")
    print(data.columns.tolist())

    print("\n--- FIRST 10 ROWS ---")
    print(data.head(10).to_string(index=False))

    print("\n--- DATA TYPES ---")
    print(data.dtypes)

    print("\n--- MISSING VALUES ---")
    print(data.isna().sum())

    print("\n--- BASIC NUMERIC SUMMARY ---")
    print(data.describe(include="all").transpose().to_string())


if __name__ == "__main__":
    main()
