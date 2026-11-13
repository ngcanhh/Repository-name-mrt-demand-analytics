from contextlib import redirect_stdout
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd

from src import combine_monthly_data


class PipelineRetentionTests(unittest.TestCase):
    def test_raw_month_replaces_old_month_and_preserves_missing_archive(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "processed.csv"
            pd.DataFrame([
                {"year_month": "2026-08-01", "day_type": "weekday", "hour": 18,
                 "transport_type": "TRAIN", "station_code": "A", "tap_in_volume": 100,
                 "tap_out_volume": 50, "total_volume": 150, "hour_label": "18:00"},
                {"year_month": "2026-09-01", "day_type": "weekday", "hour": 18,
                 "transport_type": "TRAIN", "station_code": "A", "tap_in_volume": 200,
                 "tap_out_volume": 50, "total_volume": 250, "hour_label": "18:00"},
            ]).to_csv(output, index=False)
            pd.DataFrame([
                {"YEAR_MONTH": "2026-08", "DAY_TYPE": "WEEKDAY", "TIME_PER_HOUR": 18,
                 "PT_TYPE": "TRAIN", "PT_CODE": "A", "TOTAL_TAP_IN_VOLUME": 300,
                 "TOTAL_TAP_OUT_VOLUME": 50},
            ]).to_csv(root / "transport_node_train_202608.csv", index=False)
            with patch.object(combine_monthly_data, "RAW_ROOTS", [root]), \
                 patch.object(combine_monthly_data, "OUTPUT_PATH", output), redirect_stdout(io.StringIO()):
                combine_monthly_data.main()
            result = pd.read_csv(output)
            self.assertEqual(result.year_month.tolist(), ["2026-08-01", "2026-09-01"])
            self.assertEqual(result.total_volume.tolist(), [350, 250])

    def test_conflicting_raw_records_fail_before_overwriting_output(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = [{"YEAR_MONTH": "2026-08", "DAY_TYPE": "WEEKDAY", "TIME_PER_HOUR": 18,
                     "PT_TYPE": "TRAIN", "PT_CODE": "A", "TOTAL_TAP_IN_VOLUME": volume,
                     "TOTAL_TAP_OUT_VOLUME": 50} for volume in [100, 200]]
            pd.DataFrame(rows).to_csv(root / "transport_node_train_202608.csv", index=False)
            output = root / "processed.csv"
            with patch.object(combine_monthly_data, "RAW_ROOTS", [root]), \
                 patch.object(combine_monthly_data, "OUTPUT_PATH", output), redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "Conflicting"):
                    combine_monthly_data.main()
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
