"""Tests for LogSummary."""

import pytest
from logslice.aggregator import LogAggregator
from logslice.summary import LogSummary


ENTRIES = [
    {"level": "INFO",  "message": "a"},
    {"level": "INFO",  "message": "b"},
    {"level": "WARN",  "message": "c"},
    {"level": "ERROR", "message": "d"},
]


def _make_summary() -> LogSummary:
    agg = LogAggregator(key="level")
    agg.feed(ENTRIES)
    return LogSummary(agg)


def test_as_dict_total():
    s = _make_summary()
    data = s.as_dict()
    assert data["total"] == 4


def test_as_dict_groups():
    s = _make_summary()
    data = s.as_dict()
    assert data["groups"]["INFO"] == 2
    assert data["groups"]["WARN"] == 1


def test_as_dict_top():
    s = _make_summary()
    data = s.as_dict()
    assert data["top"][0][0] == "INFO"


def test_as_text_contains_total():
    s = _make_summary()
    text = s.as_text()
    assert "Total entries" in text
    assert "4" in text


def test_as_text_with_title():
    s = _make_summary()
    text = s.as_text(title="My Report")
    assert text.startswith("My Report")
    assert "---" in text


def test_as_text_percentages():
    s = _make_summary()
    text = s.as_text()
    assert "50.0%" in text  # INFO is 2/4 = 50%


def test_empty_aggregator():
    agg = LogAggregator(key="level")
    s = LogSummary(agg)
    data = s.as_dict()
    assert data["total"] == 0
    assert data["groups"] == {}
    text = s.as_text()
    assert "0" in text
