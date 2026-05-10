"""LogArchiver — compress and archive filtered log entries to a file."""

import gzip
import json
import os
from typing import Iterable, Iterator, Optional


class LogArchiver:
    """Write log entries to a gzip-compressed JSONL archive.

    Parameters
    ----------
    path:
        Destination file path (should end in ``.jsonl.gz`` by convention).
    mode:
        ``"write"`` to overwrite, ``"append"`` to extend an existing archive.
    encoding:
        Text encoding used when serialising entries (default ``"utf-8"``).
    """

    def __init__(
        self,
        path: str,
        mode: str = "write",
        encoding: str = "utf-8",
    ) -> None:
        if mode not in ("write", "append"):
            raise ValueError("mode must be 'write' or 'append'")
        self._path = path
        self._mode = mode
        self._encoding = encoding
        self._gz_mode = "wb" if mode == "write" else "ab"

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def path(self) -> str:
        """Destination archive path."""
        return self._path

    @property
    def mode(self) -> str:
        """Archive open mode (``'write'`` or ``'append'``)"""
        return self._mode

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def archive(self, entries: Iterable[dict]) -> int:
        """Write *entries* to the archive and return the number written."""
        count = 0
        with gzip.open(self._path, self._gz_mode) as fh:
            for entry in entries:
                line = (json.dumps(entry) + "\n").encode(self._encoding)
                fh.write(line)
                count += 1
        return count

    def read(self) -> Iterator[dict]:
        """Iterate over entries stored in the archive."""
        with gzip.open(self._path, "rb") as fh:
            for raw in fh:
                line = raw.decode(self._encoding).strip()
                if line:
                    yield json.loads(line)

    def exists(self) -> bool:
        """Return ``True`` if the archive file already exists on disk."""
        return os.path.isfile(self._path)

    def size(self) -> int:
        """Return the compressed size in bytes, or 0 if the file is absent."""
        try:
            return os.path.getsize(self._path)
        except FileNotFoundError:
            return 0
