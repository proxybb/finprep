import pandas as pd

from cleaning.schema import validate_balance_sheet_schema


def _mapped_df(rows):
    return pd.DataFrame(rows)


def _row(
    canonical_label,
    mapping_status="auto_mapped",
    original_label=None,
    concept_family=None,
    review_reason=None,
    row_position=None,
    display_label=None,
):
    return {
        "original_label": original_label or canonical_label or "source label",
        "normalized_label": original_label or canonical_label or "source label",
        "row_position": row_position,
        "mapping_status": mapping_status,
        "canonical_label": canonical_label,
        "display_label": display_label,
        "concept_family": concept_family,
        "review_reason": review_reason,
    }


def test_identity_ready_balance_sheet_has_required_fields():
    result = validate_balance_sheet_schema(
        _mapped_df(
            [
                _row("total_assets"),
                _row("total_liabilities"),
                _row("total_equity"),
            ]
        )
    )

    assert result["identity_ready"] is True
    assert result["required"]["present"] == [
        "total_assets",
        "total_liabilities",
        "total_equity",
    ]
    assert result["required"]["missing"] == []


def test_missing_total_equity_blocks_identity_readiness():
    result = validate_balance_sheet_schema(
        _mapped_df(
            [
                _row("total_assets"),
                _row("total_liabilities"),
            ]
        )
    )

    assert result["identity_ready"] is False
    assert "total_equity" in result["required"]["missing"]
    assert any(
        warning["code"] == "missing_required_field"
        and warning["field"] == "total_equity"
        for warning in result["warnings"]
    )


def test_review_only_owner_equity_does_not_satisfy_total_equity():
    result = validate_balance_sheet_schema(
        _mapped_df(
            [
                _row("total_assets"),
                _row("total_liabilities"),
                _row(
                    None,
                    mapping_status="review_only",
                    original_label="shareholders equity",
                    concept_family="owner_equity",
                    review_reason="owner_only_equity_may_exclude_non_controlling_interests",
                    row_position=2,
                    display_label="Shareholders Equity",
                ),
            ]
        )
    )

    assert result["identity_ready"] is False
    assert "total_equity" in result["required"]["missing"]
    assert result["candidates"] == [
        {
            "missing_required": "total_equity",
            "original_label": "shareholders equity",
            "normalized_label": "shareholders equity",
            "row_position": 2,
            "canonical_label": None,
            "display_label": "Shareholders Equity",
            "concept_family": "owner_equity",
            "mapping_status": "review_only",
            "review_reason": "owner_only_equity_may_exclude_non_controlling_interests",
            "review_message": "Owner-only equity may exclude non-controlling interests.",
        }
    ]
    assert any(
        warning["code"] == "review_candidate_for_required_field"
        and warning["field"] == "total_equity"
        for warning in result["warnings"]
    )


def test_expected_working_capital_fields_present():
    result = validate_balance_sheet_schema(
        _mapped_df(
            [
                _row("current_assets"),
                _row("current_liabilities"),
                _row("cash_and_equivalents"),
                _row("accounts_receivable"),
                _row("inventory"),
                _row("accounts_payable"),
            ]
        )
    )

    assert result["expected"]["present"] == [
        "current_assets",
        "current_liabilities",
        "cash_and_equivalents",
        "receivables_detail",
        "inventory",
        "payables_detail",
    ]
    assert result["expected"]["missing"] == []


def test_receivables_total_satisfies_receivables_or_group():
    result = validate_balance_sheet_schema(
        _mapped_df(
            [
                _row(
                    "receivables_total",
                    mapping_status="review_only",
                    original_label="trade and other receivables",
                    concept_family="receivables",
                ),
            ]
        )
    )

    assert "receivables_detail" in result["expected"]["present"]
    assert "receivables_detail" not in result["expected"]["missing"]


def test_payables_total_satisfies_payables_or_group():
    result = validate_balance_sheet_schema(
        _mapped_df(
            [
                _row(
                    "payables_total",
                    mapping_status="review_only",
                    original_label="trade and other payables",
                    concept_family="payables",
                ),
            ]
        )
    )

    assert "payables_detail" in result["expected"]["present"]
    assert "payables_detail" not in result["expected"]["missing"]


def test_missing_inventory_is_warning_only_when_required_fields_exist():
    result = validate_balance_sheet_schema(
        _mapped_df(
            [
                _row("total_assets"),
                _row("total_liabilities"),
                _row("total_equity"),
            ]
        )
    )

    assert result["identity_ready"] is True
    assert "inventory" in result["expected"]["missing"]
    assert any(
        warning["code"] == "missing_expected_field"
        and warning["field"] == "inventory"
        and warning["level"] == "warning"
        for warning in result["warnings"]
    )


def test_review_only_total_like_rows_do_not_satisfy_required_fields():
    result = validate_balance_sheet_schema(
        _mapped_df(
            [
                _row(
                    "total_equity",
                    mapping_status="review_only",
                    original_label="conditional total equity",
                    concept_family="total_equity",
                ),
            ]
        )
    )

    assert result["identity_ready"] is False
    assert "total_equity" in result["required"]["missing"]
    assert "total_equity" not in result["required"]["present"]


def test_user_approved_required_field_satisfies_schema_readiness():
    result = validate_balance_sheet_schema(
        _mapped_df(
            [
                _row("total_assets"),
                _row("total_liabilities"),
                _row(
                    "total_equity",
                    mapping_status="user_approved",
                    original_label="stockholders equity",
                    concept_family="owner_equity",
                ),
            ]
        )
    )

    assert result["identity_ready"] is True
    assert "total_equity" in result["required"]["present"]


def test_user_override_required_field_satisfies_schema_readiness():
    result = validate_balance_sheet_schema(
        _mapped_df(
            [
                _row("total_assets"),
                _row("total_liabilities"),
                _row(
                    "total_equity",
                    mapping_status="user_override",
                    original_label="User override: Total Equity",
                ),
            ]
        )
    )

    assert result["identity_ready"] is True
    assert "total_equity" in result["required"]["present"]
    assert result["required"]["missing"] == []


def test_missing_mapping_metadata_columns_return_clean_validation_result():
    result = validate_balance_sheet_schema(
        pd.DataFrame(
            {
                "line_item": ["total assets"],
                "2023": [100],
            }
        )
    )

    assert result["identity_ready"] is False
    assert result["required"]["missing"] == [
        "total_assets",
        "total_liabilities",
        "total_equity",
    ]
    assert result["warnings"] == [
        {
            "level": "error",
            "code": "missing_mapping_metadata_columns",
            "field": None,
            "message": (
                "Balance Sheet schema validation requires mapping metadata "
                "columns: canonical_label, mapping_status."
            ),
        }
    ]
