"""LogCheckpoint — persist and restore stream read positions."""

import json
import os
from typing import Dict, Optional


class LogCheckpoint:
    """Persist byte-offset checkpoints for one or more log file paths.

    Checkpoints are stored as a simple JSON file so that a watcher or
    tail consumer can resume from where it left off after a restart.

    Example::

        cp = LogCheckpoint(".logslice_checkpoint.json")
        cp.save("/var/log/app.log", 4096)
        offset = cp.load("/var/log/app.log")  # -> 4096
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._data: Dict[str, int] = {}
        self._load_from_disk()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def path(self) -> str:
        """Path to the checkpoint file on disk."""
        return self._path

    def save(self, log_path: str, offset: int) -> None:
        """Persist *offset* for *log_path* and flush to disk."""
        if offset < 0:
            raise ValueError("offset must be >= 0")
        self._data[log_path] = offset
        self._flush()

    def load(self, log_path: str) -> Optional[int]:
        """Return the saved offset for *log_path*, or ``None`` if unknown."""
        return self._data.get(log_path)

    def delete(self, log_path: str) -> bool:
        """Remove the entry for *log_path*.  Returns ``True`` if it existed."""
        if log_path in self._data:
            del self._data[log_path]
            self._flush()
            return True
        return False

    def clear(self) -> None:
        """Remove all checkpoints and truncate the file."""
        self._data.clear()
        self._flush()

    def all(self) -> Dict[str, int]:
        """Return a shallow copy of all stored checkpoints."""
        return dict(self._data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_from_disk(self) -> None:
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    self._data = json.load(fh)
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def _flush(self) -> None:
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)
