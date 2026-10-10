import unittest
from pathlib import Path

import pandas as pd

from src.forecast_monthly_activity import build_forecast


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/processed/mrt_station_demand_multi_month_enriched.csv"


class AnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv(DATA_PATH)

    def test_total_volume_invariant(self):
        expected = self.data["tap_in_volume"] + self.data["tap_out_volume"]
        pd.testing.assert_series_equal(
            self.data["total_volume"], expected, check_names=False
        )

    def test_no_negative_volumes(self):
        self.assertTrue((self.data[["tap_in_volume", "tap_out_volume", "total_volume"]] >= 0).all().all())

    def test_forecast_adds_one_future_month(self):
        result = build_forecast(self.data)
        self.assertEqual(len(result), self.data["year_month"].nunique() + 1)
        self.assertEqual(result.iloc[-1]["record_type"], "baseline_forecast")
        self.assertGreaterEqual(result.iloc[-1]["activity"], 0)


if __name__ == "__main__":
    unittest.main()
