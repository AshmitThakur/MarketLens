"""Calculate transparent city-level retail activity metrics."""

from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class GrowthResult:
    """Comparable-store city growth plus audit information."""

    city_growth: pd.DataFrame
    comparable_store_count: int
    current_start: pd.Timestamp
    current_end: pd.Timestamp
    previous_start: pd.Timestamp
    previous_end: pd.Timestamp


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide while converting zero denominators to missing values."""
    return numerator.div(denominator.replace(0, np.nan))


def add_store_locations(frame: pd.DataFrame, stores: pd.DataFrame) -> pd.DataFrame:
    """Attach city/state to fact rows using the store dimension."""
    return frame.merge(
        stores[["store_nbr", "city", "state"]],
        on="store_nbr",
        how="left",
        validate="many_to_one",
    )


def calculate_activity_metrics(
    train: pd.DataFrame,
    stores: pd.DataFrame,
    transactions: pd.DataFrame,
    current_start: pd.Timestamp,
    current_end: pd.Timestamp,
) -> pd.DataFrame:
    """Calculate current-period sales and transactions per active store by city."""
    current_sales = train.loc[train["date"].between(current_start, current_end)]
    current_transactions = transactions.loc[
        transactions["date"].between(current_start, current_end)
    ]
    sales = add_store_locations(current_sales, stores)
    transaction_facts = add_store_locations(current_transactions, stores)

    city_sales = (
        sales.groupby(["city", "state"], as_index=False)
        .agg(active_stores=("store_nbr", "nunique"), total_sales=("sales", "sum"))
    )
    city_sales["sales_per_store"] = _safe_divide(
        city_sales["total_sales"], city_sales["active_stores"]
    )

    city_transactions = (
        transaction_facts.groupby(["city", "state"], as_index=False)
        .agg(total_transactions=("transactions", "sum"))
    )
    result = city_sales.merge(city_transactions, on=["city", "state"], how="left")
    missing_city_transactions = result["total_transactions"].isna()
    if missing_city_transactions.any():
        cities = result.loc[missing_city_transactions, "city"].tolist()
        warnings.warn(
            f"No transaction records are available for {len(cities)} cities: {cities[:10]}. "
            "Transaction metrics will remain missing.",
            stacklevel=2,
        )
    result["transactions_per_store"] = _safe_divide(
        result["total_transactions"], result["active_stores"]
    )
    return result


def calculate_comparable_growth(
    train: pd.DataFrame, stores: pd.DataFrame, period_days: int = 365
) -> GrowthResult:
    """Calculate city sales growth using stores with positive sales in both periods."""
    if period_days <= 0:
        raise ValueError("period_days must be positive")

    current_end = train["date"].max().normalize()
    current_start = current_end - pd.Timedelta(period_days - 1, unit="D")
    previous_end = current_start - pd.Timedelta(1, unit="D")
    previous_start = previous_end - pd.Timedelta(period_days - 1, unit="D")

    if train["date"].min().normalize() > previous_start:
        warnings.warn(
            "The dataset does not cover the complete preceding growth period; "
            "no city growth scores will be calculated.",
            stacklevel=2,
        )
        empty_growth = pd.DataFrame(
            columns=["city", "state", "comparable_growth_pct"]
        )
        return GrowthResult(
            city_growth=empty_growth,
            comparable_store_count=0,
            current_start=current_start,
            current_end=current_end,
            previous_start=previous_start,
            previous_end=previous_end,
        )

    relevant = train.loc[
        train["date"].between(previous_start, current_end),
        ["date", "store_nbr", "sales"],
    ].copy()
    relevant["period"] = np.where(
        relevant["date"].between(current_start, current_end), "current", "previous"
    )
    store_period_sales = relevant.pivot_table(
        index="store_nbr", columns="period", values="sales", aggfunc="sum", fill_value=0
    )
    for required_period in ("current", "previous"):
        if required_period not in store_period_sales:
            store_period_sales[required_period] = 0.0

    # Positive sales in each window is a simple, observable definition of "active".
    comparable = store_period_sales.loc[
        (store_period_sales["current"] > 0) & (store_period_sales["previous"] > 0)
    ].reset_index()
    comparable_count = len(comparable)

    comparable = comparable.merge(
        stores[["store_nbr", "city", "state"]],
        on="store_nbr",
        how="left",
        validate="one_to_one",
    )
    city_growth = (
        comparable.groupby(["city", "state"], as_index=False)
        .agg(previous_sales=("previous", "sum"), current_sales=("current", "sum"))
    )
    city_growth["comparable_growth_pct"] = (
        _safe_divide(city_growth["current_sales"], city_growth["previous_sales"])
        .sub(1)
        .mul(100)
    )
    city_growth = city_growth[["city", "state", "comparable_growth_pct"]]

    return GrowthResult(
        city_growth=city_growth,
        comparable_store_count=comparable_count,
        current_start=current_start,
        current_end=current_end,
        previous_start=previous_start,
        previous_end=previous_end,
    )


def calculate_category_breadth(
    train: pd.DataFrame,
    stores: pd.DataFrame,
    current_start: pd.Timestamp,
    current_end: pd.Timestamp,
    minimum_share: float = 0.01,
) -> pd.DataFrame:
    """Count current-period families meeting a given share of city sales."""
    if not 0 < minimum_share <= 1:
        raise ValueError("minimum_share must be greater than 0 and at most 1")

    current_sales = train.loc[train["date"].between(current_start, current_end)]
    sales = add_store_locations(current_sales, stores)
    family_sales = (
        sales.groupby(["city", "state", "family"], as_index=False)["sales"].sum()
    )
    family_sales["city_total_sales"] = family_sales.groupby(
        ["city", "state"]
    )["sales"].transform("sum")
    zero_sales_cities = family_sales.loc[
        family_sales["city_total_sales"] == 0, ["city", "state"]
    ].drop_duplicates()
    if not zero_sales_cities.empty:
        warnings.warn(
            f"{len(zero_sales_cities)} cities have zero total sales; their category "
            "breadth will be zero.",
            stacklevel=2,
        )
    family_sales["family_share"] = _safe_divide(
        family_sales["sales"], family_sales["city_total_sales"]
    )
    breadth = (
        family_sales.assign(qualifies=family_sales["family_share"] >= minimum_share)
        .groupby(["city", "state"], as_index=False)["qualifies"]
        .sum()
        .rename(columns={"qualifies": "category_breadth"})
    )
    breadth["category_breadth"] = breadth["category_breadth"].astype(int)
    return breadth


def calculate_city_metrics(
    train: pd.DataFrame,
    stores: pd.DataFrame,
    transactions: pd.DataFrame,
    period_days: int = 365,
    minimum_family_share: float = 0.01,
) -> tuple[pd.DataFrame, GrowthResult]:
    """Combine all four unscaled city metrics into one table."""
    growth = calculate_comparable_growth(train, stores, period_days=period_days)
    activity = calculate_activity_metrics(
        train,
        stores,
        transactions,
        current_start=growth.current_start,
        current_end=growth.current_end,
    )
    breadth = calculate_category_breadth(
        train,
        stores,
        current_start=growth.current_start,
        current_end=growth.current_end,
        minimum_share=minimum_family_share,
    )

    metrics = activity.merge(growth.city_growth, on=["city", "state"], how="left")
    metrics = metrics.merge(breadth, on=["city", "state"], how="left")
    no_growth = int(metrics["comparable_growth_pct"].isna().sum())
    if no_growth:
        warnings.warn(
            f"{no_growth} cities have insufficient comparable-store history; "
            "their growth and opportunity scores will remain missing.",
            stacklevel=2,
        )
    return metrics, growth
