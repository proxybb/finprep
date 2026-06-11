import pandas as pd

from cleaning.identities import check_balance_sheet_identity


def _schema(identity_ready=True, missing=None):
    return {
        "statement_type": "balance_sheet",
        "identity_ready": identity_ready,
        "required": {"present": [], "missing": missing or []},
    }


def _mapped_df(rows):
    return pd.DataFrame(rows)


def _row(canonical_label, mapping_status="auto_mapped", **periods):
    return {
        "line_item": canonical_label,
        "canonical_label": canonical_label,
        "mapping_status": mapping_status,
        "review_reason": None,
        "concept_category": "reported_concept",
        "display_label": canonical_label,
        **periods,
    }


def test_passing_balance_sheet_identity():
    result = check_balance_sheet_identity(
        _mapped_df(
            [
                _row("total_assets", **{"2023": 1000}),
                _row("total_liabilities", **{"2023": 400}),
                _row("total_equity", **{"2023": 600}),
            ]
        ),
        _schema(),
    )

    assert result["ran"] is True
    assert result["passed"] is True
    assert result["periods"][0]["difference"] == 0


def test_failing_balance_sheet_identity():
    result = check_balance_sheet_identity(
        _mapped_df(
            [
                _row("total_assets", **{"2023": 1000}),
                _row("total_liabilities", **{"2023": 450}),
                _row("total_equity", **{"2023": 600}),
            ]
        ),
        _schema(),
    )

    assert result["ran"] is True
    assert result["passed"] is False
    assert result["periods"][0]["difference"] == -50
    assert result["periods"][0]["passed"] is False


def test_balance_sheet_identity_runs_per_period():
    result = check_balance_sheet_identity(
        _mapped_df(
            [
                _row("total_assets", **{"2022": 1000, "2023": 1000, "2024": 900}),
                _row("total_liabilities", **{"2022": 400, "2023": 450, "2024": 500}),
                _row("total_equity", **{"2022": 600, "2023": 600, "2024": 400}),
            ]
        ),
        _schema(),
    )

    assert result["ran"] is True
    assert result["passed"] is False
    assert [period["period"] for period in result["periods"]] == ["2022", "2023", "2024"]
    assert [period["passed"] for period in result["periods"]] == [True, False, True]


def test_balance_sheet_identity_allows_rounding_tolerance():
    result = check_balance_sheet_identity(
        _mapped_df(
            [
                _row("total_assets", **{"2023": 1000.5}),
                _row("total_liabilities", **{"2023": 400}),
                _row("total_equity", **{"2023": 600}),
            ]
        ),
        _schema(),
    )

    assert result["ran"] is True
    assert result["passed"] is True
    assert result["periods"][0]["difference"] == 0.5


def test_balance_sheet_identity_skips_when_schema_not_ready():
    result = check_balance_sheet_identity(
        _mapped_df(
            [
                _row("total_assets", **{"2023": 1000}),
                _row("total_liabilities", **{"2023": 400}),
            ]
        ),
        _schema(identity_ready=False, missing=["total_equity"]),
    )

    assert result["ran"] is False
    assert result["passed"] is False
    assert "missing required fields: total_equity" == result["skipped_reason"]


def test_review_only_rows_are_ignored_for_identity_check():
    result = check_balance_sheet_identity(
        _mapped_df(
            [
                _row("total_assets", **{"2023": 1000}),
                _row("total_liabilities", **{"2023": 400}),
                _row("total_equity", mapping_status="review_only", **{"2023": 600}),
            ]
        ),
        _schema(identity_ready=False, missing=["total_equity"]),
    )

    assert result["ran"] is False
    assert "total_equity" in result["skipped_reason"]


def test_duplicate_canonical_rows_skip_cleanly():
    result = check_balance_sheet_identity(
        _mapped_df(
            [
                _row("total_assets", **{"2023": 1000}),
                _row("total_assets", **{"2023": 1000}),
                _row("total_liabilities", **{"2023": 400}),
                _row("total_equity", **{"2023": 600}),
            ]
        ),
        _schema(),
    )

    assert result["ran"] is False
    assert result["skipped_reason"] == "duplicate auto-mapped rows for total_assets"
    assert result["errors"][0]["code"] == "duplicate_canonical_rows"


def test_metadata_columns_are_not_treated_as_periods():
    result = check_balance_sheet_identity(
        _mapped_df(
            [
                _row("total_assets", **{"2023": 1000}),
                _row("total_liabilities", **{"2023": 400}),
                _row("total_equity", **{"2023": 600}),
            ]
        ),
        _schema(),
    )

    assert [period["period"] for period in result["periods"]] == ["2023"]


def test_non_numeric_period_value_returns_clean_period_error():
    result = check_balance_sheet_identity(
        _mapped_df(
            [
                _row("total_assets", **{"2023": 1000}),
                _row("total_liabilities", **{"2023": "not available"}),
                _row("total_equity", **{"2023": 600}),
            ]
        ),
        _schema(),
    )

    assert result["ran"] is True
    assert result["passed"] is False
    assert result["periods"][0]["passed"] is False
    assert result["periods"][0]["error"]["code"] == "non_numeric_identity_value"
    assert result["errors"][0]["fields"] == ["total_liabilities"]
