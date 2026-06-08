"""Route definitions for the Flask application."""

import math
from typing import Any

import pandas as pd
from flask import Blueprint, render_template, request

from cleaning.ingest import IngestionError, read_uploaded_file


bp = Blueprint("web", __name__)

PREVIEW_ROW_LIMIT = 50
STATEMENTS = [
    {
        "key": "income",
        "field_name": "income_statement",
        "label": "Income Statement",
        "panel_id": "panel-income",
        "tab_id": "tab-income",
    },
    {
        "key": "balance",
        "field_name": "balance_sheet",
        "label": "Balance Sheet",
        "panel_id": "panel-balance",
        "tab_id": "tab-balance",
    },
    {
        "key": "cash-flow",
        "field_name": "cash_flow_statement",
        "label": "Cash Flow Statement",
        "panel_id": "panel-cash-flow",
        "tab_id": "tab-cash-flow",
    },
]


def _render_cell_value(value: Any) -> str:
    if value is None:
        return ""
    try:
        if isinstance(value, float) and math.isnan(value):
            return ""
    except TypeError:
        pass
    return str(value)


def build_table_preview(df: pd.DataFrame, row_limit: int = PREVIEW_ROW_LIMIT) -> dict:
    """Convert a DataFrame preview into simple Jinja-renderable table data."""
    preview_df = df.head(row_limit)
    return {
        "headers": [_render_cell_value(column) for column in preview_df.columns],
        "rows": [
            [_render_cell_value(value) for value in row]
            for row in preview_df.itertuples(index=False, name=None)
        ],
        "row_count": len(df.index),
        "column_count": len(df.columns),
        "preview_row_count": len(preview_df.index),
        "is_truncated": len(df.index) > row_limit,
    }


def _empty_statement_previews() -> dict:
    return {
        statement["key"]: {
            "filename": None,
            "error": None,
            "table": None,
        }
        for statement in STATEMENTS
    }


def _build_upload_previews(uploaded_files) -> dict:
    previews = _empty_statement_previews()

    for statement in STATEMENTS:
        field_name = statement["field_name"]
        uploaded_file = uploaded_files.get(field_name)

        if not uploaded_file or not uploaded_file.filename:
            continue

        try:
            df = read_uploaded_file(uploaded_file, filename=uploaded_file.filename)
            previews[statement["key"]] = {
                "filename": uploaded_file.filename,
                "error": None,
                "table": build_table_preview(df),
            }
        except IngestionError as exc:
            previews[statement["key"]] = {
                "filename": uploaded_file.filename,
                "error": str(exc),
                "table": None,
            }

    return previews


@bp.route("/")
def dashboard():
    """Render the dashboard placeholder."""
    return render_template("dashboard.html", active_page="dashboard")


@bp.route("/data", methods=["GET", "POST"])
def data():
    """Render the data intake page and raw upload previews."""
    previews = _empty_statement_previews()
    if request.method == "POST":
        previews = _build_upload_previews(request.files)

    return render_template(
        "data.html",
        active_page="data",
        statements=STATEMENTS,
        previews=previews,
    )


@bp.route("/data/cleaned")
def cleaned_data():
    """Render the cleaned data preview placeholder."""
    return render_template("cleaned_data.html", active_page="data")


@bp.route("/companies")
def companies():
    """Render the companies placeholder."""
    return render_template("companies.html", active_page="companies")


@bp.route("/analysis")
def analysis():
    """Render the analysis placeholder."""
    return render_template("analysis.html", active_page="analysis")
