"""Lightweight audit structures for cleaning steps."""

from dataclasses import dataclass, field


@dataclass
class MechanicalAuditLog:
    """Summary of conservative mechanical cleaning changes."""

    rows_dropped_count: int = 0
    columns_dropped_count: int = 0
    duplicate_rows_dropped_count: int = 0
    headers_normalized: list[dict[str, str]] = field(default_factory=list)
    missing_values_normalized_count: int = 0
    numeric_values_converted_count: int = 0
    period_labels_normalized_count: int = 0

    def as_dict(self) -> dict:
        """Return a serializable audit summary."""
        return {
            "rows_dropped_count": self.rows_dropped_count,
            "columns_dropped_count": self.columns_dropped_count,
            "duplicate_rows_dropped_count": self.duplicate_rows_dropped_count,
            "headers_normalized": self.headers_normalized,
            "missing_values_normalized_count": self.missing_values_normalized_count,
            "numeric_values_converted_count": self.numeric_values_converted_count,
            "period_labels_normalized_count": self.period_labels_normalized_count,
        }
