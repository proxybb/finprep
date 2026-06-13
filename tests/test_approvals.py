import pandas as pd

from cleaning.approvals import (
    apply_balance_sheet_approvals,
    apply_balance_sheet_overrides,
)


def test_balance_sheet_approval_preserves_source_metadata():
    mapped_df = pd.DataFrame(
        [
            {
                "row_position": 2,
                "original_label": "Stockholders Equity",
                "normalized_label": "stockholders equity",
                "mapping_status": "review_only",
                "canonical_label": None,
                "display_label": "Stockholders Equity",
                "matched_alias": "stockholders equity",
                "matched_rule_kind": "special_review",
                "concept_category": "conditional_label",
                "concept_family": "owner_equity",
                "rollup_role": "conditional",
                "review_reason": "owner_only_equity_may_exclude_non_controlling_interests",
                "2023": 600,
            }
        ]
    )

    result = apply_balance_sheet_approvals(
        mapped_df,
        [{"row_position": 2, "canonical_label": "total_equity"}],
    )
    approved_row = result.iloc[0]

    assert approved_row["mapping_status"] == "user_approved"
    assert approved_row["canonical_label"] == "total_equity"
    assert approved_row["display_label"] == "Total Equity"
    assert approved_row["matched_rule_kind"] == "user_approved"
    assert approved_row["original_label"] == "Stockholders Equity"
    assert approved_row["normalized_label"] == "stockholders equity"
    assert approved_row["matched_alias"] == "stockholders equity"
    assert (
        approved_row["review_reason"]
        == "owner_only_equity_may_exclude_non_controlling_interests"
    )


def test_balance_sheet_approval_ignores_invalid_row_position():
    mapped_df = pd.DataFrame(
        [
            {
                "row_position": 2,
                "mapping_status": "review_only",
                "canonical_label": None,
                "concept_family": "owner_equity",
            }
        ]
    )

    result = apply_balance_sheet_approvals(
        mapped_df,
        [{"row_position": 99, "canonical_label": "total_equity"}],
    )

    assert result.iloc[0]["mapping_status"] == "review_only"
    assert pd.isna(result.iloc[0]["canonical_label"])


def test_balance_sheet_override_adds_user_override_row_for_total_equity():
    mapped_df = pd.DataFrame(
        [
            {
                "line_item": "Total Assets",
                "2023": 1000,
                "original_label": "Total Assets",
                "normalized_label": "total assets",
                "statement_type": "balance_sheet",
                "row_position": 0,
                "mapping_status": "auto_mapped",
                "canonical_label": "total_assets",
                "display_label": "Total Assets",
                "matched_alias": "total assets",
                "matched_rule_kind": "auto_alias",
                "concept_category": "reported_concept",
                "concept_family": "total_assets",
                "rollup_role": "total",
                "review_reason": None,
                "includes_restricted_cash": False,
            }
        ]
    )

    result = apply_balance_sheet_overrides(
        mapped_df,
        [{"canonical_label": "total_equity", "values": {"2023": 600}}],
    )

    assert len(result.index) == 2
    override_row = result.iloc[1]
    assert override_row["line_item"] == "User override: Total Equity"
    assert override_row["2023"] == 600
    assert override_row["canonical_label"] == "total_equity"
    assert override_row["mapping_status"] == "user_override"
    assert override_row["display_label"] == "Total Equity"
    assert override_row["matched_rule_kind"] == "user_override"
    assert override_row["review_reason"] == "user_entered_required_field_override"


def test_balance_sheet_override_does_not_overwrite_existing_trusted_total_equity():
    mapped_df = pd.DataFrame(
        [
            {
                "line_item": "Total Equity",
                "2023": 600,
                "row_position": 0,
                "mapping_status": "auto_mapped",
                "canonical_label": "total_equity",
            }
        ]
    )

    result = apply_balance_sheet_overrides(
        mapped_df,
        [{"canonical_label": "total_equity", "values": {"2023": 500}}],
    )

    assert len(result.index) == 1
    assert result.iloc[0]["2023"] == 600
    assert result.iloc[0]["mapping_status"] == "auto_mapped"


def test_balance_sheet_override_ignores_invalid_canonical_label():
    mapped_df = pd.DataFrame(
        [
            {
                "line_item": "Total Assets",
                "2023": 1000,
                "row_position": 0,
                "mapping_status": "auto_mapped",
                "canonical_label": "total_assets",
            }
        ]
    )

    result = apply_balance_sheet_overrides(
        mapped_df,
        [{"canonical_label": "revenue", "values": {"2023": 100}}],
    )

    assert result.equals(mapped_df)
