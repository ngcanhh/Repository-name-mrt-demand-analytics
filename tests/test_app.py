"""Check the rendered app against source totals and exported comparisons."""

import base64
import json
import logging
from pathlib import Path
import unittest

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def values(array):
    if isinstance(array, dict):
        return np.frombuffer(base64.b64decode(array["bdata"]), dtype=array["dtype"])
    return np.asarray(array)


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.getLogger("streamlit").setLevel(logging.ERROR)
        cls.source = pd.read_csv(ROOT / "data/processed/mrt_station_demand_multi_month_enriched.csv")

    def app(self):
        return AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)

    def assert_chart_scope(self, app, source):
        self.assertFalse(app.exception)
        charts = [json.loads(chart.proto.spec) for chart in app.get("plotly_chart")]
        self.assertEqual(sum(values(trace["y"]).sum() for trace in charts[0]["data"]),
                         source.total_volume.sum())
        expected_top10 = source.groupby("station_name").total_volume.sum().nlargest(10).sum()
        self.assertEqual(sum(values(trace["x"]).sum() for trace in charts[1]["data"]), expected_top10)
        self.assertEqual(values(charts[2]["data"][0]["y"]).sum(), source.total_volume.sum())
        return charts

    def test_default_charts_use_all_months_and_growth_matches_export(self):
        app = self.app()
        self.assert_chart_scope(app, self.source)
        export = pd.read_csv(ROOT / "outputs/tables/monthly_comparison_summary.csv")
        table = app.dataframe[1].value
        self.assertEqual(len(table), len(export))
        self.assertEqual(table["From"].tolist(), export.previous_month.tolist())
        self.assertEqual(table["To"].tolist(), export.latest_month.tolist())
        self.assertEqual(table["Comparable codes"].tolist(), export.comparable_codes.tolist())
        np.testing.assert_allclose(table["Change (%)"], export.percent_change.round(2))
        self.assertEqual(app.selectbox[0].value,
                         f"{export.iloc[-1].previous_month} → {export.iloc[-1].latest_month}")
        app.selectbox[0].select(app.selectbox[0].options[0]).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Largest increases: 2026-06 → 2026-07" in x.value for x in app.markdown))

    def test_single_month_recalculates_charts_without_growth_or_forecast(self):
        app = self.app()
        app.sidebar.multiselect[0].set_value(["2026-09"]).run()
        charts = self.assert_chart_scope(app, self.source[self.source.year_month.eq("2026-09-01")])
        self.assertEqual(len(charts[2]["data"]), 1)
        self.assertEqual(len(app.selectbox), 0)
        self.assertTrue(any("two consecutive" in x.value for x in app.info))

    def test_gap_is_not_reported_as_month_over_month_growth(self):
        app = self.app()
        app.sidebar.multiselect[0].set_value(["2026-06", "2026-09"]).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.selectbox), 0)
        self.assertTrue(any("gap" in x.value for x in app.info))

    def test_line_and_weekend_filters_scope_charts_and_review(self):
        app = self.app()
        app.sidebar.multiselect[1].set_value(["East-West Line"])
        app.sidebar.multiselect[2].set_value(["weekends/holiday"]).run()
        source = self.source[self.source.line_name.eq("East-West Line")
                             & self.source.day_type.eq("weekends/holiday")]
        self.assert_chart_scope(app, source)
        review = app.dataframe[-1].value
        self.assertTrue(review["Peak day type"].eq("selected day types").all())

    def test_empty_selection_shows_message(self):
        app = self.app()
        app.sidebar.multiselect[0].set_value([]).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("No data" in x.value for x in app.warning))
        self.assertEqual(len(app.get("plotly_chart")), 0)


if __name__ == "__main__":
    unittest.main()
