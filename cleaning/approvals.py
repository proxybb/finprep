"""Apply narrow user approvals to mapped financial statement rows."""

from __future__ import annotations

from typing import Any

import pandas as pd

from cleaning.mapping.base import MAPPING_METADATA_COLUMNS, normalize_mapping_label
from cleaning.schema import REQUIRED_BALANCE_SHEET_FIELDS


BALANCE_SHEET_DISPLAY_LABELS = {
    "total_assets": "Total Assets",
    "total_liabilities": "Total Liabilities",
    "total_equity": "Total Equity",
}
TRUSTED_NON_OVERRIDE_STATUSES = {"auto_mapped", "user_approved"}


def apply_balance_sheet_approvals(
    mapped_df: pd.DataFrame,
    approvals: list[dict[str, Any]] | None,
) -> pd.DataFrame:
    """Return a mapped DataFrame with eligible review-only approvals applied."""
    approved_df = mapped_df.copy(deep=True)
    if not approvals or "row_position" not in approved_df.columns:
        return approved_df

    for approval in approvals:
        row_position = _parse_row_position(approval.get("row_position"))
        canonical_label = approval.get("canonical_label")
        if row_position is None or canonical_label not in REQUIRED_BALANCE_SHEET_FIELDS:
            continue

        matching_index = approved_df.index[approved_df["row_position"] == row_position]
        if len(matching_index) != 1:
            continue

        index = matching_index[0]
        row = approved_df.loc[index]
        if row.get("mapping_status") != "review_only":
            continue
        if not _can_approve_required_field(row, canonical_label):
            continue

        approved_df.at[index, "mapping_status"] = "user_approved"
        approved_df.at[index, "canonical_label"] = canonical_label
        approved_df.at[index, "display_label"] = BALANCE_SHEET_DISPLAY_LABELS[
            canonical_label
        ]
        approved_df.at[index, "matched_rule_kind"] = "user_approved"

    return approved_df


def apply_balance_sheet_overrides(
    mapped_df: pd.DataFrame,
    overrides: list[dict[str, Any]] | None,
) -> pd.DataFrame:
    """Return a mapped DataFrame with controlled required-field overrides added."""
    overridden_df = mapped_df.copy(deep=True)
    if not overrides or overridden_df.empty or len(overridden_df.columns) == 0:
        return overridden_df

    for override in overrides:
        canonical_label = override.get("canonical_label")
        if canonical_label not in REQUIRED_BALANCE_SHEET_FIELDS:
            continue
        if _has_existing_trusted_required_row(overridden_df, canonical_label):
            continue

        values = override.get("values")
        if not isinstance(values, dict) or not values:
            continue

        override_row = _build_override_row(overridden_df, canonical_label, values)
        overridden_df = pd.concat(
            [overridden_df, pd.DataFrame([override_row], columns=overridden_df.columns)],
            ignore_index=True,
        )

    return overridden_df


def _parse_row_position(value: Any) -> int | None:
    try:
        row_position = int(value)
    except (TypeError, ValueError):
        return None
    if row_position < 0:
        return None
    return row_position


def _can_approve_required_field(row: pd.Series, canonical_label: str) -> bool:
    row_canonical = row.get("canonical_label")
    concept_family = row.get("concept_family")

    if row_canonical == canonical_label:
        return True
    if canonical_label == "total_equity" and concept_family in {
        "owner_equity",
        "total_equity",
    }:
        return True
    if canonical_label == "total_liabilities" and concept_family == "total_liabilities":
        return True
    if canonical_label == "total_assets" and concept_family == "total_assets":
        return True
    return False


def _has_existing_trusted_required_row(df: pd.DataFrame, canonical_label: str) -> bool:
    if not {"canonical_label", "mapping_status"} <= set(df.columns):
        return False

    matching = df[
        (df["canonical_label"] == canonical_label)
        & (df["mapping_status"].isin(TRUSTED_NON_OVERRIDE_STATUSES))
    ]
    return not matching.empty


def _build_override_row(
    df: pd.DataFrame,
    canonical_label: str,
    values: dict[str, Any],
) -> dict[str, Any]:
    display_label = BALANCE_SHEET_DISPLAY_LABELS[canonical_label]
    source_label = f"User override: {display_label}"
    row = {column: None for column in df.columns}
    row[df.columns[0]] = source_label

    for period, value in values.items():
        if period in row:
            row[period] = value

    metadata = {
        "original_label": source_label,
        "normalized_label": normalize_mapping_label(source_label),
        "statement_type": "balance_sheet",
        "row_position": _next_row_position(df),
        "mapping_status": "user_override",
        "canonical_label": canonical_label,
        "display_label": display_label,
        "matched_alias": "user_override",
        "matched_rule_kind": "user_override",
        "concept_category": "user_override",
        "concept_family": canonical_label,
        "rollup_role": "override",
        "review_reason": "user_entered_required_field_override",
        "includes_restricted_cash": False,
    }
    for column in MAPPING_METADATA_COLUMNS:
        if column in row:
            row[column] = metadata[column]

    return row


def _next_row_position(df: pd.DataFrame) -> int:
    if "row_position" not in df.columns:
        return len(df.index)

    numeric_positions = pd.to_numeric(df["row_position"], errors="coerce").dropna()
    if numeric_positions.empty:
        return len(df.index)
    return int(numeric_positions.max()) + 1
