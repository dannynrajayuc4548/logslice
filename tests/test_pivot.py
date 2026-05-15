"""Tests for LogPivot and PivotPipeline."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from logslice.pivot import LogPivot
from logslice.pivot_pipeline import PivotPipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entries():
    return [
        {"host": "web1", "level": "error"},
        {"host": "web1", "level": "warn"},
        {"host": "web1", "level": "error"},
        {"host": "web2", "level": "error"},
        {"host": "web2", "level": "info"},
    ]


def _write_log(entries):
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False
    )
    for e in entries:
        tmp.write(json.dumps(e) + "\n")
    tmp.close()
    return tmp.name


# ---------------------------------------------------------------------------
# LogPivot – construction
# ---------------------------------------------------------------------------

def test_default_row_field():
    p = LogPivot()
    assert p.row_field == "host"


def test_default_col_field():
    p = LogPivot()
    assert p.col_field == "level"


def test_custom_fields_stored():
    p = LogPivot(row_field="service", col_field="status")
    assert p.row_field == "service"
    assert p.col_field == "status"


def test_empty_row_field_raises():
    with pytest.raises(ValueError):
        LogPivot(row_field="")


def test_whitespace_row_field_raises():
    with pytest.raises(ValueError):
        LogPivot(row_field="   ")


def test_empty_col_field_raises():
    with pytest.raises(ValueError):
        LogPivot(col_field="")


def test_default_row_label():
    p = LogPivot()
    assert p.default_row == "unknown"


def test_custom_default_row_stored():
    p = LogPivot(default_row="n/a")
    assert p.default_row == "n/a"


# ---------------------------------------------------------------------------
# LogPivot – feed / table
# ---------------------------------------------------------------------------

def test_feed_returns_self():
    p = LogPivot()
    assert p.feed([]) is p


def test_columns_after_feed():
    p = LogPivot()
    p.feed(_entries())
    cols = p.columns()
    assert "error" in cols
    assert "warn" in cols
    assert "info" in cols


def test_rows_after_feed():
    p = LogPivot()
    p.feed(_entries())
    assert set(p.rows()) == {"web1", "web2"}


def test_table_counts_correct():
    p = LogPivot()
    p.feed(_entries())
    table = {r["host"]: r for r in p.table()}
    assert table["web1"]["error"] == 2
    assert table["web1"]["warn"] == 1
    assert table["web2"]["error"] == 1
    assert table["web2"]["info"] == 1


def test_table_fills_missing_cells():
    p = LogPivot()
    p.feed(_entries())
    table = {r["host"]: r for r in p.table(fill=0)}
    # web1 has no 'info' entry
    assert table["web1"]["info"] == 0


def test_cell_returns_correct_value():
    p = LogPivot()
    p.feed(_entries())
    assert p.cell("web1", "error") == 2


def test_cell_missing_returns_fill():
    p = LogPivot()
    p.feed(_entries())
    assert p.cell("web1", "debug", fill=-1) == -1


def test_missing_row_field_uses_default():
    p = LogPivot(default_row="anon")
    p.feed([{"level": "error"}])
    assert "anon" in p.rows()


def test_reset_clears_data():
    p = LogPivot()
    p.feed(_entries())
    p.reset()
    assert p.rows() == []
    assert p.columns() == []


def test_custom_agg_applied():
    agg = lambda cur, e: (cur or "") + e.get("msg", "")
    p = LogPivot(row_field="host", col_field="level", agg=agg)
    p.feed([
        {"host": "h1", "level": "error", "msg": "A"},
        {"host": "h1", "level": "error", "msg": "B"},
    ])
    assert p.cell("h1", "error") == "AB"


# ---------------------------------------------------------------------------
# PivotPipeline
# ---------------------------------------------------------------------------

def test_pipeline_attribute_is_log_pipeline():
    from logslice.pipeline import LogPipeline
    path = _write_log(_entries())
    try:
        pp = PivotPipeline(path)
        assert isinstance(pp.pipeline, LogPipeline)
    finally:
        os.unlink(path)


def test_pivot_attribute_is_log_pivot():
    path = _write_log(_entries())
    try:
        pp = PivotPipeline(path)
        assert isinstance(pp.pivot, LogPivot)
    finally:
        os.unlink(path)


def test_run_returns_list_of_dicts():
    path = _write_log(_entries())
    try:
        result = PivotPipeline(path).run()
        assert isinstance(result, list)
        assert all(isinstance(r, dict) for r in result)
    finally:
        os.unlink(path)


def test_run_produces_correct_counts():
    path = _write_log(_entries())
    try:
        result = PivotPipeline(path).run()
        table = {r["host"]: r for r in result}
        assert table["web1"]["error"] == 2
        assert table["web2"]["info"] == 1
    finally:
        os.unlink(path)


def test_add_filter_returns_self():
    from logslice.filters import RegexFilter
    path = _write_log(_entries())
    try:
        pp = PivotPipeline(path)
        assert pp.add_filter(RegexFilter("error")) is pp
    finally:
        os.unlink(path)


def test_columns_available_after_run():
    path = _write_log(_entries())
    try:
        pp = PivotPipeline(path)
        pp.run()
        assert "error" in pp.columns()
    finally:
        os.unlink(path)


def test_rows_available_after_run():
    path = _write_log(_entries())
    try:
        pp = PivotPipeline(path)
        pp.run()
        assert set(pp.rows()) == {"web1", "web2"}
    finally:
        os.unlink(path)
