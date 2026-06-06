"""
Mechanical cleaning layer for financial statements.

Handles only format and structure normalization:
- Row/column cleanup
- Column name normalization
- Period standardization
- Numeric value formatting

Does NOT apply statement-specific mappings or business rules.
"""

import re
from io import BytesIO

import pandas as pd


# Regex patterns for unit removal
_UNIT_PATTERN = re.compile(
    r"\b(?:us dollars|in millions|in thousands|millions|thousands|usd)\b|\$mm|\$m|\$",
    re.IGNORECASE,
)

_UNIT_PARENS_PATTERN = re.compile(
    r"\(\s*(?:\$mm|\$m|\$|usd|us dollars|in millions|millions|in thousands|thousands)\s*\)",
    re.IGNORECASE,
)


def normalize_column_name(column_name):
    """
    Normalize only the mechanics of a column label, not its accounting meaning.
    
    - Convert to lowercase
    - Strip whitespace
    - Replace & with 'and'
    - Remove punctuation/special characters
    - Remove unit text (USD, $, $M, $MM, in millions, etc.)
    - Collapse repeated spaces
    """
    normalized = str(column_name).lower().strip()
    
    # Remove units in parentheses like "($ millions)"
    normalized = _UNIT_PARENS_PATTERN.sub(" ", normalized)
    
    # Replace ampersand
    normalized = normalized.replace("&", "and")
    
    # Replace underscores, dashes, slashes, periods, commas with spaces
    normalized = re.sub(r"[_\-/.,\r\n]+", " ", normalized)
    
    # Remove apostrophes
    normalized = re.sub(r"['\u2019]", "", normalized)
    
    # Remove standalone unit text
    normalized = _UNIT_PATTERN.sub(" ", normalized)
    
    # Collapse repeated whitespace
    normalized = re.sub(r"\s+", " ", normalized)
    
    return normalized.strip()


def standardize_period_value(value):
    """
    Convert period labels to a year string or keep quarterly-looking periods.
    
    Examples:
    - FY2023 → 2023
    - 2021A → 2021
    - Dec-2022 → 2022
    - Q1 2023 → Q1 2023 (kept as is for now)
    """
    if pd.isna(value):
        return value
    
    stripped_value = str(value).strip()
    
    # If it looks quarterly, keep it as is
    if looks_quarterly_period(value):
        return stripped_value
    
    # Extract any 4-digit year
    year_match = re.search(r"(?<!\d)(\d{4})(?!\d)", stripped_value)
    if year_match:
        return year_match.group(1)
    
    # Return as is if no 4-digit year found
    return stripped_value


def looks_quarterly_period(value):
    """Return True when a period label appears to describe quarterly data."""
    if pd.isna(value):
        return False
    
    stripped_value = str(value).lower().strip()
    return bool(
        re.search(r"\bq[1-4]\b", stripped_value)
        or "quarter ended" in stripped_value
        or "three months ended" in stripped_value
        or "three-month period" in stripped_value
        or "3 months ended" in stripped_value
    )


def clean_numeric_value(value):
    """
    Convert obvious financial number formatting.
    
    - Remove currency symbols
    - Remove commas
    - Convert parentheses negatives: (5200) → -5200
    - Convert text numbers to floats
    - Convert blank/none/n/a/"-" to None
    """
    if pd.isna(value):
        return None
    
    # Already numeric
    if isinstance(value, (int, float)):
        return value
    
    stripped_value = str(value).strip()
    
    # Treat empty and special strings as None
    if stripped_value.lower() in {"", "none", "nan", "n/a", "-"}:
        return None
    
    # Detect and extract negative values in parentheses
    is_negative = False
    numeric_text = stripped_value
    if numeric_text.startswith("(") and numeric_text.endswith(")"):
        is_negative = True
        numeric_text = numeric_text[1:-1].strip()
    
    # Remove currency symbols
    numeric_text = re.sub(r"[$£€]", "", numeric_text)
    
    # Remove commas
    numeric_text = numeric_text.replace(",", "").strip()
    
    # Try to convert to float
    try:
        number = float(numeric_text)
    except ValueError:
        # If not convertible, return original value (user will see it in preview)
        return value
    
    # Apply negative sign if detected
    if is_negative:
        return -number
    
    return number


def mechanical_clean(df, statement_type=None):
    """
    Apply mechanical cleaning to a financial statement DataFrame.
    
    Parameters
    ----------
    df : pandas.DataFrame
        The input financial statement data.
    statement_type : str, optional
        Type of statement ('income', 'balance_sheet', 'cash_flow').
        Not used for mechanical cleaning; reserved for future statement-specific logic.
    
    Returns
    -------
    pandas.DataFrame
        Cleaned DataFrame with normalized columns, periods, and numeric values.
    
    Notes
    -----
    This function does NOT apply statement-specific mappings or business rules.
    It only normalizes format and structure.
    """
    if df is None or len(df) == 0:
        return df
    
    cleaned_df = df.copy()
    
    # Drop fully blank rows and columns
    cleaned_df = cleaned_df.dropna(how="all")
    cleaned_df = cleaned_df.dropna(axis=1, how="all")
    
    # Normalize column names mechanically
    cleaned_df.columns = [normalize_column_name(col) for col in cleaned_df.columns]
    
    # Standardize period values if period column exists
    if "period" in cleaned_df.columns:
        cleaned_df["period"] = cleaned_df["period"].apply(standardize_period_value)
    
    # Clean numeric values in all columns (will convert only if looks numeric)
    for col in cleaned_df.columns:
        # Skip period/label columns
        if col not in {"period", "company", "name", "account", "description", "item"}:
            cleaned_df[col] = cleaned_df[col].apply(clean_numeric_value)
    
    return cleaned_df


def read_uploaded_file(file_stream, filename):
    """
    Read an uploaded CSV or Excel file into a pandas DataFrame.
    
    Parameters
    ----------
    file_stream : file-like object
        The uploaded file object.
    filename : str
        The filename (used to determine file type).
    
    Returns
    -------
    pandas.DataFrame or None
        The DataFrame if successful, None if error.
    """
    try:
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(file_stream)
        elif filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_stream)
        else:
            return None
        
        return df
    except Exception:
        return None
