import pandas as pd

from cleaning.approvals import apply_balance_sheet_approvals


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
