"""LogZipper – pair entries from two sources by a shared key field."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, Optional


class LogZipper:
    """Zip two streams of log entries together on a common key field.

    Entries from *left* and *right* that share the same value for *field*
    are merged into a single dict.  Left-side keys take precedence when both
    sides contain the same key.  Entries whose key appears in only one stream
    are handled according to *how*:

    - ``'inner'``  – discard unmatched entries (default)
    - ``'left'``   – keep all left entries; right side may be absent
    - ``'right'``  – keep all right entries; left side may be absent
    - ``'outer'``  – keep all entries from both sides
    """

    _VALID_HOW = frozenset({"inner", "left", "right", "outer"})

    def __init__(
        self,
        field: str = "request_id",
        how: str = "inner",
        left_prefix: str = "",
        right_prefix: str = "right_",
    ) -> None:
        if not field or not field.strip():
            raise ValueError("field must be a non-empty string")
        if how not in self._VALID_HOW:
            raise ValueError(f"how must be one of {sorted(self._VALID_HOW)!r}; got {how!r}")
        self._field = field
        self._how = how
        self._left_prefix = left_prefix
        self._right_prefix = right_prefix

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def how(self) -> str:
        return self._how

    @property
    def left_prefix(self) -> str:
        return self._left_prefix

    @property
    def right_prefix(self) -> str:
        return self._right_prefix

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def zip(
        self,
        left: Iterable[Dict[str, Any]],
        right: Iterable[Dict[str, Any]],
    ) -> Iterator[Dict[str, Any]]:
        """Yield merged entries according to *how*."""
        left_index: Dict[Any, Dict[str, Any]] = {}
        right_index: Dict[Any, Dict[str, Any]] = {}

        for entry in left:
            key = entry.get(self._field)
            left_index[key] = entry

        for entry in right:
            key = entry.get(self._field)
            right_index[key] = entry

        all_keys: set = set()
        if self._how in ("inner", "left", "outer"):
            all_keys.update(left_index)
        if self._how in ("inner", "right", "outer"):
            all_keys.update(right_index)
        if self._how == "inner":
            all_keys = set(left_index) & set(right_index)

        for key in all_keys:
            merged = self._merge(
                left_index.get(key), right_index.get(key)
            )
            if merged is not None:
                yield merged

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _merge(
        self,
        left: Optional[Dict[str, Any]],
        right: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        result: Dict[str, Any] = {}
        if right:
            for k, v in right.items():
                result[f"{self._right_prefix}{k}"] = v
        if left:
            for k, v in left.items():
                result[f"{self._left_prefix}{k}"] = v
        return result or None
