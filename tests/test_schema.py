"""Tests for pre-built schema factories."""
from logslice.schema import minimal_schema, standard_schema
from logslice.validator import LogValidator


def _entry(**kwargs):
    base = {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "hi"}
    base.update(kwargs)
    return base


def test_standard_schema_returns_validator():
    assert isinstance(standard_schema(), LogValidator)


def test_standard_schema_valid_entry_passes():
    v = standard_schema()
    assert v.is_valid(_entry())


def test_standard_schema_missing_timestamp_fails():
    v = standard_schema(require_timestamp=True)
    assert not v.is_valid({"level": "INFO", "message": "x"})


def test_standard_schema_missing_level_fails():
    v = standard_schema(require_level=True)
    assert not v.is_valid({"timestamp": "t", "message": "x"})


def test_standard_schema_missing_message_fails():
    v = standard_schema(require_message=True)
    assert not v.is_valid({"timestamp": "t", "level": "INFO"})


def test_standard_schema_strict_level_rejects_unknown():
    v = standard_schema(strict_level=True)
    assert not v.is_valid(_entry(level="VERBOSE"))


def test_standard_schema_strict_level_accepts_known():
    v = standard_schema(strict_level=True)
    for lvl in ("DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL"):
        assert v.is_valid(_entry(level=lvl)), f"Expected {lvl!r} to be valid"


def test_standard_schema_no_requirements():
    v = standard_schema(
        require_timestamp=False, require_level=False, require_message=False
    )
    assert v.is_valid({})


def test_minimal_schema_returns_validator():
    assert isinstance(minimal_schema(), LogValidator)


def test_minimal_schema_passes_with_message():
    v = minimal_schema()
    assert v.is_valid({"message": "hello"})


def test_minimal_schema_fails_without_message():
    v = minimal_schema()
    assert not v.is_valid({"level": "INFO"})
