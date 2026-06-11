"""Schema validation rules for supported financial statement inputs."""

from __future__ import annotations

from typing import Any

import pandas as pd


REQUIRED_BALANCE_SHEET_FIELDS = [
    "total_assets",
    "total_liabilities",
    "total_equity",
]

EXPECTED_BALANCE_SHEET_FIELDS = [
    "current_assets",
    "current_liabilities",
    "cash_and_equivalents",
    "receivables_detail",
    "inventory",
    "payables_detail",
]

BALANCE_SHEET_EXPECTED_GROUPS = {
    "current_assets": {"current_assets"},
    "current_liabilities": {"current_liabilities"},
    "cash_and_equivalents": {"cash_and_equivalents"},
    "receivables_detail": {"accounts_receivable", "receivables_total"},
    "inventory": {"inventory"},
    "payables_detail": {"accounts_payable", "payables_total"},
}

REQUIRED_METADATA_COLUMNS = {"canonical_label", "mapping_status"}


def validate_balance_sheet_schema(mapped_df: pd.DataFrame) -> dict[str, Any]:
    """Validate mapped Balance Sheet schema completeness without calculations."""
    missing_metadata = sorted(REQUIRED_METADATA_COLUMNS - set(mapped_df.columns))
    if missing_metadata:
        return _metadata_missing_result(missing_metadata)

    auto_mapped_labels = _canonical_labels_for_status(mapped_df, {"auto_mapped"})
    expected_candidate_labels = _canonical_labels_for_status(
        mapped_df,
        {"auto_mapped", "review_only"},
    )

    required_present = [
        field for field in REQUIRED_BALANCE_SHEET_FIELDS if field in auto_mapped_labels
    ]
    required_missing = [
        field for field in REQUIRED_BALANCE_SHEET_FIELDS if field not in auto_mapped_labels
    ]

    expected_present = [
        field
        for field in EXPECTED_BALANCE_SHEET_FIELDS
        if BALANCE_SHEET_EXPECTED_GROUPS[field] & expected_candidate_labels
    ]
    expected_missing = [
        field
        for field in EXPECTED_BALANCE_SHEET_FIELDS
        if not BALANCE_SHEET_EXPECTED_GROUPS[field] & expected_candidate_labels
    ]

    warnings = []
    for field in required_missing:
        warnings.append(
            {
                "level": "error",
                "code": "missing_required_field",
                "field": field,
                "message": f"Missing required Balance Sheet field: {field}.",
            }
        )
    for field in expected_missing:
        warnings.append(
            {
                "level": "warning",
                "code": "missing_expected_field",
                "field": field,
                "message": f"Missing expected Balance Sheet detail: {field}.",
            }
        )

    candidates = _review_candidates_for_missing_required(mapped_df, required_missing)
    for candidate in candidates:
        warnings.append(
            {
                "level": "warning",
                "code": "review_candidate_for_required_field",
                "field": candidate["missing_required"],
                "message": (
                    f"Review-only candidate present for missing required field "
                    f"{candidate['missing_required']}: {candidate['original_label']}."
                ),
            }
        )

    return {
        "statement_type": "balance_sheet",
        "identity_ready": not required_missing,
        "required": {
            "present": required_present,
            "missing": required_missing,
        },
        "expected": {
            "present": expected_present,
            "missing": expected_missing,
        },
        "warnings": warnings,
        "candidates": candidates,
    }


def _metadata_missing_result(missing_columns: list[str]) -> dict[str, Any]:
    return {
        "statement_type": "balance_sheet",
        "identity_ready": False,
        "required": {
            "present": [],
            "missing": REQUIRED_BALANCE_SHEET_FIELDS.copy(),
        },
        "expected": {
            "present": [],
            "missing": EXPECTED_BALANCE_SHEET_FIELDS.copy(),
        },
        "warnings": [
            {
                "level": "error",
                "code": "missing_mapping_metadata_columns",
                "field": None,
                "message": (
                    "Balance Sheet schema validation requires mapping metadata "
                    f"columns: {', '.join(missing_columns)}."
                ),
            }
        ],
        "candidates": [],
    }


def _canonical_labels_for_status(df: pd.DataFrame, statuses: set[str]) -> set[str]:
    matching = df[df["mapping_status"].isin(statuses)]
    return {
        label
        for label in matching["canonical_label"].dropna().tolist()
        if isinstance(label, str) and label
    }


def _review_candidates_for_missing_required(
    df: pd.DataFrame,
    required_missing: list[str],
) -> list[dict[str, Any]]:
    if not required_missing:
        return []

    candidates = []
    for _, row in df.iterrows():
        if row.get("mapping_status") != "review_only":
            continue

        missing_required = _candidate_required_field(row, required_missing)
        if not missing_required:
            continue

        candidates.append(
            {
                "missing_required": missing_required,
                "original_label": _none_if_missing(row.get("original_label")),
                "normalized_label": _none_if_missing(row.get("normalized_label")),
                "canonical_label": _none_if_missing(row.get("canonical_label")),
                "concept_family": _none_if_missing(row.get("concept_family")),
                "mapping_status": _none_if_missing(row.get("mapping_status")),
                "review_reason": _none_if_missing(row.get("review_reason")),
            }
        )

    return candidates


def _candidate_required_field(row: pd.Series, required_missing: list[str]) -> str | None:
    canonical_label = row.get("canonical_label")
    concept_family = row.get("concept_family")

    if canonical_label in required_missing:
        return canonical_label
    if "total_equity" in required_missing and concept_family in {
        "owner_equity",
        "total_equity",
    }:
        return "total_equity"
    if "total_liabilities" in required_missing and concept_family == "total_liabilities":
        return "total_liabilities"
    if "total_assets" in required_missing and concept_family == "total_assets":
        return "total_assets"
    return None


def _none_if_missing(value: Any) -> Any:
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    return value
