"""LogPivot – reshape log entries by pivoting a field's values into columns."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Optional


class LogPivot:
    """Pivot log entries so that distinct values of *row_field* become rows
    and distinct values of *col_field* become columns.

    Parameters
    ----------
    row_field:  field whose value identifies each row (e.g. ``"host"``)
    col_field:  field whose value becomes a column name (e.g. ``"level"``)
    value_field: field to aggregate per cell (e.g. ``"count"``).
                 When *None* the cell value is the number of matching entries.
    agg:        aggregation callable ``(current_cell_value, entry) -> new_value``.
                Defaults to a simple counter.
    default_row: label used when *row_field* is absent.
    default_col: label used when *col_field* is absent.
    """

    def __init__(
        self,
        row_field: str = "host",
        col_field: str = "level",
        value_field: Optional[str] = None,
        agg: Optional[Callable[[Any, Dict], Any]] = None,
        default_row: str = "unknown",
        default_col: str = "unknown",
    ) -> None:
        if not row_field or not row_field.strip():
            raise ValueError("row_field must be a non-empty string")
        if not col_field or not col_field.strip():
            raise ValueError("col_field must be a non-empty string")

        self._row_field = row_field
        self._col_field = col_field
        self._value_field = value_field
        self._default_row = default_row
        self._default_col = default_col

        if agg is not None:
            self._agg = agg
        elif value_field is not None:
            self._agg = lambda cur, e: (cur or 0) + e.get(value_field, 0)
        else:
            self._agg = lambda cur, _e: (cur or 0) + 1

        # {row_key: {col_key: cell_value}}
        self._data: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._cols: List[str] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def row_field(self) -> str:
        return self._row_field

    @property
    def col_field(self) -> str:
        return self._col_field

    @property
    def value_field(self) -> Optional[str]:
        return self._value_field

    @property
    def default_row(self) -> str:
        return self._default_row

    @property
    def default_col(self) -> str:
        return self._default_col

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def feed(self, entries: Iterable[Dict]) -> "LogPivot":
        """Ingest *entries* and update the internal pivot table."""
        for entry in entries:
            row_key = str(entry.get(self._row_field, self._default_row))
            col_key = str(entry.get(self._col_field, self._default_col))
            if col_key not in self._cols:
                self._cols.append(col_key)
            current = self._data[row_key].get(col_key)
            self._data[row_key][col_key] = self._agg(current, entry)
        return self

    def columns(self) -> List[str]:
        """Return the ordered list of column names seen so far."""
        return list(self._cols)

    def rows(self) -> List[str]:
        """Return the ordered list of row keys seen so far."""
        return list(self._data.keys())

    def table(self, fill: Any = 0) -> List[Dict[str, Any]]:
        """Return the pivot table as a list of dicts.

        Each dict has the *row_field* key plus one key per column.
        Missing cells are filled with *fill*.
        """
        cols = self.columns()
        result = []
        for row_key, cells in self._data.items():
            record: Dict[str, Any] = {self._row_field: row_key}
            for col in cols:
                record[col] = cells.get(col, fill)
            result.append(record)
        return result

    def cell(self, row: str, col: str, fill: Any = 0) -> Any:
        """Return the value for a single *row* / *col* cell."""
        return self._data.get(row, {}).get(col, fill)

    def reset(self) -> "LogPivot":
        """Clear all accumulated data."""
        self._data.clear()
        self._cols.clear()
        return self
