"""RankPipeline – convenience wrapper combining LogPipeline with LogRanker."""
from __future__ import annotations

from typing import Iterable, Iterator

from logslice.pipeline import LogPipeline
from logslice.ranker import LogRanker


class RankPipeline:
    """High-level pipeline that filters entries then ranks them.

    Parameters
    ----------
    path:
        Path to the JSONL log file.
    field:
        Numeric field used for ranking (forwarded to :class:`LogRanker`).
    rank_field:
        Key written into each output entry (forwarded to :class:`LogRanker`).
    default:
        Fallback numeric value when *field* is absent (forwarded to
        :class:`LogRanker`).
    reverse:
        When ``True`` lowest value gets rank 1 (forwarded to
        :class:`LogRanker`).
    """

    def __init__(
        self,
        path: str,
        field: str = "score",
        rank_field: str = "rank",
        default: float = 0.0,
        reverse: bool = False,
    ) -> None:
        self._pipeline = LogPipeline(path)
        self._ranker = LogRanker(
            field=field,
            rank_field=rank_field,
            default=default,
            reverse=reverse,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def ranker(self) -> LogRanker:
        return self._ranker

    # ------------------------------------------------------------------
    # Delegation helpers
    # ------------------------------------------------------------------

    def add_filter(self, f) -> "RankPipeline":
        """Add a filter to the underlying :class:`LogPipeline`."""
        self._pipeline.add_filter(f)
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self) -> list[dict]:
        """Execute the pipeline and return ranked entries as a list."""
        entries = list(self._pipeline.run())
        return self._ranker.rank(entries)

    def stream(self) -> Iterator[dict]:
        """Execute the pipeline and yield ranked entries one by one."""
        entries = list(self._pipeline.run())
        yield from self._ranker.stream(entries)
