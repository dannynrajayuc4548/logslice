"""LogMasker – field-level masking with pattern-based and full redaction rules."""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple


class LogMasker:
    """Apply masking transformations to log entry fields.

    Each rule targets a specific field and replaces matching content with a
    placeholder, leaving non-matching content intact.
    """

    def __init__(self, placeholder: str = "***") -> None:
        if not placeholder:
            raise ValueError("placeholder must be a non-empty string")
        self._placeholder = placeholder
        self._rules: List[Tuple[str, Callable[[str], str]]] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def placeholder(self) -> str:
        return self._placeholder

    @property
    def rules(self) -> List[Tuple[str, str]]:
        """Return a list of (field, description) tuples for inspection."""
        return [(field, desc) for field, _, desc in self._rules]  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Rule builders
    # ------------------------------------------------------------------

    def mask_pattern(self, field: str, pattern: str, flags: int = 0) -> "LogMasker":
        """Replace every regex *match* within *field* with the placeholder."""
        if not field:
            raise ValueError("field must be a non-empty string")
        compiled = re.compile(pattern, flags)
        ph = self._placeholder

        def _apply(value: str) -> str:
            return compiled.sub(ph, value)

        self._rules.append((field, _apply, f"pattern:{pattern}"))  # type: ignore[arg-type]
        return self

    def mask_full(self, field: str) -> "LogMasker":
        """Replace the entire value of *field* with the placeholder."""
        if not field:
            raise ValueError("field must be a non-empty string")
        ph = self._placeholder

        def _apply(value: str) -> str:  # noqa: ARG001
            return ph

        self._rules.append((field, _apply, "full"))  # type: ignore[arg-type]
        return self

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def apply(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Return a new dict with masking rules applied."""
        result = dict(entry)
        for field, fn, _ in self._rules:  # type: ignore[misc]
            if field in result and isinstance(result[field], str):
                result[field] = fn(result[field])
        return result

    def stream(self, entries: Iterable[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Yield masked copies of each entry."""
        for entry in entries:
            yield self.apply(entry)
