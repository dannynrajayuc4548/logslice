"""logslice — Lightweight library for filtering and streaming structured logs."""

from logslice.filters import RegexFilter, TimeRangeFilter
from logslice.parser import LogParser
from logslice.formatters import JSONFormatter, PlainFormatter
from logslice.writer import LogWriter
from logslice.aggregator import LogAggregator
from logslice.summary import LogSummary
from logslice.pipeline import LogPipeline
from logslice.exporter import LogExporter
from logslice.watcher import LogWatcher
from logslice.tail import tail, stream_live
from logslice.sampler import LogSampler
from logslice.router import LogRouter
from logslice.dispatch import LogDispatcher
from logslice.deduplicator import LogDeduplicator

__all__ = [
    "RegexFilter",
    "TimeRangeFilter",
    "LogParser",
    "JSONFormatter",
    "PlainFormatter",
    "LogWriter",
    "LogAggregator",
    "LogSummary",
    "LogPipeline",
    "LogExporter",
    "LogWatcher",
    "tail",
    "stream_live",
    "LogSampler",
    "LogRouter",
    "LogDispatcher",
    "LogDeduplicator",
]
