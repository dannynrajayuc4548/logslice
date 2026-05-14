"""LogTagger – attach tags to log entries based on field patterns."""
from __future__ import annotations

import re
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Union


class LogTagger:
    """Attach one or more string tags to log entries based on rules.

    Each rule is a (tag, predicate) pair.  The predicate receives a log-entry
    dict and must return a truthy value for the tag to be applied.

    Tags are accumulated in the ``tags`` field (a list).  If the field already
    exists and is a list, new tags are appended; otherwise it is replaced.
    """

    def __init__(self, tag_field: str = "tags") -> None:
        if not tag_field:
            raise ValueError("tag_field must be a non-empty string")
        self._tag_field = tag_field
        self._rules: List[tuple[str, Callable[[dict], bool]]] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def tag_field(self) -> str:
        return self._tag_field

    @property
    def rules(self) -> List[tuple[str, Callable[[dict], bool]]]:
        return list(self._rules)

    # ------------------------------------------------------------------
    # Rule builders
    # ------------------------------------------------------------------

    def add_rule(
        self,
        tag: str,
        predicate: Callable[[dict], bool],
    ) -> "LogTagger":
        """Add a custom predicate rule."""
        if not tag:
            raise ValueError("tag must be a non-empty string")
        self._rules.append((tag, predicate))
        return self

    def tag_if_matches(
        self,
        tag: str,
        field: str,
        pattern: Union[str, re.Pattern],
    ) -> "LogTagger":
        """Add a rule that tags entries where *field* matches *pattern*."""
        compiled = re.compile(pattern) if isinstance(pattern, str) else pattern
        return self.add_rule(
            tag, lambda entry: bool(compiled.search(str(entry.get(field, ""))))
        )

    def tag_if_field_equals(
        self, tag: str, field: str, value: object
    ) -> "LogTagger":
        """Add a rule that tags entries where *field* equals *value*."""
        return self.add_rule(tag, lambda entry: entry.get(field) == value)

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    def apply(self, entry: dict) -> dict:
        """Return a *copy* of *entry* with matching tags attached."""
        result = dict(entry)
        existing = result.get(self._tag_field)
        accumulated: List[str] = list(existing) if isinstance(existing, list) else []
        for tag, predicate in self._rules:
            if predicate(entry) and tag not in accumulated:
                accumulated.append(tag)
        result[self._tag_field] = accumulated
        return result

    def stream(
        self, entries: Iterable[dict]
    ) -> Iterator[dict]:
        """Yield tagged copies of every entry in *entries*."""
        for entry in entries:
            yield self.apply(entry)
