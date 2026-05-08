"""LogRedactor – mask or remove sensitive fields from log entries."""

import re
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Union

_MASK = "***"


class LogRedactor:
    """Redact sensitive data from structured log entries.

    Supports three strategies per rule:
    - ``mask``   – replace the field value with a fixed mask string (default).
    - ``remove`` – delete the field entirely.
    - ``regex``  – apply a regex substitution on the string value.
    """

    def __init__(self, mask: str = _MASK) -> None:
        self._mask = mask
        # Each rule: (field, strategy, extra)
        self._rules: List[tuple] = []

    # ------------------------------------------------------------------
    # Rule builders
    # ------------------------------------------------------------------

    def mask_field(self, field: str, mask: Optional[str] = None) -> "LogRedactor":
        """Replace *field* value with *mask* (or the instance default)."""
        self._rules.append((field, "mask", mask or self._mask))
        return self

    def remove_field(self, field: str) -> "LogRedactor":
        """Remove *field* from the entry entirely."""
        self._rules.append((field, "remove", None))
        return self

    def regex_field(
        self, field: str, pattern: str, replacement: str = _MASK, flags: int = 0
    ) -> "LogRedactor":
        """Apply a regex substitution on the string value of *field*."""
        compiled = re.compile(pattern, flags)
        self._rules.append((field, "regex", (compiled, replacement)))
        return self

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def apply(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Return a *new* dict with all redaction rules applied."""
        result = dict(entry)
        for field, strategy, extra in self._rules:
            if field not in result:
                continue
            if strategy == "mask":
                result[field] = extra
            elif strategy == "remove":
                del result[field]
            elif strategy == "regex":
                compiled, replacement = extra
                result[field] = compiled.sub(replacement, str(result[field]))
        return result

    def stream(
        self, entries: Iterable[Dict[str, Any]]
    ) -> Iterator[Dict[str, Any]]:
        """Yield redacted copies of each entry in *entries*."""
        for entry in entries:
            yield self.apply(entry)
