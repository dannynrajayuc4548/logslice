"""ProfilePipeline – convenience wrapper that pairs LogPipeline with LogProfiler."""
from __future__ import annotations

from typing import Callable, Dict, Iterable, Iterator, List, Optional

from .pipeline import LogPipeline
from .profiler import LogProfiler


class ProfilePipeline:
    """Run log entries through a filter pipeline while collecting profiling data.

    Example
    -------
    >>> pp = ProfilePipeline("app.log", timestamp_field="ts")
    >>> pp.add_filter(my_filter)
    >>> results = pp.collect()
    >>> print(pp.profiler.summary())
    """

    def __init__(
        self,
        path: str,
        timestamp_field: Optional[str] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._pipeline = LogPipeline(path)
        kwargs: Dict = {}
        if timestamp_field is not None:
            kwargs["timestamp_field"] = timestamp_field
        if clock is not None:
            kwargs["clock"] = clock
        self._profiler = LogProfiler(**kwargs)

    # ------------------------------------------------------------------
    # read-only accessors
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        """Underlying :class:`LogPipeline`."""
        return self._pipeline

    @property
    def profiler(self) -> LogProfiler:
        """Underlying :class:`LogProfiler`."""
        return self._profiler

    # ------------------------------------------------------------------
    # delegation helpers
    # ------------------------------------------------------------------

    def add_filter(self, f) -> "ProfilePipeline":
        """Add a filter to the inner pipeline; returns *self* for chaining."""
        self._pipeline.add_filter(f)
        return self

    def enrich(self, key: str, value) -> "ProfilePipeline":
        """Delegate to :meth:`LogPipeline.enrich`; returns *self*."""
        self._pipeline.enrich(key, value)
        return self

    # ------------------------------------------------------------------
    # execution
    # ------------------------------------------------------------------

    def stream(self) -> Iterator[Dict]:
        """Yield profiled entries from the pipeline."""
        for entry in self._profiler.stream(self._pipeline.stream()):
            yield entry

    def collect(self) -> List[Dict]:
        """Return all profiled entries as a list."""
        return list(self.stream())
