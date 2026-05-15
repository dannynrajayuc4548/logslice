"""GroupPipeline – combine LogPipeline filtering with LogGrouper bucketing."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from .pipeline import LogPipeline
from .grouper import LogGrouper


class GroupPipeline:
    """High-level facade that reads a log file, filters entries, then groups them.

    Parameters
    ----------
    path:
        Path to the JSONL log file.
    field:
        Entry field used as the grouping key (forwarded to :class:`LogGrouper`).
    default:
        Fallback bucket label when the field is absent.
    """

    def __init__(
        self,
        path: str,
        field: str = "level",
        default: str = "unknown",
    ) -> None:
        self._pipeline = LogPipeline(path)
        self._grouper = LogGrouper(field=field, default=default)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def grouper(self) -> LogGrouper:
        return self._grouper

    # ------------------------------------------------------------------
    # Delegation helpers (fluent)
    # ------------------------------------------------------------------

    def add_filter(self, f) -> "GroupPipeline":
        self._pipeline.add_filter(f)
        return self

    def on_group(self, key: str, callback: Callable[[dict], None]) -> "GroupPipeline":
        self._grouper.on_group(key, callback)
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, List[dict]]:
        """Process the file and return the populated buckets dict."""
        self._grouper.clear()
        for entry in self._pipeline.stream():
            self._grouper.feed(entry)
        return self._grouper.buckets

    def counts(self) -> Dict[str, int]:
        """Run the pipeline and return per-bucket entry counts."""
        buckets = self.run()
        return {k: len(v) for k, v in buckets.items()}
