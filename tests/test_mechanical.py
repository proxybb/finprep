import pandas as pd

from cleaning.mechanical import (
    clean_numeric_value,
    drop_exact_duplicate_rows,
    drop_blank_rows_and_columns,
    normalize_header_text,
    normalize_headers,
    normalize_missing_value,
    normalize_period_label,
    normalize_string_value,
    run_mechanical_cleaning,
)


def test_drop_blank_rows_and_columns_drops_fully_blank_structures():
    df = pd.DataFrame(
        {
            "line_item": ["Revenue", "   ", None],
            "2023": ["1,200", "-", None],
            "blank_col": ["", " ", None],
        }
    )

    cleaned = drop_blank_rows_and_columns(df)

    assert cleaned.shape == (1, 2)
    assert list(cleaned.columns) == ["line_item", "2023"]
    assert cleaned.iloc[0].to_dict() == {"line_item": "Revenue", "2023": "1,200"}


def test_drop_exact_duplicate_rows_keeps_first_occurrence_only():
    df = pd.DataFrame(
        [
            {"line_item": "Revenue", "2023": 1200},
            {"line_item": "Revenue", "2023": 1200},
            {"line_item": "Revenue", "2023": 1300},
        ]
    )

    cleaned = drop_exact_duplicate_rows(df)

    assert cleaned.to_dict("records") == [
        {"line_item": "Revenue", "2023": 1200},
        {"line_item": "Revenue", "2023": 1300},
    ]


def test_normalize_string_value_strips_and_collapses_whitespace():
    assert normalize_string_value("  Total    Revenue \n FY2023  ") == "Total Revenue FY2023"
    assert normalize_string_value(1200) == 1200


def test_normalize_missing_value_converts_obvious_blank_like_values():
    for value in ["", "   ", "-", "—", "–", "N/A", "NA", "na", "n/a", "None", "none", "NULL", "null"]:
        assert normalize_missing_value(value) is None

    assert normalize_missing_value("Revenue") == "Revenue"


def test_clean_numeric_value_converts_currency_and_comma_strings():
    assert clean_numeric_value("$1,200") == 1200
    assert clean_numeric_value("1,200") == 1200
    assert clean_numeric_value(" 153000 ") == 153000
    assert clean_numeric_value("€2,500") == 2500
    assert clean_numeric_value("£2,500") == 2500


def test_clean_numeric_value_strips_known_currency_codes_only():
    assert clean_numeric_value("USD 1,200") == 1200
    assert clean_numeric_value("1,200 USD") == 1200
    assert clean_numeric_value("JOD 1,200") == 1200
    assert clean_numeric_value("1,200 JOD") == 1200
    assert clean_numeric_value("ABC 100") == "ABC 100"
    assert clean_numeric_value("XYZ 1,200") == "XYZ 1,200"


def test_clean_numeric_value_converts_parenthetical_negatives():
    assert clean_numeric_value("(5,200)") == -5200
    assert clean_numeric_value("($1,250)") == -1250


def test_clean_numeric_value_preserves_non_numeric_text():
    assert clean_numeric_value("Total Revenue") == "Total Revenue"
    assert clean_numeric_value("Q1 2023") == "Q1 2023"
    assert clean_numeric_value(5200) == 5200


def test_headers_are_normalized_without_semantic_mapping():
    df = pd.DataFrame(columns=[" Total Revenue ($M) ", "Cash & Equivalents USD"])

    cleaned = normalize_headers(df)

    assert list(cleaned.columns) == ["total revenue", "cash and equivalents"]
    assert normalize_header_text("Sales") == "sales"
    assert normalize_header_text("Sales") != "revenue"
    assert normalize_header_text("Operating Income") == "operating income"
    assert normalize_header_text("Operating Income") != "ebit"
    assert normalize_header_text("Total Revenue") == "total revenue"
    assert normalize_header_text("Total Revenue") != "revenue"


def test_header_punctuation_is_normalized_mechanically():
    assert normalize_header_text("Total_Revenue") == "total revenue"
    assert normalize_header_text("Total-Revenue") == "total revenue"
    assert normalize_header_text("Total/Revenue") == "total revenue"
    assert normalize_header_text("Total.Revenue") == "total revenue"
    assert normalize_header_text("Shareholders' Equity") == "shareholders equity"


