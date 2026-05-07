"""Convenience helpers built on top of LogWatcher."""

from __future__ import annotations

from typing import Iterator, List, Optional

from .watcher import LogWatcher
from .parser import LogParser


def tail(
    path: str,
    n: int = 10,
    parser: Optional[LogParser] = None,
    from_start: bool = False,
) -> List:
    """Return the last *n* new entries written to *path*.

    When *from_start* is ``True`` the file is read from the beginning;
    otherwise only lines appended after the call returns are collected
    (useful for integration tests or CI checks).

    Parameters
    ----------
    path:
        Log file to read.
    n:
        Maximum number of entries to collect.
    parser:
        A :class:`~logslice.parser.LogParser` instance used to parse
        each raw line.  When *None* raw strings are returned.
    from_start:
        If ``True`` start reading from offset 0.
    """
    _raw_parser = parser._parse_line if parser is not None else None
    watcher = LogWatcher(path, poll_interval=0.05, parser=_raw_parser)

    if not from_start:
        watcher.seek_end()

    return list(watcher.follow(max_lines=n, timeout=2.0))


def stream_live(
    path: str,
    parser: Optional[LogParser] = None,
) -> Iterator:
    """Yield entries from *path* as they are appended (infinite iterator).

    The watcher starts from the current end of the file so historical
    content is skipped.

    Parameters
    ----------
    path:
        Log file to watch.
    parser:
        Optional :class:`~logslice.parser.LogParser` for structured
        parsing.  When *None* raw stripped lines are yielded.
    """
    _raw_parser = parser._parse_line if parser is not None else None
    watcher = LogWatcher(path, poll_interval=0.1, parser=_raw_parser)
    watcher.seek_end()
    yield from watcher.follow()
