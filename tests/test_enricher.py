"""Tests for logslice.enricher.LogEnricher."""

import pytest

from logslice.enricher import LogEnricher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(**kw):
    base = {"level": "INFO", "message": "hello"}
    base.update(kw)
    return base


# ---------------------------------------------------------------------------
# add / remove
# ---------------------------------------------------------------------------

def test_add_static_value():
    e = LogEnricher()
    e.add("env", "prod")
    result = e.apply(_entry())
    assert result["env"] == "prod"


def test_add_callable():
    e = LogEnricher()
    e.add("upper", lambda entry: entry["level"].upper())
    result = e.apply(_entry(level="info"))
    assert result["upper"] == "INFO"


def test_add_returns_self_for_chaining():
    e = LogEnricher()
    assert e.add("k", "v") is e


def test_remove_strips_key():
    e = LogEnricher()
    e.add("env", "prod").add("host", "box")
    e.remove("env")
    assert "env" not in e.rule_keys
    assert "host" in e.rule_keys


def test_remove_returns_self():
    e = LogEnricher()
    e.add("k", 1)
    assert e.remove("k") is e


def test_empty_key_raises():
    e = LogEnricher()
    with pytest.raises(ValueError):
        e.add("", "value")


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------

def test_apply_does_not_mutate_original():
    e = LogEnricher().add("env", "staging")
    original = _entry()
    copy = dict(original)
    e.apply(original)
    assert original == copy


def test_apply_multiple_rules():
    e = LogEnricher()
    e.add("a", 1).add("b", 2)
    result = e.apply(_entry())
    assert result["a"] == 1 and result["b"] == 2


def test_later_rule_overwrites_earlier():
    e = LogEnricher()
    e.add("env", "dev").add("env", "prod")
    result = e.apply(_entry())
    assert result["env"] == "prod"


# ---------------------------------------------------------------------------
# enrich (streaming)
# ---------------------------------------------------------------------------

def test_enrich_yields_all_entries():
    e = LogEnricher().add("tag", "x")
    entries = [_entry(), _entry(message="world")]
    out = list(e.enrich(entries))
    assert len(out) == 2


def test_enrich_each_entry_has_field():
    e = LogEnricher().add("src", "file.log")
    out = list(e.enrich([_entry(), _entry()]))
    assert all(r["src"] == "file.log" for r in out)


def test_enrich_skip_errors_continues_on_bad_callable():
    def boom(entry):
        raise RuntimeError("oops")

    e = LogEnricher().add("bad", boom)
    entries = [_entry(), _entry()]
    out = list(e.enrich(entries, skip_errors=True))
    # original entries returned unchanged on error
    assert len(out) == 2
    assert all("bad" not in r for r in out)


def test_enrich_raises_by_default_on_error():
    e = LogEnricher().add("bad", lambda _: (_ for _ in ()).throw(ValueError("x")))
    with pytest.raises(Exception):
        list(e.enrich([_entry()]))


# ---------------------------------------------------------------------------
# rule_keys
# ---------------------------------------------------------------------------

def test_rule_keys_order_preserved():
    e = LogEnricher()
    e.add("z", 1).add("a", 2).add("m", 3)
    assert e.rule_keys == ["z", "a", "m"]
