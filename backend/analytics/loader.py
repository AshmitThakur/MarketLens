"""Load and validate the three Store Sales source files."""

from pathlib import Path
import warnings

import pandas as pd


REQUIRED_COLUMNS = {
    "train.csv": {"date", "store_nbr", "family", "sales", "onpromotion"},
    "stores.csv": {"store_nbr", "city", "state", "type", "cluster"},
    "transactions.csv": {"date", "store_nbr", "transactions"},
}


def _read_csv(path: Path, required_columns: set[str]) -> pd.DataFrame:
    """Read one CSV and fail with a useful message if its schema is invalid."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Required input file not found: {path}. "
            "Download it from the Kaggle Store Sales dataset."
        )

    frame = pd.read_csv(path)
    missing = sorted(required_columns.difference(frame.columns))
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {missing}")
    if frame.empty:
        raise ValueError(f"{path.name} is empty")
    return frame


def _parse_dates(frame: pd.DataFrame, file_name: str) -> pd.DataFrame:
    """Parse the date column and reject invalid or missing dates."""
    frame = frame.copy()
    parsed = pd.to_datetime(frame["date"], errors="coerce")
    invalid_count = int(parsed.isna().sum())
    if invalid_count:
        raise ValueError(f"{file_name} contains {invalid_count} invalid/missing dates")
    frame["date"] = parsed
    return frame


def _validate_numeric_data(train: pd.DataFrame, transactions: pd.DataFrame) -> None:
    """Validate measures whose absence would make the business metrics unreliable."""
    checks = (
        (train, "train.csv", "sales"),
        (train, "train.csv", "onpromotion"),
        (transactions, "transactions.csv", "transactions"),
    )
    for frame, file_name, column in checks:
        if not pd.api.types.is_numeric_dtype(frame[column]):
            raise ValueError(f"{file_name}.{column} must be numeric")
        missing_count = int(frame[column].isna().sum())
        if missing_count:
            raise ValueError(f"{file_name}.{column} contains {missing_count} missing values")

    if (train["sales"] < 0).any():
        raise ValueError("train.csv contains negative sales values")
    if (transactions["transactions"] < 0).any():
        raise ValueError("transactions.csv contains negative transaction values")


def _validate_required_values(
    train: pd.DataFrame, stores: pd.DataFrame, transactions: pd.DataFrame
) -> None:
    """Reject missing identifiers and dimensions that grouping would otherwise drop."""
    checks = (
        (train, "train.csv", ("store_nbr", "family")),
        (stores, "stores.csv", ("store_nbr", "city", "state")),
        (transactions, "transactions.csv", ("store_nbr",)),
    )
    for frame, file_name, columns in checks:
        for column in columns:
            missing_count = int(frame[column].isna().sum())
            if missing_count:
                raise ValueError(
                    f"{file_name}.{column} contains {missing_count} missing values"
                )


def load_data(raw_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load train, stores, and transactions data and apply core validation."""
    raw_dir = Path(raw_dir)
    train = _read_csv(raw_dir / "train.csv", REQUIRED_COLUMNS["train.csv"])
    stores = _read_csv(raw_dir / "stores.csv", REQUIRED_COLUMNS["stores.csv"])
    transactions = _read_csv(
        raw_dir / "transactions.csv", REQUIRED_COLUMNS["transactions.csv"]
    )

    train = _parse_dates(train, "train.csv")
    transactions = _parse_dates(transactions, "transactions.csv")
    _validate_numeric_data(train, transactions)

    _validate_required_values(train, stores, transactions)

    if stores["store_nbr"].duplicated().any():
        duplicates = stores.loc[stores["store_nbr"].duplicated(), "store_nbr"].tolist()
        raise ValueError(f"stores.csv contains duplicate store_nbr values: {duplicates[:10]}")
    known_stores = set(stores["store_nbr"])
    for frame, name in ((train, "train.csv"), (transactions, "transactions.csv")):
        unknown = sorted(set(frame["store_nbr"]) - known_stores)
        if unknown:
            raise ValueError(f"{name} contains stores absent from stores.csv: {unknown[:10]}")

    sales_stores = set(train["store_nbr"])
    transaction_stores = set(transactions["store_nbr"])
    without_transactions = sorted(sales_stores - transaction_stores)
    if without_transactions:
        warnings.warn(
            f"{len(without_transactions)} sales stores have no transaction records: "
            f"{without_transactions[:10]}",
            stacklevel=2,
        )

    positive_sales_days = set(
        map(
            tuple,
            train.loc[train["sales"] > 0, ["date", "store_nbr"]]
            .drop_duplicates()
            .itertuples(index=False, name=None),
        )
    )
    transaction_days = set(
        map(
            tuple,
            transactions[["date", "store_nbr"]]
            .drop_duplicates()
            .itertuples(index=False, name=None),
        )
    )
    missing_transaction_days = positive_sales_days - transaction_days
    if missing_transaction_days:
        warnings.warn(
            f"{len(missing_transaction_days)} store-days with positive sales have no "
            "transaction record. Totals use only observed transactions.",
            stacklevel=2,
        )

    return train, stores, transactions


def build_validation_summary(
    train: pd.DataFrame,
    stores: pd.DataFrame,
    transactions: pd.DataFrame,
    comparable_store_count: int,
) -> dict:
    """Return basic coverage and missing-data information for logging or an API."""
    active_store_ids = train["store_nbr"].dropna().unique()
    active_locations = stores[stores["store_nbr"].isin(active_store_ids)]
    return {
        "earliest_dataset_date": train["date"].min().date().isoformat(),
        "latest_dataset_date": train["date"].max().date().isoformat(),
        "total_stores": int(len(active_store_ids)),
        "number_of_cities": int(active_locations["city"].nunique()),
        "number_of_states": int(active_locations["state"].nunique()),
        "number_of_product_families": int(train["family"].nunique()),
        "missing_values": {
            "train.csv": train.isna().sum().astype(int).to_dict(),
            "stores.csv": stores.isna().sum().astype(int).to_dict(),
            "transactions.csv": transactions.isna().sum().astype(int).to_dict(),
        },
        "comparable_stores": int(comparable_store_count),
        "sales_stores_without_any_transactions": int(
            len(set(active_store_ids) - set(transactions["store_nbr"]))
        ),
        "positive_sales_store_days_without_transactions": int(
            len(
                set(
                    map(
                        tuple,
                        train.loc[train["sales"] > 0, ["date", "store_nbr"]]
                        .drop_duplicates()
                        .itertuples(index=False, name=None),
                    )
                )
                - set(
                    map(
                        tuple,
                        transactions[["date", "store_nbr"]]
                        .drop_duplicates()
                        .itertuples(index=False, name=None),
                    )
                )
            )
        ),
    }
