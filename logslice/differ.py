"""LogDiffer – compare two streams of log entries and surface added/removed/changed records."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, List, Tuple

_Entry = Dict[str, Any]


def _default_key(entry: _Entry) -> str:
    """Use 'id' when present, otherwise fall back to the raw log line."""
    return str(entry.get("id", entry.get("raw", "")))


class LogDiffer:
    """Compare two collections of log entries and classify differences.

    Parameters
    ----------
    key:
        Callable that returns a hashable identity for each entry.  Defaults to
        the entry's ``id`` field, falling back to ``raw``.
    compare_fields:
        When *None* the entire entry dict is compared for equality.  Pass a
        list of field names to restrict the equality check to those fields.
    """

    def __init__(
        self,
        key: Callable[[_Entry], str] | None = None,
        compare_fields: List[str] | None = None,
    ) -> None:
        self._key = key or _default_key
        self._compare_fields = compare_fields

    # ------------------------------------------------------------------
    # public properties
    # ------------------------------------------------------------------

    @property
    def key(self) -> Callable[[_Entry], str]:
        return self._key

    @property
    def compare_fields(self) -> List[str] | None:
        return self._compare_fields

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _sig(self, entry: _Entry) -> Any:
        """Return the comparison signature for *entry*."""
        if self._compare_fields is None:
            return tuple(sorted(entry.items()))
        return tuple((f, entry.get(f)) for f in self._compare_fields)

    # ------------------------------------------------------------------
    # core API
    # ------------------------------------------------------------------

    def diff(
        self,
        left: Iterable[_Entry],
        right: Iterable[_Entry],
    ) -> Iterator[Tuple[str, _Entry]]:
        """Yield ``(status, entry)`` tuples where *status* is one of:

        * ``'added'``   – present in *right* but not *left*
        * ``'removed'`` – present in *left* but not *right*
        * ``'changed'`` – present in both but with different field values
        * ``'unchanged'`` – identical in both streams
        """
        left_map: Dict[str, _Entry] = {self._key(e): e for e in left}
        right_map: Dict[str, _Entry] = {self._key(e): e for e in right}

        all_keys = set(left_map) | set(right_map)
        for k in sorted(all_keys):
            if k not in left_map:
                yield ("added", right_map[k])
            elif k not in right_map:
                yield ("removed", left_map[k])
            elif self._sig(left_map[k]) != self._sig(right_map[k]):
                yield ("changed", right_map[k])
            else:
                yield ("unchanged", left_map[k])

    def only_changes(
        self,
        left: Iterable[_Entry],
        right: Iterable[_Entry],
    ) -> Iterator[Tuple[str, _Entry]]:
        """Like :meth:`diff` but skips ``'unchanged'`` entries."""
        for status, entry in self.diff(left, right):
            if status != "unchanged":
                yield status, entry
