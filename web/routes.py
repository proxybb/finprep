"""Route definitions for the Flask application."""

import json
import math
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from flask import Blueprint, render_template, request, session
from werkzeug.utils import secure_filename

from cleaning.ingest import IngestionError, read_uploaded_file
from cleaning.mechanical import run_mechanical_cleaning


bp = Blueprint("web", __name__)

PREVIEW_ROW_LIMIT = 50
TEMP_UPLOAD_ROOT = Path("data/temp_uploads")
UPLOAD_METADATA_FILENAME = "metadata.json"
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


def _upload_dir(upload_id: str) -> Path:
    return TEMP_UPLOAD_ROOT / upload_id


def _metadata_path(upload_id: str) -> Path:
    return _upload_dir(upload_id) / UPLOAD_METADATA_FILENAME


def _load_upload_metadata(upload_id: str | None) -> dict:
    if not upload_id:
        return {}

    path = _metadata_path(upload_id)
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_upload_metadata(upload_id: str, metadata: dict) -> None:
    upload_dir = _upload_dir(upload_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    _metadata_path(upload_id).write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _save_uploaded_file(upload_id: str, statement: dict, uploaded_file) -> dict:
    upload_dir = _upload_dir(upload_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = secure_filename(uploaded_file.filename or "upload")
    if not safe_filename:
        safe_filename = "upload"

    stored_filename = f"{statement['field_name']}-{safe_filename}"
    destination = upload_dir / stored_filename
    uploaded_file.seek(0)
    uploaded_file.save(destination)

    return {
        "filename": uploaded_file.filename,
        "stored_filename": stored_filename,
        "field_name": statement["field_name"],
    }


def _read_saved_statement(upload_id: str, metadata_entry: dict) -> pd.DataFrame:
    stored_path = _upload_dir(upload_id) / metadata_entry["stored_filename"]
    with stored_path.open("rb") as file:
        return read_uploaded_file(file, filename=metadata_entry["filename"])


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
    metadata = {"statements": {}}
    upload_id = uuid4().hex

    for statement in STATEMENTS:
        field_name = statement["field_name"]
        uploaded_file = uploaded_files.get(field_name)

        if not uploaded_file or not uploaded_file.filename:
            continue

        try:
            df = read_uploaded_file(uploaded_file, filename=uploaded_file.filename)
            metadata["statements"][statement["key"]] = _save_uploaded_file(
                upload_id,
                statement,
                uploaded_file,
            )
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

    if metadata["statements"]:
        _save_upload_metadata(upload_id, metadata)
        session["current_upload_id"] = upload_id

    return previews


def _build_saved_upload_previews(upload_id: str | None) -> dict:
    previews = _empty_statement_previews()
    metadata = _load_upload_metadata(upload_id)
    saved_statements = metadata.get("statements", {})

    for statement in STATEMENTS:
        metadata_entry = saved_statements.get(statement["key"])
        if not metadata_entry:
            continue

        try:
            df = _read_saved_statement(upload_id, metadata_entry)
            previews[statement["key"]] = {
                "filename": metadata_entry["filename"],
                "error": None,
                "table": build_table_preview(df),
            }
        except (IngestionError, OSError, KeyError) as exc:
            previews[statement["key"]] = {
                "filename": metadata_entry.get("filename", "uploaded file"),
                "error": str(exc),
                "table": None,
            }

    return previews


def _build_cleaned_results(upload_id: str | None) -> dict:
    results = _empty_statement_previews()
    metadata = _load_upload_metadata(upload_id)
    saved_statements = metadata.get("statements", {})

    for statement in STATEMENTS:
        metadata_entry = saved_statements.get(statement["key"])
        if not metadata_entry:
            continue

        try:
            raw_df = _read_saved_statement(upload_id, metadata_entry)
            cleaning_result = run_mechanical_cleaning(raw_df)
            cleaned_df = cleaning_result["cleaned_df"]
            results[statement["key"]] = {
                "filename": metadata_entry["filename"],
                "error": None,
                "table": build_table_preview(cleaned_df),
                "audit_log": cleaning_result["audit_log"],
            }
        except (IngestionError, OSError, KeyError, ValueError) as exc:
            results[statement["key"]] = {
                "filename": metadata_entry.get("filename", "uploaded file"),
                "error": str(exc),
                "table": None,
                "audit_log": None,
            }

    return results


@bp.route("/")
def dashboard():
    """Render the dashboard placeholder."""
    return render_template("dashboard.html", active_page="dashboard")


@bp.route("/data", methods=["GET", "POST"])
def data():
    """Render the data intake page and raw upload previews."""
    if request.method == "POST":
        previews = _build_upload_previews(request.files)
    else:
        previews = _build_saved_upload_previews(session.get("current_upload_id"))

    return render_template(
        "data.html",
        active_page="data",
        statements=STATEMENTS,
        previews=previews,
    )


@bp.route("/data/cleaned")
def cleaned_data():
    """Render mechanically cleaned previews for the current uploaded files."""
    upload_id = session.get("current_upload_id")
    has_upload = bool(_load_upload_metadata(upload_id))
    results = _build_cleaned_results(upload_id) if has_upload else _empty_statement_previews()

    return render_template(
        "cleaned_data.html",
        active_page="data",
        statements=STATEMENTS,
        results=results,
        has_upload=has_upload,
    )


@bp.route("/companies")
def companies():
    """Render the companies placeholder."""
    return render_template("companies.html", active_page="companies")


@bp.route("/analysis")
def analysis():
    """Render the analysis placeholder."""
    return render_template("analysis.html", active_page="analysis")
