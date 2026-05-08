"""stream_from_checkpoint — convenience helper that wires LogWatcher + LogCheckpoint."""

from typing import Dict, Generator, Optional

from .checkpoint import LogCheckpoint
from .watcher import LogWatcher


def stream_from_checkpoint(
    log_path: str,
    checkpoint: LogCheckpoint,
    *,
    follow: bool = False,
    poll_interval: float = 0.2,
    max_lines: Optional[int] = None,
) -> Generator[Dict, None, None]:
    """Yield parsed log entries starting from the last saved checkpoint.

    After each entry is yielded the checkpoint is updated so that an
    interrupted consumer can resume without re-processing lines.

    Args:
        log_path:      Absolute or relative path to the log file.
        checkpoint:    A :class:`~logslice.checkpoint.LogCheckpoint` instance.
        follow:        When ``True`` keep tailing the file for new lines.
        poll_interval: Seconds between polls when *follow* is ``True``.
        max_lines:     Stop after this many entries (``None`` = unlimited).

    Yields:
        Parsed log entry dicts, each containing at least ``_raw``.
    """
    start_offset = checkpoint.load(log_path) or 0
    watcher = LogWatcher(log_path)

    count = 0
    for entry in watcher.follow(
        from_offset=start_offset,
        poll_interval=poll_interval,
        follow=follow,
    ):
        yield entry
        # Persist the new offset after each entry.
        checkpoint.save(log_path, watcher.current_offset)
        count += 1
        if max_lines is not None and count >= max_lines:
            break
