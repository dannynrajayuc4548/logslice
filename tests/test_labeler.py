"""Tests for logslice.labeler.LogLabeler."""
import pytest
from logslice.labeler import LogLabeler


def _e(**kw):
    return {"message": "hello", "level": "INFO", **kw}


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_starts_with_no_labels():
    assert LogLabeler().keys == []


def test_add_returns_self_for_chaining():
    lb = LogLabeler()
    assert lb.add("env", "prod") is lb


def test_empty_key_raises():
    with pytest.raises(ValueError):
        LogLabeler().add("", "value")


def test_whitespace_key_raises():
    with pytest.raises(ValueError):
        LogLabeler().add("   ", "value")


# ---------------------------------------------------------------------------
# Keys property
# ---------------------------------------------------------------------------

def test_keys_reflect_insertion_order():
    lb = LogLabeler().add("a", 1).add("b", 2).add("c", 3)
    assert lb.keys == ["a", "b", "c"]


def test_remove_drops_key():
    lb = LogLabeler().add("env", "prod").add("region", "us")
    lb.remove("env")
    assert lb.keys == ["region"]


def test_remove_missing_key_is_noop():
    lb = LogLabeler().add("env", "prod")
    lb.remove("nonexistent")  # should not raise
    assert lb.keys == ["env"]


# ---------------------------------------------------------------------------
# Static labels
# ---------------------------------------------------------------------------

def test_static_string_label_attached():
    lb = LogLabeler().add("env", "staging")
    result = list(lb.apply([_e()]))
    assert result[0]["env"] == "staging"


def test_static_numeric_label_attached():
    lb = LogLabeler().add("version", 42)
    result = list(lb.apply([_e()]))
    assert result[0]["version"] == 42


def test_static_none_label_attached():
    lb = LogLabeler().add("optional", None)
    result = list(lb.apply([_e()]))
    assert result[0]["optional"] is None


# ---------------------------------------------------------------------------
# Callable labels
# ---------------------------------------------------------------------------

def test_callable_label_receives_entry():
    lb = LogLabeler().add("msg_len", lambda e: len(e.get("message", "")))
    entry = _e(message="hi")
    result = list(lb.apply([entry]))
    assert result[0]["msg_len"] == 2


def test_callable_label_can_derive_from_existing_field():
    lb = LogLabeler().add("upper_level", lambda e: e.get("level", "").upper())
    result = list(lb.apply([_e(level="error")]))
    assert result[0]["upper_level"] == "ERROR"


# ---------------------------------------------------------------------------
# Immutability / no mutation
# ---------------------------------------------------------------------------

def test_apply_does_not_mutate_original():
    lb = LogLabeler().add("env", "prod")
    original = _e()
    original_copy = dict(original)
    list(lb.apply([original]))
    assert original == original_copy


def test_apply_returns_new_dict_per_entry():
    """Each entry yielded by apply should be a distinct dict object."""
    lb = LogLabeler().add("env", "prod")
    entry = _e()
    results = list(lb.apply([entry]))
    assert results[0] is not entry
