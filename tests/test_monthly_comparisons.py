import unittest

import pandas as pd

from src.analyze_monthly_growth import build_monthly_comparisons, monthly_coverage
from src.operations_review import build_review_priorities, hourly_activity, station_activity


def record(month, code, activity, hour=18, day_type="weekday", name=None):
    return {"year_month": f"2026-{month:02d}-01", "station_code": code,
            "station_name": name or code, "line_name": "Test Line", "hour": hour,
            "day_type": day_type, "total_volume": activity}


class MonthlyComparisonTests(unittest.TestCase):
    def test_four_months_produce_three_consecutive_pairs(self):
        data = pd.DataFrame([record(month, "A", volume) for month, volume in
                             [(6, 100), (7, 120), (8, 90), (9, 99)]])
        movement, summary = build_monthly_comparisons(data)
        self.assertEqual(list(zip(summary.previous_month, summary.latest_month)),
                         [("2026-06", "2026-07"), ("2026-07", "2026-08"), ("2026-08", "2026-09")])
        self.assertEqual(movement.absolute_change.tolist(), [20, -30, 9])
        self.assertAlmostEqual(summary.iloc[-1].percent_change, 10)

    def test_missing_station_does_not_become_a_decline(self):
        data = pd.DataFrame([record(8, "A", 100), record(8, "B", 100), record(9, "A", 100)])
        movement, summary = build_monthly_comparisons(data)
        self.assertEqual(summary.iloc[0].percent_change, 0)
        self.assertEqual(summary.iloc[0].previous_recorded_activity, 200)
        self.assertEqual(summary.iloc[0].previous_comparable_activity, 100)
        missing = movement[movement.station_code.eq("B")].iloc[0]
        self.assertEqual(missing.growth_quality, "missing_latest_month")
        self.assertTrue(pd.isna(missing.percent_change))
        self.assertTrue(pd.isna(missing.absolute_change))

    def test_same_code_count_does_not_imply_same_cohort(self):
        data = pd.DataFrame([record(8, "A", 100), record(8, "B", 200),
                             record(9, "A", 110), record(9, "C", 500)])
        _, summary = build_monthly_comparisons(data)
        row = summary.iloc[0]
        self.assertEqual((row.previous_codes, row.latest_codes, row.comparable_codes), (2, 2, 1))
        self.assertAlmostEqual(row.percent_change, 10)

    def test_changed_hour_or_day_type_coverage_is_excluded(self):
        for changed in [record(9, "B", 50, hour=19), record(9, "B", 50, day_type="weekends/holiday")]:
            with self.subTest(changed=changed):
                data = pd.DataFrame([record(8, "A", 100), record(9, "A", 110),
                                     record(8, "B", 100), changed])
                movement, summary = build_monthly_comparisons(data)
                self.assertEqual(summary.iloc[0].changed_hour_coverage_codes, 1)
                self.assertAlmostEqual(summary.iloc[0].percent_change, 10)
                self.assertTrue(movement.loc[movement.station_code.eq("B"), "percent_change"].isna().all())

    def test_zero_baseline_has_no_percentage_but_zero_latest_is_valid(self):
        data = pd.DataFrame([record(8, "A", 0), record(9, "A", 20),
                             record(8, "B", 100), record(9, "B", 0)])
        movement, summary = build_monthly_comparisons(data)
        rows = movement.set_index("station_code")
        self.assertEqual(rows.loc["A", "growth_quality"], "zero_baseline")
        self.assertTrue(pd.isna(rows.loc["A", "percent_change"]))
        self.assertEqual(rows.loc["B", "percent_change"], -100)
        self.assertEqual(summary.iloc[0].percent_change, -80)

    def test_metadata_change_preserves_code_identity(self):
        data = pd.DataFrame([record(8, "A", 100, name="Old"), record(9, "A", 120, name="New")])
        movement, summary = build_monthly_comparisons(data)
        self.assertEqual(movement.iloc[0].station_name, "New")
        self.assertAlmostEqual(summary.iloc[0].percent_change, 20)

    def test_gaps_and_single_month_do_not_produce_monthly_growth(self):
        for data in [pd.DataFrame([record(6, "A", 100), record(9, "A", 200)]),
                     pd.DataFrame([record(6, "A", 100)])]:
            movement, summary = build_monthly_comparisons(data)
            self.assertTrue(movement.empty)
            self.assertTrue(summary.empty)
            self.assertIn("percent_change", summary.columns)

    def test_duplicate_cells_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_monthly_comparisons(pd.DataFrame([record(8, "A", 100), record(8, "A", 110)]))

    def test_no_common_codes_does_not_report_zero_percent_change(self):
        _, summary = build_monthly_comparisons(pd.DataFrame([record(8, "A", 100), record(9, "B", 100)]))
        self.assertEqual(summary.iloc[0].comparable_codes, 0)
        self.assertTrue(pd.isna(summary.iloc[0].percent_change))

    def test_all_months_contribute_to_charts_and_review(self):
        data = pd.DataFrame([record(month, "A", 100, name="Alpha") for month in [6, 7, 8, 9]]
                            + [record(9, "B", 50, name="Alpha")])
        self.assertEqual(hourly_activity(data).total_volume.sum(), 450)
        stations = station_activity(data)
        self.assertEqual(len(stations), 1)
        self.assertEqual(stations.iloc[0].total_volume, 450)
        priorities = build_review_priorities(data)
        self.assertEqual(priorities.iloc[0].months_observed, 4)
        self.assertEqual(priorities.iloc[0].peak_hour, 18)
        self.assertEqual(monthly_coverage(data).station_codes.tolist(), [1, 1, 1, 2])
        self.assertEqual(hourly_activity(data[data.year_month.eq("2026-09-01")]).total_volume.sum(), 150)

    def test_selected_day_type_changes_comparison_scope(self):
        data = pd.DataFrame([record(8, "A", 100), record(9, "A", 110),
                             record(8, "A", 900, day_type="weekends/holiday"),
                             record(9, "A", 900, day_type="weekends/holiday")])
        _, summary = build_monthly_comparisons(data[data.day_type.eq("weekday")])
        self.assertAlmostEqual(summary.iloc[0].percent_change, 10)
        self.assertEqual(summary.iloc[0].previous_comparable_activity, 100)


if __name__ == "__main__":
    unittest.main()
