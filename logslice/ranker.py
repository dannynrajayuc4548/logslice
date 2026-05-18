"""LogRanker – assign ordinal rank to log entries based on a numeric field."""
from __future__ import annotations

from typing import Callable, Iterable, Iterator, Optional


class LogRanker:
    """Rank log entries by a numeric field and attach the rank to each entry.

    Parameters
    ----------
    field:
        Name of the numeric field to rank by (default ``"score"``).  Higher
        values receive a lower (better) rank unless *reverse* is ``True``.
    rank_field:
        Name of the key written into each entry (default ``"rank"``).  The
        value is 1-based.
    default:
        Value used when *field* is absent or non-numeric (default ``0``).
    reverse:
        When ``True`` lowest numeric value gets rank 1 (ascending order).
    """

    def __init__(
        self,
        field: str = "score",
        rank_field: str = "rank",
        default: float = 0.0,
        reverse: bool = False,
    ) -> None:
        if not field or not field.strip():
            raise ValueError("field must be a non-empty string")
        if not rank_field or not rank_field.strip():
            raise ValueError("rank_field must be a non-empty string")
        self._field = field
        self._rank_field = rank_field
        self._default = default
        self._reverse = reverse

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def rank_field(self) -> str:
        return self._rank_field

    @property
    def default(self) -> float:
        return self._default

    @property
    def reverse(self) -> bool:
        return self._reverse

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _numeric(self, entry: dict) -> float:
        try:
            return float(entry.get(self._field, self._default))
        except (TypeError, ValueError):
            return float(self._default)

    def rank(self, entries: Iterable[dict]) -> list[dict]:
        """Return a new list of entries each enriched with *rank_field*.

        Entries are sorted by *field* (descending by default, i.e. highest
        value = rank 1).  The original order among equal-valued entries is
        preserved (stable sort).
        """
        items = list(entries)
        sorted_items = sorted(
            items, key=self._numeric, reverse=not self._reverse
        )
        ranked: list[dict] = []
        for position, entry in enumerate(sorted_items, start=1):
            enriched = dict(entry)
            enriched[self._rank_field] = position
            ranked.append(enriched)
        return ranked

    def stream(self, entries: Iterable[dict]) -> Iterator[dict]:
        """Yield ranked entries one by one (materialises the full list first)."""
        yield from self.rank(entries)
