"""Selection/unseen split and market-regime helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


SPLIT_VALUES = ("selection", "unseen", "full_sample")
REGIME_VALUES = ("rising", "falling", "unknown")
STABILITY_SUMMARY_COLUMNS = (
    "selection_count",
    "unseen_count",
    "selection_average_return",
    "unseen_average_return",
    "stability_delta",
    "stability_label",
)


class SplitInputError(ValueError):
    """Raised when split or regime inputs are structurally invalid."""


def label_period_split(
    frame: pd.DataFrame,
    unseen_start_date: str | None,
    date_column: str = "date",
) -> pd.DataFrame:
    """Add a `period_split` column without using unseen rows for selection labels."""

    _require_columns(frame, [date_column], scope="period split input")
    output = frame.copy()
    dates = pd.to_datetime(output[date_column], errors="raise")

    if unseen_start_date is None:
        output["period_split"] = "full_sample"
        return output

    unseen_start = pd.to_datetime(unseen_start_date, errors="raise")
    output["period_split"] = "selection"
    output.loc[dates >= unseen_start, "period_split"] = "unseen"
    return output


def label_market_regime(
    frame: pd.DataFrame,
    benchmark_prices: pd.DataFrame | None = None,
    date_column: str = "date",
    price_column: str = "close",
    lookback_days: int = 20,
) -> pd.DataFrame:
    """Add rising/falling regime labels from benchmark or local price history."""

    if lookback_days <= 0:
        raise SplitInputError("lookback_days must be positive")
    _require_columns(frame, [date_column], scope="regime input")

    output = frame.copy()
    output[date_column] = pd.to_datetime(output[date_column], errors="raise")

    if benchmark_prices is not None:
        regime_frame = build_market_regime_frame(
            benchmark_prices=benchmark_prices,
            lookback_days=lookback_days,
        )
        output = output.merge(regime_frame, on=date_column, how="left")
    else:
        _require_columns(output, [price_column], scope="regime input")
        output = output.sort_values(date_column).reset_index(drop=True)
        output["regime_return"] = pd.to_numeric(output[price_column], errors="raise").pct_change(
            lookback_days
        )
        output["market_regime"] = _regime_labels(output["regime_return"])

    output["market_regime"] = output["market_regime"].fillna("unknown")
    return output


def build_market_regime_frame(
    benchmark_prices: pd.DataFrame,
    lookback_days: int = 20,
    date_column: str = "date",
    price_column: str = "close",
) -> pd.DataFrame:
    """Build date-level market-regime labels from a benchmark price series."""

    if lookback_days <= 0:
        raise SplitInputError("lookback_days must be positive")
    _require_columns(benchmark_prices, [date_column, price_column], scope="benchmark")

    frame = benchmark_prices.loc[:, [date_column, price_column]].copy()
    frame[date_column] = pd.to_datetime(frame[date_column], errors="raise")
    frame[price_column] = pd.to_numeric(frame[price_column], errors="raise")
    frame = frame.sort_values(date_column).reset_index(drop=True)
    if frame[date_column].duplicated().any():
        raise SplitInputError("benchmark contains duplicate dates")

    frame["regime_return"] = frame[price_column].pct_change(lookback_days)
    frame["market_regime"] = _regime_labels(frame["regime_return"])
    return frame.loc[:, [date_column, "regime_return", "market_regime"]]


def apply_split_and_regime_labels(
    frame: pd.DataFrame,
    unseen_start_date: str | None,
    benchmark_prices: pd.DataFrame | None = None,
    date_column: str = "date",
    price_column: str = "close",
    lookback_days: int = 20,
) -> pd.DataFrame:
    """Apply period split and market-regime labels in one deterministic pass."""

    with_split = label_period_split(
        frame=frame,
        unseen_start_date=unseen_start_date,
        date_column=date_column,
    )
    return label_market_regime(
        frame=with_split,
        benchmark_prices=benchmark_prices,
        date_column=date_column,
        price_column=price_column,
        lookback_days=lookback_days,
    )


def summarize_unseen_stability(
    observations: pd.DataFrame,
    group_columns: list[str],
    return_column: str,
    status_column: str | None = "status",
    eligible_status: str = "ok",
) -> pd.DataFrame:
    """Compare selection and unseen average returns for predefined groups."""

    required = list(group_columns) + ["period_split", return_column]
    if status_column is not None:
        required.append(status_column)
    _require_columns(observations, required, scope="stability input")

    frame = observations.copy()
    if status_column is not None:
        frame = frame[frame[status_column] == eligible_status].copy()
    if frame.empty:
        return _empty_stability_frame(group_columns)

    frame[return_column] = pd.to_numeric(frame[return_column], errors="coerce")
    frame = frame[frame["period_split"].isin(("selection", "unseen"))]
    if frame.empty:
        return _empty_stability_frame(group_columns)

    grouped = (
        frame.groupby(group_columns + ["period_split"], dropna=False)[return_column]
        .agg(["count", "mean"])
        .reset_index()
    )
    pivot_count = grouped.pivot_table(
        index=group_columns,
        columns="period_split",
        values="count",
        fill_value=0,
        aggfunc="sum",
    )
    pivot_mean = grouped.pivot_table(
        index=group_columns,
        columns="period_split",
        values="mean",
        aggfunc="mean",
    )

    result = pivot_count.reset_index()
    result["selection_count"] = _column_or_default(pivot_count, "selection", 0).astype(int).to_numpy()
    result["unseen_count"] = _column_or_default(pivot_count, "unseen", 0).astype(int).to_numpy()
    result["selection_average_return"] = _column_or_default(pivot_mean, "selection", pd.NA).to_numpy()
    result["unseen_average_return"] = _column_or_default(pivot_mean, "unseen", pd.NA).to_numpy()
    result["stability_delta"] = (
        result["unseen_average_return"] - result["selection_average_return"]
    )
    result["stability_label"] = result.apply(_stability_label, axis=1)

    return result.loc[:, group_columns + list(STABILITY_SUMMARY_COLUMNS)]


def write_split_regime_report(
    stability_summary: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Write a compact markdown report for split/regime readiness."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Unseen Period And Regime Split Report",
        "",
        "Status: split/regime helpers implemented, not yet populated with live strategy outputs.",
        "",
        "Implemented scope:",
        "- Selection vs unseen period labels.",
        "- Rising/falling/unknown market regime labels from benchmark history.",
        "- Stability comparison of predefined groups across selection and unseen periods.",
        "",
    ]

    if stability_summary.empty:
        lines.extend(["Current output: no stability summary generated yet.", ""])
    else:
        lines.extend(["## Stability Summary", "", stability_summary.to_markdown(index=False), ""])

    lines.extend(
        [
            "Limitations:",
            "- Unseen period start date must be fixed before strategy selection.",
            "- Regime labels depend on benchmark availability and configured lookback.",
            "- This report is historical research infrastructure, not investment advice.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _regime_labels(regime_return: pd.Series) -> pd.Series:
    labels = pd.Series("unknown", index=regime_return.index, dtype="object")
    labels.loc[regime_return >= 0] = "rising"
    labels.loc[regime_return < 0] = "falling"
    return labels


def _stability_label(row: pd.Series) -> str:
    selection_count = int(row["selection_count"])
    unseen_count = int(row["unseen_count"])
    if selection_count == 0 or unseen_count == 0:
        return "unavailable"

    selection_return = row["selection_average_return"]
    unseen_return = row["unseen_average_return"]
    if pd.isna(selection_return) or pd.isna(unseen_return):
        return "unavailable"
    if selection_return > 0 and unseen_return > 0:
        return "stable_positive"
    if selection_return < 0 and unseen_return < 0:
        return "stable_negative"
    if selection_return * unseen_return < 0:
        return "sign_flip"
    return "inconclusive"


def _column_or_default(frame: pd.DataFrame, column: str, default) -> pd.Series:
    if column in frame.columns:
        return frame[column]
    return pd.Series(default, index=frame.index)


def _empty_stability_frame(group_columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=group_columns + list(STABILITY_SUMMARY_COLUMNS))


def _require_columns(frame: pd.DataFrame, columns: list[str], scope: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise SplitInputError(f"{scope} missing required columns: {', '.join(missing)}")
