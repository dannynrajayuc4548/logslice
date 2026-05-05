"""logslice — Lightweight Python library for filtering and streaming structured log files."""

from .parser import LogParser
from .filters import RegexFilter, TimeRangeFilter

__version__ = "0.1.0"
__all__ = ["LogParser", "RegexFilter", "TimeRangeFilter"]
