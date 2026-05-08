"""LogTransformer — apply field-level transformations to log entries.

Allows users to enrich, rename, redact, or derive new fields from
existing log entry dictionaries before they reach a writer or exporter.

Example usage::

    from logslice.transformer import LogTransformer

    t = (LogTransformer()
         .rename("lvl", "level")
         .add("service", lambda e: "api")
         .redact("password")
         .apply(lambda e: {**e, "message": e.get("message", "").upper()}))

    transformed = list(t.stream(entries))
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional

LogEntry = Dict[str, Any]
TransformFn = Callable[[LogEntry], LogEntry]

_REDACTED = "***REDACTED***"


class LogTransformer:
    """Chain multiple transformation steps over log entry dictionaries."""

    def __init__(self) -> None:
        self._steps: List[TransformFn] = []

    # ------------------------------------------------------------------
    # Builder methods — each returns *self* for chaining
    # ------------------------------------------------------------------

    def rename(self, old_key: str, new_key: str) -> "LogTransformer":
        """Rename *old_key* to *new_key*; no-op if *old_key* is absent."""

        def _rename(entry: LogEntry) -> LogEntry:
            if old_key in entry:
                entry = {**entry, new_key: entry[old_key]}
                entry.pop(old_key, None)  # type: ignore[attr-defined]
                # dict copy above means we can safely drop from the new dict
                result = dict(entry)
                result[new_key] = result.pop(old_key, result.get(new_key))
                return result
            return entry

        # Simpler, allocation-friendly version:
        def _rename_clean(entry: LogEntry) -> LogEntry:
            if old_key not in entry:
                return entry
            out = {k: v for k, v in entry.items() if k != old_key}
            out[new_key] = entry[old_key]
            return out

        self._steps.append(_rename_clean)
        return self

    def add(self, key: str, value_fn: Callable[[LogEntry], Any]) -> "LogTransformer":
        """Add (or overwrite) *key* using the result of *value_fn(entry)*."""

        def _add(entry: LogEntry) -> LogEntry:
            return {**entry, key: value_fn(entry)}

        self._steps.append(_add)
        return self

    def redact(self, key: str, placeholder: str = _REDACTED) -> "LogTransformer":
        """Replace the value of *key* with *placeholder* if the key exists."""

        def _redact(entry: LogEntry) -> LogEntry:
            if key in entry:
                return {**entry, key: placeholder}
            return entry

        self._steps.append(_redact)
        return self

    def drop(self, key: str) -> "LogTransformer":
        """Remove *key* from the entry; no-op if the key is absent."""

        def _drop(entry: LogEntry) -> LogEntry:
            if key not in entry:
                return entry
            return {k: v for k, v in entry.items() if k != key}

        self._steps.append(_drop)
        return self

    def apply(self, fn: TransformFn) -> "LogTransformer":
        """Append an arbitrary transformation function *fn(entry) -> entry*."""
        self._steps.append(fn)
        return self

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def transform_one(self, entry: LogEntry) -> LogEntry:
        """Run all transformation steps on a single *entry* and return it."""
        for step in self._steps:
            entry = step(entry)
        return entry

    def stream(self, entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        """Yield transformed copies of each entry in *entries*."""
        for entry in entries:
            yield self.transform_one(entry)

    def collect(self, entries: Iterable[LogEntry]) -> List[LogEntry]:
        """Return a list of transformed entries."""
        return list(self.stream(entries))

    def __repr__(self) -> str:  # pragma: no cover
        return f"LogTransformer(steps={len(self._steps)})"
