"""Summary report generation from aggregated log data."""

from typing import Dict, List, Optional
from logslice.aggregator import LogAggregator


class LogSummary:
    """Produces human-readable or structured summaries from a LogAggregator."""

    def __init__(self, aggregator: LogAggregator):
        self.aggregator = aggregator

    def as_dict(self) -> dict:
        """Return a structured summary dict with counts and top groups."""
        counts = self.aggregator.counts()
        total = sum(counts.values())
        return {
            "total": total,
            "groups": counts,
            "top": self.aggregator.top(5),
        }

    def as_text(self, title: Optional[str] = None) -> str:
        """Return a plain-text summary report."""
        data = self.as_dict()
        lines: List[str] = []
        if title:
            lines.append(title)
            lines.append("-" * len(title))
        lines.append(f"Total entries : {data['total']}")
        lines.append(f"Unique groups : {len(data['groups'])}")
        lines.append("")
        lines.append("Breakdown:")
        for key, count in sorted(data["groups"].items(), key=lambda x: x[1], reverse=True):
            pct = (count / data["total"] * 100) if data["total"] else 0
            lines.append(f"  {str(key):<20} {count:>6}  ({pct:.1f}%)")
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover
        return f"LogSummary(groups={list(self.aggregator.counts().keys())})"
