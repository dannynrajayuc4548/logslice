"""AlertPipeline — convenience wrapper that wires a LogPipeline to a LogAlerter."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional

from logslice.alerter import LogAlerter
from logslice.pipeline import LogPipeline


class AlertPipeline:
    """Run a :class:`~logslice.pipeline.LogPipeline` and fire alerts on results.

    Example::

        ap = AlertPipeline("app.log")
        ap.add_alert(
            "errors",
            condition=lambda e: e.get("level") == "ERROR",
            callback=lambda name, e: print(name, e),
        )
        triggered = ap.run()
    """

    def __init__(self, log_path: str) -> None:
        self._pipeline: LogPipeline = LogPipeline(log_path)
        self._alerter: LogAlerter = LogAlerter()

    # ------------------------------------------------------------------
    # Delegation helpers
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def alerter(self) -> LogAlerter:
        return self._alerter

    def add_filter(self, f: Any) -> "AlertPipeline":
        self._pipeline.add_filter(f)
        return self

    def add_alert(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        callback: Callable[[str, Dict[str, Any]], None],
    ) -> "AlertPipeline":
        """Register an alert rule. Returns *self* for chaining."""
        self._alerter.add_rule(name, condition, callback)
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self) -> List[Dict[str, Any]]:
        """Execute the pipeline and evaluate alerts. Returns triggered records."""
        entries = list(self._pipeline.run())
        return self._alerter.feed(entries)
