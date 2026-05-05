"""Output formatters for log entries produced by LogParser."""

import json
from typing import Any, Dict, Optional


class BaseFormatter:
    """Base class for all output formatters."""

    def format(self, entry: Dict[str, Any]) -> str:
        raise NotImplementedError


class JSONFormatter(BaseFormatter):
    """Serialize each log entry as a compact JSON string."""

    def __init__(self, indent: Optional[int] = None, sort_keys: bool = False):
        self.indent = indent
        self.sort_keys = sort_keys

    def format(self, entry: Dict[str, Any]) -> str:
        return json.dumps(entry, indent=self.indent, sort_keys=self.sort_keys, default=str)


class PlainFormatter(BaseFormatter):
    """Render a log entry as a human-readable key=value line."""

    def __init__(self, fields: Optional[list] = None, separator: str = " | "):
        """
        Args:
            fields: ordered list of field names to include; None means all fields.
            separator: string placed between each key=value pair.
        """
        self.fields = fields
        self.separator = separator

    def format(self, entry: Dict[str, Any]) -> str:
        keys = self.fields if self.fields else list(entry.keys())
        parts = [f"{k}={entry[k]}" for k in keys if k in entry]
        return self.separator.join(parts)


class CSVFormatter(BaseFormatter):
    """Render a log entry as a CSV row (no header)."""

    def __init__(self, fields: Optional[list] = None):
        self.fields = fields

    def format(self, entry: Dict[str, Any]) -> str:
        keys = self.fields if self.fields else list(entry.keys())
        values = [str(entry.get(k, "")) for k in keys]
        # Quote values that contain commas or quotes
        escaped = []
        for v in values:
            if "," in v or '"' in v or "\n" in v:
                v = '"' + v.replace('"', '""') + '"'
            escaped.append(v)
        return ",".join(escaped)
