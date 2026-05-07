"""Tail-style log file watcher that yields new lines as they appear."""

import os
import time
from typing import Callable, Iterator, Optional


class LogWatcher:
    """Watch a log file and yield new lines as they are appended.

    Parameters
    ----------
    path:
        Path to the log file to watch.
    poll_interval:
        Seconds to sleep between polls when no new data is available.
    parser:
        Optional callable that receives a raw line and returns a parsed
        entry (dict).  When *None* the raw stripped line is yielded.
    """

    def __init__(
        self,
        path: str,
        poll_interval: float = 0.25,
        parser: Optional[Callable[[str], Optional[dict]]] = None,
    ) -> None:
        self.path = path
        self.poll_interval = poll_interval
        self._parser = parser
        self._offset: int = 0

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def seek_end(self) -> None:
        """Move the internal offset to the current end of the file.

        Call this before :meth:`follow` to skip historical content.
        """
        try:
            self._offset = os.path.getsize(self.path)
        except FileNotFoundError:
            self._offset = 0

    def follow(
        self,
        max_lines: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> Iterator:
        """Yield entries from the watched file indefinitely (or until limits).

        Parameters
        ----------
        max_lines:
            Stop after yielding this many entries.
        timeout:
            Stop after approximately this many seconds.
        """
        start = time.monotonic()
        yielded = 0

        while True:
            if timeout is not None and (time.monotonic() - start) >= timeout:
                return

            try:
                file_size = os.path.getsize(self.path)
            except FileNotFoundError:
                time.sleep(self.poll_interval)
                continue

            if file_size > self._offset:
                with open(self.path, "r", encoding="utf-8", errors="replace") as fh:
                    fh.seek(self._offset)
                    for raw in fh:
                        entry = self._parse(raw)
                        if entry is not None:
                            yield entry
                            yielded += 1
                            if max_lines is not None and yielded >= max_lines:
                                self._offset = fh.tell()
                                return
                    self._offset = fh.tell()
            else:
                time.sleep(self.poll_interval)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _parse(self, raw: str):
        line = raw.rstrip("\n")
        if not line:
            return None
        if self._parser is not None:
            return self._parser(line)
        return line
