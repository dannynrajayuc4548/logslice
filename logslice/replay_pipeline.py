"""Convenience wrapper that combines LogPipeline with LogReplayer."""

from typing import Callable, Iterable, Iterator, Optional

from logslice.pipeline import LogPipeline
from logslice.replayer import LogReplayer


class ReplayPipeline:
    """Run a LogPipeline and feed its output through a LogReplayer.

    Example::

        rp = (
            ReplayPipeline(log_path, speed=2.0)
            .add_filter(RegexFilter("error"))
        )
        for entry in rp.stream():
            print(entry)
    """

    def __init__(
        self,
        path: str,
        speed: float = 1.0,
        timestamp_field: str = "timestamp",
        timestamp_fmt: str = "%Y-%m-%dT%H:%M:%S",
        on_entry: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self._pipeline = LogPipeline(path)
        self._replayer = LogReplayer(
            speed=speed,
            timestamp_field=timestamp_field,
            timestamp_fmt=timestamp_fmt,
            on_entry=on_entry,
        )

    # ------------------------------------------------------------------
    # Fluent helpers that delegate to the inner pipeline
    # ------------------------------------------------------------------

    def add_filter(self, f) -> "ReplayPipeline":
        self._pipeline.add_filter(f)
        return self

    def set_formatter(self, fmt) -> "ReplayPipeline":
        self._pipeline.set_formatter(fmt)
        return self

    def enrich(self, key: str, value) -> "ReplayPipeline":
        self._pipeline.enrich(key, value)
        return self

    # ------------------------------------------------------------------
    # Terminal operations
    # ------------------------------------------------------------------

    def stream(self) -> Iterator[dict]:
        """Yield entries processed by the pipeline then throttled by the replayer."""
        return self._replayer.stream(self._pipeline.stream())

    def collect(self) -> list:
        return list(self.stream())

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def replayer(self) -> LogReplayer:
        return self._replayer
