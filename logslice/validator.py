"""Schema-based validation for structured log entries."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional


class ValidationError(Exception):
    """Raised when an entry fails validation and raise_on_error is True."""


class LogValidator:
    """Validate log entries against a set of field rules.

    Rules are callables that receive the field value and return True/False.
    Missing required fields always fail validation.

    Example::

        v = (
            LogValidator()
            .require("level")
            .require("message")
            .add_rule("level", lambda v: v in {"INFO", "WARN", "ERROR"})
        )
        valid, invalid = v.partition(entries)
    """

    def __init__(self, raise_on_error: bool = False) -> None:
        self._required: List[str] = []
        self._rules: Dict[str, List[Callable[[Any], bool]]] = {}
        self._raise = raise_on_error

    # ------------------------------------------------------------------
    # Builder helpers
    # ------------------------------------------------------------------

    def require(self, field: str) -> "LogValidator":
        """Mark *field* as required (must be present and non-None)."""
        if field not in self._required:
            self._required.append(field)
        return self

    def add_rule(
        self, field: str, rule: Callable[[Any], bool]
    ) -> "LogValidator":
        """Attach a validation *rule* callable to *field*."""
        self._rules.setdefault(field, []).append(rule)
        return self

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def is_valid(self, entry: Dict[str, Any]) -> bool:
        """Return True if *entry* passes all rules."""
        for field in self._required:
            if entry.get(field) is None:
                return False
        for field, rules in self._rules.items():
            value = entry.get(field)
            for rule in rules:
                if not rule(value):
                    return False
        return True

    def validate(self, entries: Iterable[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Yield only entries that pass validation.

        If *raise_on_error* was set, raise :class:`ValidationError` on the
        first invalid entry instead of silently dropping it.
        """
        for entry in entries:
            if self.is_valid(entry):
                yield entry
            elif self._raise:
                raise ValidationError(f"Entry failed validation: {entry}")

    def partition(
        self, entries: Iterable[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split *entries* into (valid, invalid) lists."""
        valid: List[Dict[str, Any]] = []
        invalid: List[Dict[str, Any]] = []
        for entry in entries:
            (valid if self.is_valid(entry) else invalid).append(entry)
        return valid, invalid
