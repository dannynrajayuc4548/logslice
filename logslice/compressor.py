"""LogCompressor – compress collected log entries to a gzip or bz2 file."""

from __future__ import annotations

import bz2
import gzip
import json
from pathlib import Path
from typing import Iterable, Literal

_MODES = ("gz", "bz2")


class LogCompressor:
    """Write log entries to a compressed archive file.

    Parameters
    ----------
    path:
        Destination file path.  The appropriate extension is appended
        automatically if not already present.
    mode:
        Compression format – ``'gz'`` (gzip, default) or ``'bz2'`` (bzip2).
    """

    def __init__(
        self,
        path: str | Path,
        mode: Literal["gz", "bz2"] = "gz",
    ) -> None:
        if mode not in _MODES:
            raise ValueError(f"mode must be one of {_MODES!r}, got {mode!r}")
        self._mode = mode
        path = Path(path)
        if path.suffix != f".{mode}":
            path = path.with_suffix(path.suffix + f".{mode}")
        self._path = path

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        """Resolved destination path (read-only)."""
        return self._path

    @property
    def mode(self) -> str:
        """Compression mode (read-only)."""
        return self._mode

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compress(self, entries: Iterable[dict]) -> int:
        """Serialize *entries* as JSON lines and write to the compressed file.

        Returns the number of entries written.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        open_fn = gzip.open if self._mode == "gz" else bz2.open
        count = 0
        with open_fn(self._path, "wt", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
                count += 1
        return count

    def decompress(self) -> list[dict]:
        """Read the compressed file and return a list of parsed log entries."""
        open_fn = gzip.open if self._mode == "gz" else bz2.open
        entries: list[dict] = []
        with open_fn(self._path, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries
