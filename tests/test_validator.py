"""Tests for LogValidator."""
import pytest

from logslice.validator import LogValidator, ValidationError


def _entry(**kwargs):
    base = {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "ok"}
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# require()
# ---------------------------------------------------------------------------

def test_require_passes_when_field_present():
    v = LogValidator().require("level")
    assert v.is_valid(_entry())


def test_require_fails_when_field_missing():
    v = LogValidator().require("level")
    assert not v.is_valid({"message": "no level"})


def test_require_fails_when_field_is_none():
    v = LogValidator().require("level")
    assert not v.is_valid({"level": None, "message": "x"})


# ---------------------------------------------------------------------------
# add_rule()
# ---------------------------------------------------------------------------

def test_add_rule_passes_for_valid_value():
    v = LogValidator().add_rule("level", lambda val: val in {"INFO", "ERROR"})
    assert v.is_valid(_entry(level="ERROR"))


def test_add_rule_fails_for_invalid_value():
    v = LogValidator().add_rule("level", lambda val: val in {"INFO", "ERROR"})
    assert not v.is_valid(_entry(level="DEBUG"))


def test_multiple_rules_all_must_pass():
    v = (
        LogValidator()
        .add_rule("level", lambda val: isinstance(val, str))
        .add_rule("level", lambda val: val.isupper())
    )
    assert v.is_valid(_entry(level="INFO"))
    assert not v.is_valid(_entry(level="info"))


# ---------------------------------------------------------------------------
# validate()
# ---------------------------------------------------------------------------

def test_validate_yields_only_valid_entries():
    v = LogValidator().require("level")
    entries = [_entry(), {"message": "no level"}, _entry(level="WARN")]
    result = list(v.validate(entries))
    assert len(result) == 2


def test_validate_raise_on_error_raises():
    v = LogValidator(raise_on_error=True).require("level")
    with pytest.raises(ValidationError):
        list(v.validate([{"message": "missing level"}]))


def test_validate_no_raise_drops_invalid_silently():
    v = LogValidator(raise_on_error=False).require("level")
    result = list(v.validate([{"message": "missing level"}]))
    assert result == []


# ---------------------------------------------------------------------------
# partition()
# ---------------------------------------------------------------------------

def test_partition_splits_correctly():
    v = LogValidator().require("level")
    entries = [_entry(), {"message": "x"}, _entry()]
    valid, invalid = v.partition(entries)
    assert len(valid) == 2
    assert len(invalid) == 1


def test_partition_all_valid():
    v = LogValidator().require("message")
    entries = [_entry(), _entry(message="another")]
    valid, invalid = v.partition(entries)
    assert invalid == []


def test_partition_all_invalid():
    v = LogValidator().require("nonexistent")
    valid, invalid = v.partition([_entry(), _entry()])
    assert valid == []
    assert len(invalid) == 2


# ---------------------------------------------------------------------------
# chaining / builder
# ---------------------------------------------------------------------------

def test_require_returns_self_for_chaining():
    v = LogValidator()
    assert v.require("level") is v


def test_add_rule_returns_self_for_chaining():
    v = LogValidator()
    assert v.add_rule("level", lambda x: True) is v
