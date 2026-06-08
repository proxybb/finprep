import re

import pandas as pd


IMPORTANT_COLUMNS_BY_STATEMENT = {
    "income": [
        "revenue",
        "cogs",
        "gross_profit",
        "ebit",
        "net_income",
    ],
    "balance": [
        "cash_and_equivalents",
        "accounts_receivable",
        "inventory",
        "current_assets",
        "total_assets",
        "accounts_payable",
        "current_liabilities",
        "total_liabilities",
        "total_equity",
    ],
    "cashflow": [
        "operating_cash_flow",
        "capital_expenditures",
        "free_cash_flow",
    ],
}

REQUIRED_COLUMNS = {
    "income": ["period", "revenue"],
    "balance": ["period", "current_assets", "current_liabilities"],
    "cashflow": ["period", "operating_cash_flow"],
}

REVIEW_ONLY_COLUMNS = {
    "depreciation and amortization",
    "depreciation and amortization expenses",
    "depreciation and amortisation",
    "depreciation and amortisation expenses",
    "gross margin",
    "receivables",
    "cash on hand",
    "accounts payable and accrued expenses",
    "adjusted ebitda",
    "adjusted free cash flow",
}


def get_statement_key(statement_type):
    statement_name = str(statement_type).lower()

    if "income" in statement_name:
        return "income"
    if "balance" in statement_name:
        return "balance"
    if "cashflow" in statement_name or "cash flow" in statement_name:
        return "cashflow"

    return "unknown"


def validate_required_columns(df, statement_type):
    """Return validation messages for statement-specific required columns."""
    if df is None:
        return [
            f"Required-column check skipped for {statement_type} because no data exists."
        ]

    statement_key = get_statement_key(statement_type)
    if statement_key == "unknown":
        return [
            f"Required-column check skipped for {statement_type} because the statement type is unknown."
        ]

    missing_columns = get_missing_required_columns(df, statement_type)
    if missing_columns:
        missing_list = ", ".join(missing_columns)
        return [
            f"Missing required columns in {statement_type}: {missing_list}. "
            "These fields are needed before saving or analysis."
        ]

    return [f"Required columns present for {statement_type}."]


def get_missing_required_columns(df, statement_type):
    """Return missing required columns for a supported statement type."""
    if df is None:
        return []

    statement_key = get_statement_key(statement_type)
    required_columns = REQUIRED_COLUMNS.get(statement_key)
    if not required_columns:
        return []

    existing_columns = set(df.columns)
    return [
        column for column in required_columns if column not in existing_columns
    ]


def find_duplicate_periods(df, statement_type):
    """Return validation messages about duplicate period rows."""
    if df is None:
        return [
            f"Duplicate-period check skipped for {statement_type} because no data exists."
        ]
    if "period" not in df.columns:
        return [
            f"Duplicate-period check skipped for {statement_type} because no period column exists."
        ]

    duplicate_periods = (
        df.loc[df["period"].duplicated(keep=False), "period"].dropna().unique()
    )
    if len(duplicate_periods) == 0:
        return [f"No duplicate periods found for {statement_type}."]

    duplicate_list = ", ".join(str(period) for period in duplicate_periods)
    return [
        f"Duplicate periods found in {statement_type}: {duplicate_list}. "
        "Review these rows before finalizing."
    ]


def _looks_quarterly_period(value):
    period_value = str(value).lower().strip()
    return bool(
        re.search(r"\bq[1-4]\b", period_value)
        or "quarter ended" in period_value
        or "three months ended" in period_value
        or "three-month period" in period_value
        or "3 months ended" in period_value
    )


def find_quarterly_periods(df, statement_type):
    """Return validation messages about quarterly-looking periods."""
    if df is None:
        return [
            f"Quarterly-period check skipped for {statement_type} because no data exists."
        ]
    if "period" not in df.columns:
        return [
            f"Quarterly-period check skipped for {statement_type} because no period column exists."
        ]

    quarterly_periods = df.loc[
        df["period"].apply(_looks_quarterly_period), "period"
    ].dropna().unique()
    if len(quarterly_periods) == 0:
        return [f"No quarterly periods found for {statement_type}."]

    quarterly_list = ", ".join(str(period) for period in quarterly_periods)
    return [
        f"Quarterly periods detected in {statement_type}: {quarterly_list}. "
        "v1 currently supports annual data only."
    ]


def _is_blank(value):
    if value is None or pd.isna(value):
        return True
    return isinstance(value, str) and value.strip() == ""


def find_missing_values(df, statement_type):
    """Return validation messages about missing values in important columns."""
    if df is None:
        return [
            f"Missing-value check skipped for {statement_type} because no data exists."
        ]
    if "period" not in df.columns:
        return [
            f"Missing-value check skipped for {statement_type} because no period column exists."
        ]

    statement_key = get_statement_key(statement_type)
    important_columns = IMPORTANT_COLUMNS_BY_STATEMENT.get(statement_key)
    if important_columns is None:
        return [
            f"Missing-value check skipped for {statement_type} because the statement type is unknown."
        ]

    existing_columns = [column for column in important_columns if column in df.columns]
    messages = []

    for _, row in df.iterrows():
        period = row.get("period")
        period_label = "unknown period" if _is_blank(period) else str(period)

        for column in existing_columns:
            if _is_blank(row.get(column)):
                messages.append(
                    f"Missing value in {statement_type}: {column} is blank "
                    f"for period {period_label}."
                )

    if messages:
        return messages

    return [
        f"No missing values found in important columns for {statement_type}."
    ]


def get_duplicate_period_rows(df):
    """Return rows whose period appears more than once, preserving original indexes."""
    if df is None or "period" not in df.columns:
        return pd.DataFrame()

    duplicate_mask = df["period"].duplicated(keep=False)
    return df.loc[duplicate_mask].copy()


