"""LogClamper — clamp numeric field values to a [min, max] range."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, Optional, Union

Number = Union[int, float]


class LogClamper:
    """Clamp a numeric field in every log entry to a given [lo, hi] range.

    Values below *lo* are raised to *lo*; values above *hi* are lowered to
    *hi*.  Non-numeric values are left untouched unless *coerce* is True, in
    which case a conversion to float is attempted and entries that fail
    conversion are passed through unchanged.

    Parameters
    ----------
    field:
        The entry key whose value should be clamped.
    lo:
        Inclusive lower bound.  ``None`` means no lower bound.
    hi:
        Inclusive upper bound.  ``None`` means no upper bound.
    coerce:
        When True, attempt ``float()`` conversion before clamping.
    """

    def __init__(
        self,
        field: str,
        lo: Optional[Number] = None,
        hi: Optional[Number] = None,
        *,
        coerce: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise ValueError("field must be a non-empty string")
        if lo is not None and hi is not None and lo > hi:
            raise ValueError(f"lo ({lo}) must be <= hi ({hi})")
        self._field = field
        self._lo = lo
        self._hi = hi
        self._coerce = coerce

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def lo(self) -> Optional[Number]:
        return self._lo

    @property
    def hi(self) -> Optional[Number]:
        return self._hi

    @property
    def coerce(self) -> bool:
        return self._coerce

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    def _clamp_value(self, value: Any) -> Any:
        if not isinstance(value, (int, float)):
            if not self._coerce:
                return value
            try:
                value = float(value)
            except (TypeError, ValueError):
                return value
        if self._lo is not None and value < self._lo:
            return type(value)(self._lo)
        if self._hi is not None and value > self._hi:
            return type(value)(self._hi)
        return value

    def apply(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Return a new entry with the field value clamped."""
        if self._field not in entry:
            return entry
        result = dict(entry)
        result[self._field] = self._clamp_value(entry[self._field])
        return result

    def stream(self, entries: Iterable[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Yield clamped entries from *entries*."""
        for entry in entries:
            yield self.apply(entry)

    def collect(self, entries: Iterable[Dict[str, Any]]) -> list:
        """Return a list of clamped entries."""
        return list(self.stream(entries))
