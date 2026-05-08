"""Pre-built validator factories for common log schemas."""
from __future__ import annotations

from logslice.validator import LogValidator

_VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL"}


def standard_schema(
    require_timestamp: bool = True,
    require_level: bool = True,
    require_message: bool = True,
    strict_level: bool = False,
) -> LogValidator:
    """Return a :class:`~logslice.validator.LogValidator` for a typical
    structured log entry.

    Parameters
    ----------
    require_timestamp:
        Enforce presence of a ``timestamp`` field.
    require_level:
        Enforce presence of a ``level`` field.
    require_message:
        Enforce presence of a ``message`` field.
    strict_level:
        When *True*, also validate that ``level`` is one of the well-known
        severity strings (DEBUG / INFO / WARNING / WARN / ERROR / CRITICAL).
    """
    v = LogValidator()
    if require_timestamp:
        v.require("timestamp")
    if require_level:
        v.require("level")
    if require_message:
        v.require("message")
    if strict_level:
        v.add_rule("level", lambda val: val in _VALID_LEVELS)
    return v


def minimal_schema() -> LogValidator:
    """Return a validator that only requires a ``message`` field."""
    return LogValidator().require("message")
