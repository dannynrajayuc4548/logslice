"""Writer utilities that combine a LogParser stream with a formatter."""

import sys
from typing import IO, Iterator, Dict, Any

from logslice.formatters import BaseFormatter, JSONFormatter
from logslice.parser import LogParser


class LogWriter:
    """Iterates over parsed log entries, formats them, and writes to a sink."""

    def __init__(
        self,
        parser: LogParser,
        formatter: BaseFormatter = None,
        sink: IO[str] = None,
    ):
        """
        Args:
            parser: a configured LogParser instance.
            formatter: formatter to apply to each entry; defaults to JSONFormatter.
            sink: writable text stream; defaults to sys.stdout.
        """
        self.parser = parser
        self.formatter = formatter or JSONFormatter()
        self.sink = sink or sys.stdout

    def write(self, source: str) -> int:
        """Stream *source* through the parser, format each entry, write to sink.

        Args:
            source: path to the log file.

        Returns:
            Number of entries written.
        """
        count = 0
        for entry in self.parser.stream(source):
            line = self.formatter.format(entry)
            self.sink.write(line + "\n")
            count += 1
        return count

    def collect(self, source: str) -> Iterator[str]:
        """Yield formatted strings without writing to the sink."""
        for entry in self.parser.stream(source):
            yield self.formatter.format(entry)
