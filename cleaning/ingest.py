"""Raw file ingestion for uploaded CSV and Excel statements."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


class IngestionError(ValueError):
    """Base error for user-facing ingestion failures."""


class UnsupportedFileTypeError(IngestionError):
    """Raised when the uploaded filename has an unsupported extension."""


class EmptyUploadedFileError(IngestionError):
    """Raised when the uploaded file has no readable tabular data."""


class UnreadableUploadedFileError(IngestionError):
    """Raised when pandas cannot parse an uploaded file."""


def get_file_extension(filename: str | None) -> str:
    """Return the lowercase file extension for a filename."""
    if not filename:
        return ""
    return Path(filename).suffix.lower()


def is_supported_file(filename: str | None) -> bool:
    """Return True for supported CSV and Excel filenames."""
    return get_file_extension(filename) in SUPPORTED_EXTENSIONS


def _resolve_filename(file: Any, filename: str | None) -> str | None:
    if filename:
        return filename
    return getattr(file, "filename", None) or getattr(file, "name", None)


def _rewind_file(file: Any) -> None:
    if hasattr(file, "seek"):
        file.seek(0)


def _raise_if_empty(df: pd.DataFrame) -> None:
    if df.empty:
        raise EmptyUploadedFileError("The uploaded file is empty.")


def read_uploaded_file(file: Any, filename: str | None = None) -> pd.DataFrame:
    """Read a CSV or Excel upload into a raw pandas DataFrame."""
    resolved_filename = _resolve_filename(file, filename)
    extension = get_file_extension(resolved_filename)

    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            "Unsupported file type. Please upload a CSV or Excel file."
        )

    try:
        _rewind_file(file)
        if extension == ".csv":
            df = pd.read_csv(file, dtype=object, keep_default_na=False)
        else:
            df = pd.read_excel(file, dtype=object, keep_default_na=False)
        _raise_if_empty(df)
        return df
    except EmptyUploadedFileError:
        raise
    except EmptyDataError as exc:
        raise EmptyUploadedFileError("The uploaded file is empty.") from exc
    except (ParserError, UnicodeDecodeError, OSError, ValueError, ImportError) as exc:
        raise UnreadableUploadedFileError(
            "The uploaded file could not be read. Please check the file format."
        ) from exc
