"""Apply narrow user approvals to mapped financial statement rows."""

from __future__ import annotations

from typing import Any

import pandas as pd

from cleaning.schema import REQUIRED_BALANCE_SHEET_FIELDS


BALANCE_SHEET_DISPLAY_LABELS = {
    "total_assets": "Total Assets",
    "total_liabilities": "Total Liabilities",
    "total_equity": "Total Equity",
}


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
