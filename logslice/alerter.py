"""LogAlerter — trigger callbacks when log entries match defined conditions."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional


class Alert:
    """Holds the definition of a single alert rule."""

    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        callback: Callable[[str, Dict[str, Any]], None],
    ) -> None:
        self.name = name
        self.condition = condition
        self.callback = callback


class LogAlerter:
    """Evaluate alert rules against a stream of log entries.

    Example usage::

        alerter = LogAlerter()
        alerter.add_rule(
            "high-error",
            condition=lambda e: e.get("level") == "ERROR",
            callback=lambda name, entry: print(f"[{name}] {entry}"),
        )
        alerter.feed(entries)
    """

    def __init__(self) -> None:
        self._rules: List[Alert] = []
        self._triggered: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def add_rule(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        callback: Callable[[str, Dict[str, Any]], None],
    ) -> "LogAlerter":
        """Register a new alert rule. Returns *self* for chaining."""
        if not name:
            raise ValueError("Alert name must be a non-empty string.")
        self._rules.append(Alert(name, condition, callback))
        return self

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def feed(self, entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate all rules against *entries*.

        Matching entries are passed to the rule's callback and recorded
        in :attr:`triggered`.  Returns the list of triggered entries.
        """
        self._triggered.clear()
        for entry in entries:
            for rule in self._rules:
                try:
                    if rule.condition(entry):
                        rule.callback(rule.name, entry)
                        self._triggered.append({"rule": rule.name, "entry": entry})
                except Exception:  # noqa: BLE001 — never crash the stream
                    pass
        return list(self._triggered)

    @property
    def triggered(self) -> List[Dict[str, Any]]:
        """Records from the most recent :meth:`feed` call."""
        return list(self._triggered)

    @property
    def rule_names(self) -> List[str]:
        """Names of all registered rules in insertion order."""
        return [r.name for r in self._rules]
