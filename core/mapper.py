"""
Mapper for translating mechanically-cleaned financial data to standard field names.

This module provides safe, conservative mapping of normalized column names
to standard financial field names. It does not apply business logic or
statement-specific transformations beyond name mapping.
"""

from core.mappings import (
    PERIOD_MAP,
    STATEMENT_MAPPINGS,
    REVIEW_ONLY_LABELS,
)


def get_mapping_for_statement(statement_type):
    """
    Get the combined mapping (PERIOD_MAP + statement-specific map) for a statement type.
    
    Parameters
    ----------
    statement_type : str
        The statement type key ('income', 'balance', 'cashflow').
    
    Returns
    -------
    dict
        A combined mapping dictionary including both PERIOD_MAP and statement-specific mappings.
    """
    normalized = str(statement_type).lower().strip()
    
    # Determine which statement mapping to use
    statement_map = {}
    if "income" in normalized:
        statement_map = STATEMENT_MAPPINGS.get("income", {})
    elif "balance" in normalized:
        statement_map = STATEMENT_MAPPINGS.get("balance", {})
    elif "cashflow" in normalized or "cash flow" in normalized:
        statement_map = STATEMENT_MAPPINGS.get("cashflow", {})
    
    # Return combined mapping: period map + statement map
    # (statement map takes precedence if there are overlaps)
    return {**PERIOD_MAP, **statement_map}


def map_column_name(normalized_name, statement_type):
    """
    Map a normalized column name to a standard financial field name.
    
    Safe mapping rules:
    1. If the name is in REVIEW_ONLY_LABELS, keep it unchanged.
    2. If the name is in the combined mapping for the statement type, apply the mapping.
    3. Otherwise, keep the normalized name unchanged.
    
    Parameters
    ----------
    normalized_name : str
        A mechanically-normalized column name (lowercase, spaces collapsed, etc.).
    statement_type : str
        The statement type ('income', 'balance', 'cashflow').
    
    Returns
    -------
    str
        The mapped field name or the original normalized name if no mapping exists.
    """
    # Preserve review-only labels
    if normalized_name in REVIEW_ONLY_LABELS:
        return normalized_name
    
    # Get the mapping for this statement type
    mapping = get_mapping_for_statement(statement_type)
    
    # Return mapped name or original if not in mapping
    return mapping.get(normalized_name, normalized_name)


def apply_statement_mappings(df, statement_type):
    """
    Apply safe column name mappings to a mechanically-cleaned DataFrame.
    
    This function translates normalized column names to standard financial
    field names without applying any business rules or transformations.
    
    Parameters
    ----------
    df : pandas.DataFrame
        A mechanically-cleaned DataFrame (typically output from mechanical_clean).
    statement_type : str
        The statement type ('income', 'balance', 'cashflow').
    
    Returns
    -------
    pandas.DataFrame
        DataFrame with mapped column names.
    """
    if df is None or len(df) == 0:
        return df
    
    mapped_df = df.copy()
    
    # Map each column name
    mapped_df.columns = [
        map_column_name(col, statement_type)
        for col in mapped_df.columns
    ]
    
    return mapped_df
