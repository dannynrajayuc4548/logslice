"""Tests for logslice.flattener.LogFlattener."""
import pytest

from logslice.flattener import LogFlattener


def _e(**kwargs):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_separator_is_dot():
    assert LogFlattener().separator == "."


def test_custom_separator_stored():
    f = LogFlattener(separator="__")
    assert f.separator == "__"


def test_empty_separator_raises():
    with pytest.raises(ValueError, match="separator"):
        LogFlattener(separator="")


def test_default_max_depth_is_zero():
    assert LogFlattener().max_depth == 0


def test_custom_max_depth_stored():
    assert LogFlattener(max_depth=2).max_depth == 2


def test_negative_max_depth_raises():
    with pytest.raises(ValueError, match="max_depth"):
        LogFlattener(max_depth=-1)


def test_fields_none_by_default():
    assert LogFlattener().fields is None


def test_custom_fields_stored():
    f = LogFlattener(fields=["ctx"])
    assert f.fields == ["ctx"]


# ---------------------------------------------------------------------------
# Flattening behaviour
# ---------------------------------------------------------------------------

def test_flat_entry_unchanged():
    entry = {"level": "INFO", "msg": "hello"}
    result = list(LogFlattener().apply([entry]))
    assert result == [entry]


def test_single_level_nested_expanded():
    entry = {"level": "INFO", "ctx": {"user": "alice"}}
    result = list(LogFlattener().apply([entry]))[0]
    assert result == {"level": "INFO", "ctx.user": "alice"}


def test_deep_nested_expanded_by_default():
    entry = {"req": {"id": 1, "meta": {"ip": "127.0.0.1"}}}
    result = list(LogFlattener().apply([entry]))[0]
    assert result == {"req.id": 1, "req.meta.ip": "127.0.0.1"}


def test_custom_separator_used():
    entry = {"ctx": {"user": "bob"}}
    result = list(LogFlattener(separator="__").apply([entry]))[0]
    assert "ctx__user" in result


def test_max_depth_limits_expansion():
    entry = {"req": {"meta": {"ip": "10.0.0.1"}}}
    result = list(LogFlattener(max_depth=1).apply([entry]))[0]
    # depth=1 means we expand req -> req.meta, but req.meta is still a dict
    assert result["req.meta"] == {"ip": "10.0.0.1"}


def test_fields_filter_only_flattens_named_fields():
    entry = {"ctx": {"user": "alice"}, "extra": {"debug": True}}
    result = list(LogFlattener(fields=["ctx"]).apply([entry]))[0]
    assert "ctx.user" in result
    assert result["extra"] == {"debug": True}


def test_multiple_entries_all_processed():
    entries = [
        {"level": "INFO", "ctx": {"user": "alice"}},
        {"level": "ERROR", "ctx": {"user": "bob"}},
    ]
    results = list(LogFlattener().apply(entries))
    assert len(results) == 2
    assert results[0]["ctx.user"] == "alice"
    assert results[1]["ctx.user"] == "bob"


def test_non_dict_value_not_expanded():
    entry = {"tags": ["a", "b"], "count": 3}
    result = list(LogFlattener().apply([entry]))[0]
    assert result["tags"] == ["a", "b"]
    assert result["count"] == 3


def test_original_entry_not_mutated():
    entry = {"ctx": {"user": "alice"}}
    original = dict(entry)
    list(LogFlattener().apply([entry]))
    assert entry == original
