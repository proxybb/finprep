"""Route definitions for the Flask application."""

import json
import math
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from cleaning.approvals import apply_balance_sheet_approvals
from cleaning.ingest import IngestionError, read_uploaded_file
from cleaning.identities import check_balance_sheet_identity
from cleaning.mapping import MAPPING_METADATA_COLUMNS, map_statement_rows
from cleaning.mechanical import run_mechanical_cleaning
from cleaning.orientation import normalize_orientation
from cleaning.schema import REQUIRED_BALANCE_SHEET_FIELDS, validate_balance_sheet_schema
from cleaning.table_boundary import normalize_table_boundary


bp = Blueprint("web", __name__)

PREVIEW_ROW_LIMIT = 50
TEMP_UPLOAD_ROOT = Path("data/temp_uploads")
UPLOAD_METADATA_FILENAME = "metadata.json"
BALANCE_SHEET_APPROVAL_KEY = "balance_sheet"
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


def _is_safe_upload_dir(path: Path) -> bool:
    try:
        upload_root = TEMP_UPLOAD_ROOT.resolve()
        resolved_path = path.resolve()
    except OSError:
        return False

    return resolved_path.parent == upload_root


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


def _clear_upload_state(upload_id: str | None) -> None:
    session.pop("current_upload_id", None)
    if not upload_id:
        return

    upload_dir = _upload_dir(upload_id)
    if not _is_safe_upload_dir(upload_dir) or not upload_dir.exists():
        return

    if upload_dir.is_dir():
        shutil.rmtree(upload_dir)


def _balance_sheet_approvals(metadata: dict) -> list[dict[str, Any]]:
    approvals = metadata.get("approvals", {}).get(BALANCE_SHEET_APPROVAL_KEY, [])
    if isinstance(approvals, list):
        return approvals
    return []


def _store_balance_sheet_approval(
    upload_id: str | None,
    row_position: Any,
    canonical_label: Any,
) -> None:
    if not upload_id:
        return
    metadata = _load_upload_metadata(upload_id)
    if not metadata.get("statements", {}).get("balance"):
        return

    try:
        parsed_row_position = int(row_position)
    except (TypeError, ValueError):
        return
    if parsed_row_position < 0 or canonical_label not in REQUIRED_BALANCE_SHEET_FIELDS:
        return

    approvals = metadata.setdefault("approvals", {}).setdefault(
        BALANCE_SHEET_APPROVAL_KEY,
        [],
    )
    approval = {
        "row_position": parsed_row_position,
        "canonical_label": canonical_label,
    }
    approvals[:] = [
        existing
        for existing in approvals
        if existing.get("row_position") != parsed_row_position
    ]
    approvals.append(approval)
    _save_upload_metadata(upload_id, metadata)


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


def _is_missing_cell(value: Any) -> bool:
    if value is None:
        return True
    try:
        if isinstance(value, float) and math.isnan(value):
            return True
    except TypeError:
        pass
    return False


def build_table_preview(
    df: pd.DataFrame,
    row_limit: int = PREVIEW_ROW_LIMIT,
    first_column_header: str | None = None,
    highlight_missing: bool = False,
) -> dict:
    """Convert a DataFrame preview into simple Jinja-renderable table data."""
    preview_df = df.head(row_limit)
    headers = [_render_cell_value(column) for column in preview_df.columns]
    if first_column_header is not None and headers:
        headers[0] = first_column_header

    return {
        "headers": headers,
        "rows": [
            [
                {
                    "value": _render_cell_value(value),
                    "is_missing": highlight_missing and _is_missing_cell(value),
                }
                for value in row
            ]
            for row in preview_df.itertuples(index=False, name=None)
        ],
        "row_count": len(df.index),
        "column_count": len(df.columns),
        "preview_row_count": len(preview_df.index),
        "is_truncated": len(df.index) > row_limit,
    }


def _has_display_value(value: Any) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass
    return str(value).strip() != ""


def _balance_sheet_display_df(mapped_df: pd.DataFrame) -> pd.DataFrame:
    """Build a user-facing Balance Sheet preview without mapping metadata columns."""
    display_df = mapped_df.drop(
        columns=[column for column in MAPPING_METADATA_COLUMNS if column in mapped_df.columns],
        errors="ignore",
    ).copy()
    if display_df.empty or len(display_df.columns) == 0:
        return display_df

    label_column = display_df.columns[0]
    if "display_label" not in mapped_df.columns:
        return display_df

    display_df[label_column] = [
        display_label if _has_display_value(display_label) else existing_label
        for existing_label, display_label in zip(
            display_df[label_column].tolist(),
            mapped_df["display_label"].tolist(),
        )
    ]
    return display_df


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
            boundary_result = normalize_table_boundary(cleaned_df)
            orientation_result = normalize_orientation(boundary_result.dataframe)
            preview_df = orientation_result.dataframe
            schema_validation = None
            identity_check = None
            display_df = preview_df
            if statement["field_name"] == "balance_sheet":
                preview_df, _mapping_audit = map_statement_rows(preview_df, "balance_sheet")
                preview_df = apply_balance_sheet_approvals(
                    preview_df,
                    _balance_sheet_approvals(metadata),
                )
                schema_validation = validate_balance_sheet_schema(preview_df)
                identity_check = check_balance_sheet_identity(preview_df, schema_validation)
                display_df = _balance_sheet_display_df(preview_df)

            results[statement["key"]] = {
                "filename": metadata_entry["filename"],
                "error": None,
                "table": build_table_preview(
                    display_df,
                    first_column_header="",
                    highlight_missing=True,
                ),
                "orientation": {
                    "status": orientation_result.status,
                    "action": orientation_result.action,
                    "confidence": orientation_result.confidence,
                    "message": orientation_result.message,
                },
                "schema_validation": schema_validation,
                "identity_check": identity_check,
            }
        except (IngestionError, OSError, KeyError, ValueError) as exc:
            results[statement["key"]] = {
                "filename": metadata_entry.get("filename", "uploaded file"),
                "error": str(exc),
                "table": None,
                "orientation": None,
                "schema_validation": None,
                "identity_check": None,
            }

    return results


@bp.route("/")
def dashboard():
    """Render the dashboard placeholder."""
    return render_template("dashboard.html", active_page="dashboard")


@bp.route("/data")
def data():
    """Redirect to the upload/raw preview step of the data workflow."""
    return redirect(url_for("web.data_upload"))


@bp.route("/data/upload", methods=["GET", "POST"])
def data_upload():
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


@bp.route("/data/clear", methods=["POST"])
def clear_uploaded_data():
    """Clear the current temporary upload state and return to data intake."""
    _clear_upload_state(session.get("current_upload_id"))
    return redirect(url_for("web.data"))


@bp.route("/data/review/approve", methods=["POST"])
def approve_balance_sheet_review_candidate():
    """Approve a narrow Balance Sheet review candidate for the current upload."""
    if request.form.get("statement_type") == "balance_sheet":
        _store_balance_sheet_approval(
            session.get("current_upload_id"),
            request.form.get("row_position"),
            request.form.get("canonical_label"),
        )
    return redirect(url_for("web.cleaned_data"))


@bp.route("/data/cleaned")
def cleaned_data():
    """Render cleaned and orientation-normalized previews for uploaded files."""
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
