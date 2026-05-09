"""LogReplayer: replay structured log entries with configurable speed control."""

import time
from datetime import datetime
from typing import Callable, Iterable, Iterator, Optional


DEFAULT_TIMESTAMP_FIELD = "timestamp"
DEFAULT_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"


class LogReplayer:
    """Replay log entries in time order, optionally throttled to real or scaled time.

    Args:
        speed:  Playback multiplier. 1.0 = real time, 2.0 = double speed,
                0.0 = no delay (as fast as possible).
        timestamp_field: Dict key that holds the timestamp string.
        timestamp_fmt:   strptime format for parsing the timestamp.
        on_entry:        Optional callback invoked with each entry before yielding.
    """

    def __init__(
        self,
        speed: float = 1.0,
        timestamp_field: str = DEFAULT_TIMESTAMP_FIELD,
        timestamp_fmt: str = DEFAULT_TIMESTAMP_FORMAT,
        on_entry: Optional[Callable[[dict], None]] = None,
    ) -> None:
        if speed < 0:
            raise ValueError("speed must be >= 0")
        self._speed = speed
        self._field = timestamp_field
        self._fmt = timestamp_fmt
        self._on_entry = on_entry

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def timestamp_field(self) -> str:
        return self._field

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _parse_ts(self, entry: dict) -> Optional[datetime]:
        raw = entry.get(self._field)
        if raw is None:
            return None
        try:
            return datetime.strptime(str(raw), self._fmt)
        except ValueError:
            return None

    def stream(self, entries: Iterable[dict]) -> Iterator[dict]:
        """Yield entries, sleeping between them to simulate original timing."""
        prev_log_ts: Optional[datetime] = None
        prev_wall: Optional[float] = None

        for entry in entries:
            log_ts = self._parse_ts(entry)

            if self._speed > 0 and log_ts is not None and prev_log_ts is not None:
                log_delta = (log_ts - prev_log_ts).total_seconds()
                if log_delta > 0:
                    wall_delta = log_delta / self._speed
                    elapsed = time.monotonic() - prev_wall  # type: ignore[operator]
                    sleep_for = wall_delta - elapsed
                    if sleep_for > 0:
                        time.sleep(sleep_for)

            if self._on_entry is not None:
                self._on_entry(entry)

            prev_log_ts = log_ts
            prev_wall = time.monotonic()
            yield entry

    def collect(self, entries: Iterable[dict]) -> list:
        """Consume stream() and return all entries as a list."""
        return list(self.stream(entries))
