"""Deterministic financial statement label mapping."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


MAPPING_METADATA_COLUMNS = [
    "original_label",
    "normalized_label",
    "statement_type",
    "row_position",
    "mapping_status",
    "canonical_label",
    "display_label",
    "matched_alias",
    "matched_rule_kind",
    "concept_category",
    "concept_family",
    "rollup_role",
    "review_reason",
    "includes_restricted_cash",
]

_PUNCTUATION_PATTERN = re.compile(r"[^\w\s]")


def normalize_mapping_label(label: Any) -> str:
    """Normalize a source statement label for exact deterministic matching."""
    if label is None:
        return ""

    try:
        if pd.isna(label):
            return ""
    except TypeError:
        pass

    normalized = str(label).lower().strip()
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"['\u2019]", "", normalized)
    normalized = _PUNCTUATION_PATTERN.sub(" ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def map_statement_rows(df: pd.DataFrame, statement_type: str) -> tuple[pd.DataFrame, list[dict]]:
    """Map cleaned statement rows to canonical metadata without changing values."""
    if statement_type != "balance_sheet":
        raise ValueError("Only balance_sheet asset mapping is implemented in this step.")
    if len(df.columns) == 0:
        raise ValueError("Mapping requires a DataFrame with at least one label column.")

    mapped_df = df.copy(deep=True)
    label_column = mapped_df.columns[0]

    audit_records = []
    metadata_by_column = {column: [] for column in MAPPING_METADATA_COLUMNS}

    for row_position, original_label in enumerate(mapped_df[label_column].tolist()):
        metadata = _metadata_for_label(
            original_label=original_label,
            normalized_label=normalize_mapping_label(original_label),
            statement_type=statement_type,
            row_position=row_position,
        )
        audit_records.append(metadata.copy())
        for column in MAPPING_METADATA_COLUMNS:
            metadata_by_column[column].append(metadata[column])

    for column, values in metadata_by_column.items():
        mapped_df[column] = pd.Series(values, index=mapped_df.index, dtype=object)

    return mapped_df, audit_records


def _metadata_for_label(
    *,
    original_label: Any,
    normalized_label: str,
    statement_type: str,
    row_position: int,
) -> dict:
    rule = _SPECIAL_ASSET_RULES.get(normalized_label)
    if rule is None:
        rule = _AUTO_MAP_ASSET_RULES.get(normalized_label)

    if rule is None:
        rule = {
            "mapping_status": "unmapped",
            "canonical_label": None,
            "display_label": None,
            "matched_alias": None,
            "matched_rule_kind": None,
            "concept_category": None,
            "concept_family": None,
            "rollup_role": "none",
            "review_reason": None,
            "includes_restricted_cash": False,
        }

    return {
        "original_label": original_label,
        "normalized_label": normalized_label,
        "statement_type": statement_type,
        "row_position": row_position,
        **rule,
    }


def _asset_rule(
    *,
    mapping_status: str,
    canonical_label: str | None,
    display_label: str | None,
    matched_alias: str,
    matched_rule_kind: str,
    concept_category: str,
    concept_family: str,
    rollup_role: str,
    review_reason: str | None = None,
    includes_restricted_cash: bool = False,
) -> dict:
    return {
        "mapping_status": mapping_status,
        "canonical_label": canonical_label,
        "display_label": display_label,
        "matched_alias": matched_alias,
        "matched_rule_kind": matched_rule_kind,
        "concept_category": concept_category,
        "concept_family": concept_family,
        "rollup_role": rollup_role,
        "review_reason": review_reason,
        "includes_restricted_cash": includes_restricted_cash,
    }


def _auto_rule(
    *,
    alias: str,
    canonical_label: str,
    display_label: str,
    concept_family: str,
    rollup_role: str,
    concept_category: str = "reported_concept",
) -> dict:
    return _asset_rule(
        mapping_status="auto_mapped",
        canonical_label=canonical_label,
        display_label=display_label,
        matched_alias=alias,
        matched_rule_kind="auto_alias",
        concept_category=concept_category,
        concept_family=concept_family,
        rollup_role=rollup_role,
    )


_AUTO_MAP_ASSET_RULES = {
    alias: _auto_rule(
        alias=alias,
        canonical_label="cash_and_equivalents",
        display_label="Cash and Cash Equivalents",
        concept_family="liquidity",
        rollup_role="narrow",
    )
    for alias in (
        "cash and cash equivalents",
        "cash and equivalents",
    )
}

_AUTO_MAP_ASSET_RULES.update(
    {
        alias: _auto_rule(
            alias=alias,
            canonical_label="accounts_receivable",
            display_label="Accounts Receivable",
            concept_family="receivables",
            rollup_role="component",
        )
        for alias in (
            "accounts receivable",
            "accounts receivable net",
            "trade receivables",
            "trade receivables net",
        )
    }
)

_AUTO_MAP_ASSET_RULES["trade and other receivables"] = _asset_rule(
    mapping_status="review_only",
    canonical_label="receivables_total",
    display_label="Trade and Other Receivables",
    matched_alias="trade and other receivables",
    matched_rule_kind="special_review",
    concept_category="composite_label",
    concept_family="receivables",
    rollup_role="composite",
    review_reason="includes_other_receivables",
)

_AUTO_MAP_ASSET_RULES.update(
    {
        alias: _auto_rule(
            alias=alias,
            canonical_label="inventory",
            display_label="Inventory",
            concept_family="inventory",
            rollup_role="total",
        )
        for alias in (
            "inventory",
            "inventories",
        )
    }
)

_AUTO_MAP_ASSET_RULES.update(
    {
        alias: _auto_rule(
            alias=alias,
            canonical_label="current_assets",
            display_label="Current Assets",
            concept_family="current_assets",
            rollup_role="total",
        )
        for alias in (
            "current assets",
            "total current assets",
        )
    }
)

_AUTO_MAP_ASSET_RULES.update(
    {
        alias: _auto_rule(
            alias=alias,
            canonical_label="pp_and_e",
            display_label="PP&E",
            concept_family="long_lived_assets",
            rollup_role="narrow",
        )
        for alias in (
            "property plant and equipment",
            "property plant and equipment net",
            "property plant equipment",
            "property plant equipment net",
            "ppe",
            "pp and e",
        )
    }
)

_AUTO_MAP_ASSET_RULES["total assets"] = _auto_rule(
    alias="total assets",
    canonical_label="total_assets",
    display_label="Total Assets",
    concept_family="total_assets",
    rollup_role="total",
)


_SPECIAL_ASSET_RULES = {
    "cash": _asset_rule(
        mapping_status="unmapped",
        canonical_label=None,
        display_label=None,
        matched_alias="cash",
        matched_rule_kind="special_review",
        concept_category="broad_label",
        concept_family="liquidity",
        rollup_role="broad_unspecified",
        review_reason="broad_cash_label",
    ),
    "cash on hand": _asset_rule(
        mapping_status="unmapped",
        canonical_label=None,
        display_label=None,
        matched_alias="cash on hand",
        matched_rule_kind="special_review",
        concept_category="broad_label",
        concept_family="liquidity",
        rollup_role="broad_unspecified",
        review_reason="broad_vendor_label",
    ),
    "cash and short term investments": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="cash and short term investments",
        matched_rule_kind="special_review",
        concept_category="composite_label",
        concept_family="liquidity",
        rollup_role="composite",
        review_reason="includes_short_term_investments",
    ),
    "cash and marketable securities": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="cash and marketable securities",
        matched_rule_kind="special_review",
        concept_category="composite_label",
        concept_family="liquidity",
        rollup_role="composite",
        review_reason="includes_marketable_securities",
    ),
    "cash and cash equivalents and restricted cash": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="cash and cash equivalents and restricted cash",
        matched_rule_kind="special_review",
        concept_category="conditional_label",
        concept_family="liquidity",
        rollup_role="conditional",
        review_reason="restricted_cash_scope",
        includes_restricted_cash=True,
    ),
    "receivables": _asset_rule(
        mapping_status="unmapped",
        canonical_label=None,
        display_label=None,
        matched_alias="receivables",
        matched_rule_kind="special_review",
        concept_category="broad_label",
        concept_family="receivables",
        rollup_role="broad_unspecified",
        review_reason="broad_receivables_label",
    ),
    "other receivables": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="other receivables",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="receivables",
        rollup_role="component",
        review_reason="other_receivables_not_supported_yet",
    ),
    "accounts receivable net and other": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="accounts receivable net and other",
        matched_rule_kind="special_review",
        concept_category="composite_label",
        concept_family="receivables",
        rollup_role="composite",
        review_reason="includes_other_receivables",
    ),
    "raw materials": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="raw materials",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="inventory",
        rollup_role="component",
        review_reason="inventory_component_not_supported_yet",
    ),
    "finished goods": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="finished goods",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="inventory",
        rollup_role="component",
        review_reason="inventory_component_not_supported_yet",
    ),
    "work in process": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="work in process",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="inventory",
        rollup_role="component",
        review_reason="inventory_component_not_supported_yet",
    ),
    "stock": _asset_rule(
        mapping_status="unmapped",
        canonical_label=None,
        display_label=None,
        matched_alias="stock",
        matched_rule_kind="special_review",
        concept_category="broad_label",
        concept_family="inventory",
        rollup_role="broad_unspecified",
        review_reason="broad_or_regional_label",
    ),
    "fixed assets": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="fixed assets",
        matched_rule_kind="special_review",
        concept_category="conditional_label",
        concept_family="long_lived_assets",
        rollup_role="conditional",
        review_reason="may_not_equal_pp_and_e",
    ),
    "tangible assets": _asset_rule(
        mapping_status="review_only",
        canonical_label=None,
        display_label=None,
        matched_alias="tangible assets",
        matched_rule_kind="special_review",
        concept_category="conditional_label",
        concept_family="long_lived_assets",
        rollup_role="conditional",
        review_reason="may_not_equal_pp_and_e",
    ),
    "right of use assets": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="right of use assets",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="long_lived_assets",
        rollup_role="component",
        review_reason="separate_asset_class",
    ),
    "construction in progress": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="construction in progress",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="long_lived_assets",
        rollup_role="component",
        review_reason="pp_and_e_component_not_supported_yet",
    ),
    "intangible assets": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="intangible assets",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="long_lived_assets",
        rollup_role="component",
        review_reason="intangible_assets_not_supported_yet",
    ),
    "goodwill": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="goodwill",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="long_lived_assets",
        rollup_role="component",
        review_reason="goodwill_not_supported_yet",
    ),
    "assets": _asset_rule(
        mapping_status="unmapped",
        canonical_label=None,
        display_label=None,
        matched_alias="assets",
        matched_rule_kind="special_review",
        concept_category="broad_label",
        concept_family="other_assets",
        rollup_role="broad_unspecified",
        review_reason="broad_assets_label",
    ),
    "other current assets": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="other current assets",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="current_assets",
        rollup_role="component",
        review_reason="other_current_assets_not_supported_yet",
    ),
    "other non current assets": _asset_rule(
        mapping_status="deferred",
        canonical_label=None,
        display_label=None,
        matched_alias="other non current assets",
        matched_rule_kind="special_review",
        concept_category="deferred_canonical",
        concept_family="other_assets",
        rollup_role="component",
        review_reason="other_non_current_assets_not_supported_yet",
    ),
}