def test_header_unit_noise_is_removed_mechanically():
    assert normalize_header_text("Revenue ($MM)") == "revenue"
    assert normalize_header_text("Revenue ($M)") == "revenue"
    assert normalize_header_text("Revenue US Dollars") == "revenue"
    assert normalize_header_text("Revenue USD") == "revenue"
    assert normalize_header_text("Revenue millions") == "revenue"
    assert normalize_header_text("Revenue thousands") == "revenue"
    assert normalize_header_text("Revenue in millions") == "revenue"
    assert normalize_header_text("Revenue in thousands") == "revenue"


def test_period_labels_normalize_obvious_annual_periods_and_preserve_quarters():
    assert normalize_period_label("FY2023") == "2023"
    assert normalize_period_label("FY 2023") == "2023"
    assert normalize_period_label("as of 2021") == "2021"
    assert normalize_period_label("As of 2021") == "2021"
    assert normalize_period_label("as of Dec 31, 2021") == "2021"
    assert normalize_period_label("As of December 31, 2021") == "2021"
    assert normalize_period_label("2021A") == "2021"
    assert normalize_period_label("2022A") == "2022"
    assert normalize_period_label("FY2021A") == "2021"
    assert normalize_period_label("FY 2021A") == "2021"
    assert normalize_period_label("2024E") == "2024E"
    assert normalize_period_label("2025F") == "2025F"
    assert normalize_period_label("Dec-2022") == "2022"
    assert normalize_period_label("December 2022") == "2022"
    assert normalize_period_label("Q1 2023") == "Q1 2023"
    assert normalize_period_label("13/14/2022") == "13/14/2022"


def test_run_mechanical_cleaning_drops_exact_duplicate_rows_only():
    df = pd.DataFrame(
        {
            "Line Item": ["Sales", " Sales ", "Operating Income"],
            "2023": ["$1,200", " $1,200 ", "$500"],
        }
    )

    result = run_mechanical_cleaning(df)

    cleaned_df = result["cleaned_df"]
    assert cleaned_df.to_dict("records") == [
        {"line item": "Sales", "2023": 1200},
        {"line item": "Operating Income", "2023": 500},
    ]
    assert result["audit_log"]["duplicate_rows_dropped_count"] == 1


def test_run_mechanical_cleaning_does_not_drop_or_merge_duplicate_period_columns():
    df = pd.DataFrame(
        [
            ["Revenue", "$1,200", "$1,250"],
            ["Operating Income", "$500", "$550"],
        ],
        columns=["Line Item", "2023", "2023"],
    )

    result = run_mechanical_cleaning(df)

    cleaned_df = result["cleaned_df"]
    assert list(cleaned_df.columns) == ["line item", "2023", "2023"]
    assert cleaned_df.shape == (2, 3)
    assert result["audit_log"]["columns_dropped_count"] == 0


def test_run_mechanical_cleaning_returns_cleaned_df_and_audit_log():
    df = pd.DataFrame(
        {
            " Line Item ": [" Revenue  ", "FY2023", "  ", None],
            " Total Revenue ($M) ": [" $1,200 ", "(5,200)", "-", None],
            " Empty ": ["", " ", "—", None],
        }
    )

    result = run_mechanical_cleaning(df)

    assert set(result.keys()) == {"cleaned_df", "audit_log"}

    cleaned_df = result["cleaned_df"]
    assert list(cleaned_df.columns) == ["line item", "total revenue"]
    assert cleaned_df.to_dict("records") == [
        {"line item": "Revenue", "total revenue": 1200},
        {"line item": "2023", "total revenue": -5200},
    ]

    audit_log = result["audit_log"]
    assert audit_log["rows_dropped_count"] == 2
    assert audit_log["columns_dropped_count"] == 1
    assert audit_log["duplicate_rows_dropped_count"] == 0
    assert audit_log["headers_normalized"] == [
        {"original": " Line Item ", "normalized": "line item"},
        {"original": " Total Revenue ($M) ", "normalized": "total revenue"},
    ]
    assert audit_log["missing_values_normalized_count"] == 0
    assert audit_log["numeric_values_converted_count"] == 2
    assert audit_log["period_labels_normalized_count"] == 1
