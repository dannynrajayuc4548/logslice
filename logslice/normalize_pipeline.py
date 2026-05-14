"""NormalizePipeline — convenience wrapper combining LogPipeline + LogNormalizer."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, Optional

from .pipeline import LogPipeline
from .normalizer import LogNormalizer


class NormalizePipeline:
    """Stream log entries through filters then normalise the results.

    Example::

        pipe = (
            NormalizePipeline("app.log")
            .alias("lvl", "level")
            .coerce("level", str.upper)
        )
        for entry in pipe.stream():
            print(entry)
    """

    def __init__(self, path: str) -> None:
        self._pipeline = LogPipeline(path)
        self._normalizer = LogNormalizer()

    # ------------------------------------------------------------------
    # expose sub-objects for advanced use
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def normalizer(self) -> LogNormalizer:
        return self._normalizer

    # ------------------------------------------------------------------
    # builder delegation
    # ------------------------------------------------------------------

    def add_filter(self, f: Any) -> "NormalizePipeline":
        self._pipeline.add_filter(f)
        return self

    def alias(self, old_key: str, new_key: str) -> "NormalizePipeline":
        self._normalizer.alias(old_key, new_key)
        return self

    def coerce(
        self, key: str, fn: Callable[[Any], Any]
    ) -> "NormalizePipeline":
        self._normalizer.coerce(key, fn)
        return self

    # ------------------------------------------------------------------
    # execution
    # ------------------------------------------------------------------

    def stream(self) -> Iterator[Dict[str, Any]]:
        """Yield filtered and normalised log entries."""
        return self._normalizer.stream(self._pipeline.stream())

    def collect(self) -> list:
        """Return all filtered and normalised entries as a list."""
        return list(self.stream())
