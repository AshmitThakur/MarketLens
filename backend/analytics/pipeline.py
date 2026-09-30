"""Command-line entry point for the MarketLens analytics pipeline."""

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .loader import build_validation_summary, load_data
from .metrics import calculate_city_metrics
from .scoring import DEFAULT_WEIGHTS, score_city_metrics


OUTPUT_COLUMNS = [
    "city",
    "state",
    "active_stores",
    "total_sales",
    "sales_per_store",
    "total_transactions",
    "transactions_per_store",
    "comparable_growth_pct",
    "category_breadth",
    "sales_score",
    "transaction_score",
    "growth_score",
    "breadth_score",
    "opportunity_score",
]


def run_pipeline(
    raw_dir: str | Path,
    output_path: str | Path,
    weights: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run loading, metric calculation, scoring, validation, and CSV export."""
    train, stores, transactions = load_data(raw_dir)
    metrics, growth = calculate_city_metrics(train, stores, transactions)
    scored = score_city_metrics(metrics, weights=weights)[OUTPUT_COLUMNS]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(output_path, index=False)

    summary = build_validation_summary(
        train, stores, transactions, growth.comparable_store_count
    )
    summary["growth_windows"] = {
        "previous": [
            growth.previous_start.date().isoformat(),
            growth.previous_end.date().isoformat(),
        ],
        "current": [
            growth.current_start.date().isoformat(),
            growth.current_end.date().isoformat(),
        ],
    }
    metadata_path = output_path.with_name("analysis_metadata.json")
    metadata_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return scored, summary


def _build_parser() -> argparse.ArgumentParser:
    project_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Build MarketLens city metrics")
    parser.add_argument("--raw-dir", type=Path, default=project_root / "data" / "raw")
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "data" / "processed" / "city_metrics.csv",
    )
    parser.add_argument("--sales-weight", type=float, default=DEFAULT_WEIGHTS["sales"])
    parser.add_argument(
        "--transaction-weight", type=float, default=DEFAULT_WEIGHTS["transactions"]
    )
    parser.add_argument("--growth-weight", type=float, default=DEFAULT_WEIGHTS["growth"])
    parser.add_argument("--breadth-weight", type=float, default=DEFAULT_WEIGHTS["breadth"])
    return parser


def main() -> None:
    """Run the CLI and print validation details plus the top ten cities."""
    args = _build_parser().parse_args()
    weights = {
        "sales": args.sales_weight,
        "transactions": args.transaction_weight,
        "growth": args.growth_weight,
        "breadth": args.breadth_weight,
    }
    scored, summary = run_pipeline(args.raw_dir, args.output, weights=weights)
    print("Validation summary:")
    print(json.dumps(summary, indent=2))
    print("\nTop 10 cities by Expansion Opportunity Score:")
    print(scored.head(10).to_string(index=False))
    print(f"\nSaved {len(scored)} rows to {args.output}")


if __name__ == "__main__":
    main()
