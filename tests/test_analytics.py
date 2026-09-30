"""Focused tests for MarketLens business rules."""

import unittest
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from backend.analytics.metrics import (
    calculate_activity_metrics,
    calculate_category_breadth,
    calculate_comparable_growth,
)
from backend.analytics.pipeline import OUTPUT_COLUMNS, run_pipeline
from backend.analytics.scoring import percentile_score, score_city_metrics


class AnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stores = pd.DataFrame(
            {
                "store_nbr": [1, 2, 3],
                "city": ["Alpha", "Alpha", "Beta"],
                "state": ["North", "North", "South"],
                "type": ["A", "A", "B"],
                "cluster": [1, 1, 2],
            }
        )

    def test_growth_excludes_store_without_prior_period_sales(self) -> None:
        train = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2021-01-02",
                        "2023-01-01",
                        "2023-01-01",
                        "2021-01-02",
                        "2023-01-01",
                    ]
                ),
                "store_nbr": [1, 1, 2, 3, 3],
                "sales": [100.0, 120.0, 500.0, 200.0, 180.0],
            }
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = calculate_comparable_growth(train, self.stores)

        self.assertEqual(result.comparable_store_count, 2)
        growth = result.city_growth.set_index("city")["comparable_growth_pct"]
        self.assertAlmostEqual(growth["Alpha"], 20.0)
        self.assertAlmostEqual(growth["Beta"], -10.0)

    def test_category_breadth_uses_one_percent_city_share(self) -> None:
        train = pd.DataFrame(
            {
                "date": pd.to_datetime(["2023-01-01"] * 3),
                "store_nbr": [1, 1, 1],
                "family": ["A", "B", "C"],
                "sales": [980.0, 10.0, 10.0],
            }
        )
        result = calculate_category_breadth(
            train,
            self.stores,
            current_start=pd.Timestamp("2023-01-01"),
            current_end=pd.Timestamp("2023-12-31"),
        )
        self.assertEqual(result.loc[0, "category_breadth"], 3)

    def test_activity_metrics_use_only_current_period(self) -> None:
        train = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2022-12-31", "2023-01-01", "2023-12-31"]
                ),
                "store_nbr": [2, 1, 1],
                "sales": [1000.0, 40.0, 60.0],
            }
        )
        transactions = pd.DataFrame(
            {
                "date": pd.to_datetime(["2022-12-31", "2023-06-01"]),
                "store_nbr": [2, 1],
                "transactions": [500, 25],
            }
        )

        result = calculate_activity_metrics(
            train,
            self.stores,
            transactions,
            current_start=pd.Timestamp("2023-01-01"),
            current_end=pd.Timestamp("2023-12-31"),
        )

        alpha = result.loc[result["city"] == "Alpha"].iloc[0]
        self.assertEqual(alpha["active_stores"], 1)
        self.assertEqual(alpha["total_sales"], 100.0)
        self.assertEqual(alpha["sales_per_store"], 100.0)
        self.assertEqual(alpha["total_transactions"], 25)
        self.assertEqual(alpha["transactions_per_store"], 25)

    def test_percentile_score_spans_zero_to_one_hundred(self) -> None:
        result = percentile_score(pd.Series([10.0, 20.0, 30.0]))
        self.assertEqual(result.tolist(), [0.0, 50.0, 100.0])

    def test_percentile_score_assigns_neutral_score_when_all_values_tie(self) -> None:
        result = percentile_score(pd.Series([10.0, 10.0]))
        self.assertEqual(result.tolist(), [50.0, 50.0])

    def test_missing_component_keeps_opportunity_score_missing(self) -> None:
        metrics = pd.DataFrame(
            {
                "sales_per_store": [1.0, 2.0],
                "transactions_per_store": [1.0, 2.0],
                "comparable_growth_pct": [np.nan, 2.0],
                "category_breadth": [1, 2],
            }
        )
        result = score_city_metrics(metrics)
        missing_row = result.loc[result["sales_per_store"] == 1.0].iloc[0]
        self.assertTrue(np.isnan(missing_row["opportunity_score"]))

    def test_weights_must_sum_to_one(self) -> None:
        metrics = pd.DataFrame(
            {
                "sales_per_store": [1.0],
                "transactions_per_store": [1.0],
                "comparable_growth_pct": [1.0],
                "category_breadth": [1],
            }
        )
        with self.assertRaisesRegex(ValueError, "sum to 1.0"):
            score_city_metrics(
                metrics,
                weights={"sales": 1, "transactions": 1, "growth": 1, "breadth": 1},
            )

    def test_pipeline_exports_expected_city_dataset(self) -> None:
        train = pd.DataFrame(
            {
                "date": [
                    "2022-01-01",
                    "2023-01-01",
                    "2023-12-31",
                    "2022-01-01",
                    "2023-01-01",
                    "2023-12-31",
                ],
                "store_nbr": [1, 1, 1, 3, 3, 3],
                "family": ["A", "A", "A", "B", "B", "B"],
                "sales": [100.0, 120.0, 0.0, 100.0, 80.0, 0.0],
                "onpromotion": [0, 0, 0, 0, 0, 0],
            }
        )
        stores = self.stores.loc[self.stores["store_nbr"].isin([1, 3])]
        transactions = pd.DataFrame(
            {
                "date": ["2022-01-01", "2023-01-01"] * 2,
                "store_nbr": [1, 1, 3, 3],
                "transactions": [50, 60, 50, 40],
            }
        )

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            raw = root / "raw"
            raw.mkdir()
            train.to_csv(raw / "train.csv", index=False)
            stores.to_csv(raw / "stores.csv", index=False)
            transactions.to_csv(raw / "transactions.csv", index=False)
            output = root / "processed" / "city_metrics.csv"

            result, summary = run_pipeline(raw, output)

            self.assertTrue(output.is_file())
            self.assertTrue((output.parent / "analysis_metadata.json").is_file())
            self.assertEqual(result.columns.tolist(), OUTPUT_COLUMNS)
            self.assertEqual(result["city"].tolist(), ["Alpha", "Beta"])
            self.assertEqual(summary["comparable_stores"], 2)


if __name__ == "__main__":
    unittest.main()
