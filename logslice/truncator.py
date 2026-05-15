"""LogTruncator — trim oversized field values in log entries."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional


class LogTruncator:
    """Truncate string field values that exceed a maximum length.

    Parameters
    ----------
    max_length:
        Maximum number of characters allowed for any watched field.
        Must be a positive integer.
    suffix:
        String appended to truncated values to signal the truncation.
        Defaults to ``'...'``.
    """

    def __init__(self, max_length: int = 200, suffix: str = "...") -> None:
        if max_length <= 0:
            raise ValueError("max_length must be a positive integer")
        self._max_length = max_length
        self._suffix = suffix
        self._fields: List[str] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def max_length(self) -> int:
        return self._max_length

    @property
    def suffix(self) -> str:
        return self._suffix

    @property
    def fields(self) -> List[str]:
        return list(self._fields)

    # ------------------------------------------------------------------
    # Builder
    # ------------------------------------------------------------------

    def add_field(self, field: str) -> "LogTruncator":
        """Register *field* for truncation.  Returns *self* for chaining."""
        field = field.strip()
        if not field:
            raise ValueError("field name must not be empty or whitespace")
        if field not in self._fields:
            self._fields.append(field)
        return self

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    def _truncate_value(self, value: Any) -> Any:
        """Return truncated *value* if it is a string exceeding max_length."""
        if not isinstance(value, str):
            return value
        if len(value) <= self._max_length:
            return value
        cut = self._max_length - len(self._suffix)
        if cut < 0:
            cut = 0
        return value[:cut] + self._suffix

    def apply(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Return a new entry dict with registered fields truncated."""
        result = dict(entry)
        for field in self._fields:
            if field in result:
                result[field] = self._truncate_value(result[field])
        return result

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    def stream(
        self, entries: Iterable[Dict[str, Any]]
    ) -> Iterator[Dict[str, Any]]:
        """Yield truncated copies of every entry in *entries*."""
        for entry in entries:
            yield self.apply(entry)