def get_missing_value_locations(df, statement_type):
    """Return structured missing-value locations for important financial columns."""
    if df is None:
        return []

    statement_key = get_statement_key(statement_type)
    important_columns = IMPORTANT_COLUMNS_BY_STATEMENT.get(statement_key, [])
    existing_columns = [column for column in important_columns if column in df.columns]
    locations = []

    for row_index, row in df.iterrows():
        period = row.get("period", "unknown period")
        period_label = "unknown period" if _is_blank(period) else str(period)

        for column in existing_columns:
            if _is_blank(row.get(column)):
                locations.append(
                    {
                        "statement_type": statement_type,
                        "period": period_label,
                        "column": column,
                        "row_index": row_index,
                    }
                )

    return locations


def get_review_only_columns(df):
    """Return review-only or unmapped value-bearing columns preserved for review."""
    if df is None:
        return []

    review_only_columns = []
    for column in df.columns:
        normalized_column = str(column).lower().strip()
        if normalized_column in REVIEW_ONLY_COLUMNS:
            review_only_columns.append(column)

    return review_only_columns


def run_quality_checks(df, statement_type):
    """Run detection-only quality checks and return structured results."""
    duplicate_rows = get_duplicate_period_rows(df)
    missing_locations = get_missing_value_locations(df, statement_type)
    missing_required_columns = get_missing_required_columns(df, statement_type)
    review_only_columns = get_review_only_columns(df)

    messages = []
    messages.extend(validate_required_columns(df, statement_type))
    messages.extend(find_duplicate_periods(df, statement_type))
    messages.extend(find_quarterly_periods(df, statement_type))
    messages.extend(find_missing_values(df, statement_type))

    if review_only_columns:
        review_only_list = ", ".join(str(column) for column in review_only_columns)
        messages.append(
            f"Review-only columns found in {statement_type}: {review_only_list}. "
            "These columns were preserved because automatic mapping could be "
            "misleading."
        )
    else:
        messages.append(f"No review-only columns found for {statement_type}.")

    return {
        "statement_type": statement_type,
        "messages": messages,
        "duplicate_rows": duplicate_rows,
        "missing_locations": missing_locations,
        "missing_required_columns": missing_required_columns,
        "review_only_columns": review_only_columns,
    }


def _get_periods(df):
    return {
        str(period).strip()
        for period in df["period"].dropna()
        if str(period).strip() != ""
    }


def get_period_alignment_summary(income_df, balance_df, cashflow_df):
    """Return period alignment details across the three statements."""
    statements = [income_df, balance_df, cashflow_df]
    if any(df is None or "period" not in df.columns for df in statements):
        return {
            "income_periods": [],
            "balance_periods": [],
            "cashflow_periods": [],
            "aligned_periods": [],
            "missing_from_income": [],
            "missing_from_balance": [],
            "missing_from_cashflow": [],
        }

    income_periods = _get_periods(income_df)
    balance_periods = _get_periods(balance_df)
    cashflow_periods = _get_periods(cashflow_df)
    all_periods = income_periods | balance_periods | cashflow_periods
    aligned_periods = income_periods & balance_periods & cashflow_periods

    return {
        "income_periods": sorted(income_periods),
        "balance_periods": sorted(balance_periods),
        "cashflow_periods": sorted(cashflow_periods),
        "aligned_periods": sorted(aligned_periods),
        "missing_from_income": sorted(all_periods - income_periods),
        "missing_from_balance": sorted(all_periods - balance_periods),
        "missing_from_cashflow": sorted(all_periods - cashflow_periods),
    }


def get_aligned_periods(income_df, balance_df, cashflow_df):
    """Return periods shared by all three statements."""
    summary = get_period_alignment_summary(income_df, balance_df, cashflow_df)
    return summary["aligned_periods"]


def check_period_alignment(income_df, balance_df, cashflow_df):
    """Return validation messages about period alignment across statements."""
    if income_df is None or balance_df is None or cashflow_df is None:
        return [
            "Period alignment check skipped because one or more statements are missing."
        ]

    statements = [
        ("Income Statement", income_df),
        ("Balance Sheet", balance_df),
        ("Cash Flow Statement", cashflow_df),
    ]
    missing_period_columns = [
        statement_name
        for statement_name, df in statements
        if "period" not in df.columns
    ]
    if missing_period_columns:
        missing_list = ", ".join(missing_period_columns)
        return [
            "Period alignment check skipped because these statements are missing "
            f"the period column: {missing_list}."
        ]

    summary = get_period_alignment_summary(income_df, balance_df, cashflow_df)
    aligned_periods = summary["aligned_periods"]

    if (
        aligned_periods
        and not summary["missing_from_income"]
        and not summary["missing_from_balance"]
        and not summary["missing_from_cashflow"]
    ):
        shared_list = ", ".join(aligned_periods)
        return [f"Period alignment passed. Shared periods: {shared_list}."]

    messages = []
    missing_statement_messages = [
        ("Income Statement", summary["missing_from_income"]),
        ("Balance Sheet", summary["missing_from_balance"]),
        ("Cash Flow Statement", summary["missing_from_cashflow"]),
    ]
    for statement_name, missing_periods in missing_statement_messages:
        if missing_periods:
            missing_list = ", ".join(missing_periods)
            messages.append(
                f"Period alignment issue: {statement_name} is missing periods: "
                f"{missing_list}."
            )

    if aligned_periods:
        aligned_list = ", ".join(aligned_periods)
        messages.append(
            f"Aligned periods available for future saving/analysis: {aligned_list}."
        )
    else:
        messages.append(
            "Period alignment issue: no periods are shared across all three statements."
        )

    return messages
