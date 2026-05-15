"""LogFlattener – collapse nested dict fields into dot-notation keys."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional


class LogFlattener:
    """Flatten nested dictionary entries into a single-level dict.

    Nested keys are joined with *separator* (default ``"."``).
    Only the fields listed in *fields* are flattened; when *fields* is
    ``None`` every dict-valued field is flattened.

    Example
    -------
    >>> entry = {"level": "INFO", "ctx": {"user": "alice", "req": {"id": 1}}}
    >>> list(LogFlattener().apply([entry]))[0]
    {'level': 'INFO', 'ctx.user': 'alice', 'ctx.req.id': 1}
    """

    def __init__(
        self,
        fields: Optional[List[str]] = None,
        separator: str = ".",
        max_depth: int = 0,
    ) -> None:
        if not separator:
            raise ValueError("separator must be a non-empty string")
        if max_depth < 0:
            raise ValueError("max_depth must be >= 0 (0 means unlimited)")
        self._fields: Optional[List[str]] = list(fields) if fields is not None else None
        self._separator = separator
        self._max_depth = max_depth

    # ------------------------------------------------------------------
    # public properties
    # ------------------------------------------------------------------

    @property
    def separator(self) -> str:
        return self._separator

    @property
    def max_depth(self) -> int:
        return self._max_depth

    @property
    def fields(self) -> Optional[List[str]]:
        return list(self._fields) if self._fields is not None else None

    # ------------------------------------------------------------------
    # core logic
    # ------------------------------------------------------------------

    def _flatten_value(
        self, value: Any, prefix: str, depth: int, out: Dict[str, Any]
    ) -> None:
        """Recursively expand *value* into *out* using dotted keys."""
        if (
            isinstance(value, dict)
            and (self._max_depth == 0 or depth < self._max_depth)
        ):
            for k, v in value.items():
                self._flatten_value(v, f"{prefix}{self._separator}{k}", depth + 1, out)
        else:
            out[prefix] = value

    def _flatten_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in entry.items():
            should_flatten = (
                self._fields is None or key in self._fields
            ) and isinstance(value, dict)
            if should_flatten:
                self._flatten_value(value, key, 1, result)
            else:
                result[key] = value
        return result

    def apply(self, entries: Iterable[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Yield a flattened copy of every entry in *entries*."""
        for entry in entries:
            yield self._flatten_entry(entry)
