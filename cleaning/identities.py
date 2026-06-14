"""Accounting identity checks for mapped financial statement data."""

from __future__ import annotations

from numbers import Number
from typing import Any

import pandas as pd

from cleaning.mapping.base import MAPPING_METADATA_COLUMNS
from cleaning.mechanical import clean_numeric_value


BALANCE_SHEET_IDENTITY_TOLERANCE = 1.0
BALANCE_SHEET_IDENTITY_FIELDS = [
    "total_assets",
    "total_liabilities",
    "total_equity",
]
TRUSTED_BALANCE_SHEET_IDENTITY_STATUSES = {
    "auto_mapped",
    "user_approved",
    "user_override",
}
NON_PERIOD_COLUMNS = set(MAPPING_METADATA_COLUMNS) | {
    "line_item",
    "label",
    "labels",
    "account",
    "accounts",
    "item",
    "description",
}


def check_balance_sheet_identity(
    mapped_df: pd.DataFrame,
    schema_result: dict[str, Any],
) -> dict[str, Any]:
    """Check Assets = Liabilities + Equity using strict mapped total rows only."""
    result = _base_result()

    if not isinstance(schema_result, dict):
        return _skipped_result(result, "schema validation result unavailable")
    if schema_result.get("statement_type") != "balance_sheet":
        return _skipped_result(result, "not a Balance Sheet schema result")
    if not schema_result.get("identity_ready"):
        return _skipped_result(result, _schema_not_ready_reason(schema_result))
    if not isinstance(mapped_df, pd.DataFrame):
        return _skipped_result(result, "mapped DataFrame unavailable")

    missing_columns = [
        column for column in ("canonical_label", "mapping_status") if column not in mapped_df.columns
    ]
    if missing_columns:
        return _skipped_result(
            result,
            f"missing mapping metadata columns: {', '.join(missing_columns)}",
        )

    strict_rows = mapped_df[
        (mapped_df["mapping_status"].isin(TRUSTED_BALANCE_SHEET_IDENTITY_STATUSES))
        & (mapped_df["canonical_label"].isin(BALANCE_SHEET_IDENTITY_FIELDS))
    ]

    rows_by_label: dict[str, pd.Series] = {}
    for label in BALANCE_SHEET_IDENTITY_FIELDS:
        matching = strict_rows[strict_rows["canonical_label"] == label]
        if matching.empty:
            return _skipped_result(result, f"missing required strict row: {label}")
        if len(matching.index) > 1:
            result["errors"].append(
                {
                    "code": "duplicate_canonical_rows",
                    "canonical_label": label,
                    "message": f"Duplicate trusted rows found for {label}.",
                }
            )
            return _skipped_result(result, f"duplicate trusted rows for {label}")
        rows_by_label[label] = matching.iloc[0]

    period_columns = _period_columns(mapped_df, rows_by_label)
    if not period_columns:
        return _skipped_result(result, "no numeric period columns available")

    result["ran"] = True
    for column in period_columns:
        period_result = _check_period(column, rows_by_label)
        result["periods"].append(period_result)
        if period_result.get("error"):
            result["errors"].append(period_result["error"])

    result["passed"] = bool(result["periods"]) and all(
        period["passed"] for period in result["periods"]
    )
    return result


def _base_result() -> dict[str, Any]:
    return {
        "statement_type": "balance_sheet",
        "check_name": "balance_sheet_identity",
        "ran": False,
        "passed": False,
        "skipped_reason": None,
        "tolerance": BALANCE_SHEET_IDENTITY_TOLERANCE,
        "periods": [],
        "errors": [],
    }


def _skipped_result(result: dict[str, Any], reason: str) -> dict[str, Any]:
    result["ran"] = False
    result["passed"] = False
    result["skipped_reason"] = reason
    return result


def _schema_not_ready_reason(schema_result: dict[str, Any]) -> str:
    missing = schema_result.get("required", {}).get("missing", [])
    if missing:
        return f"missing required fields: {', '.join(missing)}"
    return "schema not identity-ready"


def _period_columns(
    mapped_df: pd.DataFrame,
    rows_by_label: dict[str, pd.Series],
) -> list[Any]:
    columns = []
    for column in mapped_df.columns:
        normalized_column = str(column).strip().lower()
        if normalized_column in NON_PERIOD_COLUMNS:
            continue

        values = [rows_by_label[label].get(column) for label in BALANCE_SHEET_IDENTITY_FIELDS]
        if any(_to_number(value) is not None for value in values):
            columns.append(column)

    return columns


def _check_period(column: Any, rows_by_label: dict[str, pd.Series]) -> dict[str, Any]:
    values = {
        label: _to_number(rows_by_label[label].get(column))
        for label in BALANCE_SHEET_IDENTITY_FIELDS
    }
    bad_labels = [label for label, value in values.items() if value is None]
    if bad_labels:
        error = {
            "code": "non_numeric_identity_value",
            "period": str(column),
            "fields": bad_labels,
            "message": (
                f"Non-numeric Balance Sheet identity value for {str(column)}: "
                f"{', '.join(bad_labels)}."
            ),
        }
        return {
            "period": str(column),
            "total_assets": values["total_assets"],
            "total_liabilities": values["total_liabilities"],
            "total_equity": values["total_equity"],
            "difference": None,
            "passed": False,
            "error": error,
        }

    difference = (
        values["total_assets"]
        - values["total_liabilities"]
        - values["total_equity"]
    )
    return {
        "period": str(column),
        "total_assets": values["total_assets"],
        "total_liabilities": values["total_liabilities"],
        "total_equity": values["total_equity"],
        "difference": difference,
        "passed": abs(difference) <= BALANCE_SHEET_IDENTITY_TOLERANCE,
    }


def _to_number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass

    cleaned = clean_numeric_value(value)
    if isinstance(cleaned, Number) and not isinstance(cleaned, bool):
        return float(cleaned)
    return None
