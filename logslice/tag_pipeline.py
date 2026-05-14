"""TagPipeline – convenience wrapper combining LogPipeline and LogTagger."""
from __future__ import annotations

from typing import Callable, Iterable, Iterator, Union
import re

from logslice.pipeline import LogPipeline
from logslice.tagger import LogTagger


class TagPipeline:
    """Run log entries through a filter pipeline and then a tagger.

    Usage::

        tp = (
            TagPipeline("app.log")
            .tag_if_matches("slow", "message", r"timeout")
            .tag_if_field_equals("critical", "level", "ERROR")
        )
        for entry in tp.stream():
            print(entry["tags"])
    """

    def __init__(
        self,
        log_path: str,
        tag_field: str = "tags",
    ) -> None:
        self._pipeline = LogPipeline(log_path)
        self._tagger = LogTagger(tag_field=tag_field)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def tagger(self) -> LogTagger:
        return self._tagger

    # ------------------------------------------------------------------
    # Delegation to LogPipeline
    # ------------------------------------------------------------------

    def add_filter(self, f) -> "TagPipeline":
        self._pipeline.add_filter(f)
        return self

    # ------------------------------------------------------------------
    # Delegation to LogTagger
    # ------------------------------------------------------------------

    def add_rule(
        self, tag: str, predicate: Callable[[dict], bool]
    ) -> "TagPipeline":
        self._tagger.add_rule(tag, predicate)
        return self

    def tag_if_matches(
        self,
        tag: str,
        field: str,
        pattern: Union[str, re.Pattern],
    ) -> "TagPipeline":
        self._tagger.tag_if_matches(tag, field, pattern)
        return self

    def tag_if_field_equals(
        self, tag: str, field: str, value: object
    ) -> "TagPipeline":
        self._tagger.tag_if_field_equals(tag, field, value)
        return self

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    def stream(self) -> Iterator[dict]:
        """Yield filtered and tagged entries from the log file."""
        return self._tagger.stream(self._pipeline.stream())

    def collect(self) -> list:
        """Return all filtered and tagged entries as a list."""
        return list(self.stream())
