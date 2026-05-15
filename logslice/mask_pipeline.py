"""MaskPipeline – convenience wrapper combining LogPipeline with LogMasker."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional

from .masker import LogMasker
from .pipeline import LogPipeline


class MaskPipeline:
    """Read log entries through a filter pipeline then apply field masking.

    Example::

        mp = (
            MaskPipeline("app.log")
            .mask_pattern("email", r"[^@]+@[^@]+", replacement="<email>")
            .mask_full("password")
        )
        for entry in mp.stream():
            print(entry)
    """

    def __init__(self, path: str, placeholder: str = "***") -> None:
        self._pipeline = LogPipeline(path)
        self._masker = LogMasker(placeholder=placeholder)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def masker(self) -> LogMasker:
        return self._masker

    # ------------------------------------------------------------------
    # Pipeline delegation
    # ------------------------------------------------------------------

    def add_filter(self, f: Any) -> "MaskPipeline":
        self._pipeline.add_filter(f)
        return self

    # ------------------------------------------------------------------
    # Masker delegation
    # ------------------------------------------------------------------

    def mask_pattern(self, field: str, pattern: str, flags: int = 0) -> "MaskPipeline":
        self._masker.mask_pattern(field, pattern, flags)
        return self

    def mask_full(self, field: str) -> "MaskPipeline":
        self._masker.mask_full(field)
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def stream(self) -> Iterator[Dict[str, Any]]:
        """Yield filtered and masked log entries."""
        return self._masker.stream(self._pipeline.stream())

    def collect(self) -> List[Dict[str, Any]]:
        """Return all filtered and masked entries as a list."""
        return list(self.stream())
