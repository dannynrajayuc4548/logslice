"""Tests for logslice.zipper.LogZipper."""
import pytest

from logslice.zipper import LogZipper


def _left(*pairs):
    return [{"request_id": k, "left_val": v} for k, v in pairs]


def _right(*pairs):
    return [{"request_id": k, "right_val": v} for k, v in pairs]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_field_is_request_id():
    z = LogZipper()
    assert z.field == "request_id"


def test_custom_field_stored():
    z = LogZipper(field="trace_id")
    assert z.field == "trace_id"


def test_empty_field_raises():
    with pytest.raises(ValueError, match="field"):
        LogZipper(field="")


def test_whitespace_field_raises():
    with pytest.raises(ValueError, match="field"):
        LogZipper(field="   ")


def test_default_how_is_inner():
    z = LogZipper()
    assert z.how == "inner"


def test_invalid_how_raises():
    with pytest.raises(ValueError, match="how"):
        LogZipper(how="full")


def test_default_right_prefix():
    z = LogZipper()
    assert z.right_prefix == "right_"


def test_custom_prefixes_stored():
    z = LogZipper(left_prefix="l_", right_prefix="r_")
    assert z.left_prefix == "l_"
    assert z.right_prefix == "r_"


# ---------------------------------------------------------------------------
# inner join
# ---------------------------------------------------------------------------

def test_inner_keeps_only_matched():
    z = LogZipper(how="inner")
    left = _left(("a", 1), ("b", 2))
    right = _right(("b", 10), ("c", 30))
    results = list(z.zip(left, right))
    assert len(results) == 1
    result = results[0]
    assert result["request_id"] == "b"


def test_inner_merges_fields():
    z = LogZipper(how="inner", right_prefix="r_")
    left = [{"request_id": "x", "msg": "hello"}]
    right = [{"request_id": "x", "msg": "world"}]
    result = list(z.zip(left, right))[0]
    # left takes precedence (no prefix by default)
    assert result["msg"] == "hello"
    assert result["r_msg"] == "world"


# ---------------------------------------------------------------------------
# left join
# ---------------------------------------------------------------------------

def test_left_keeps_all_left_entries():
    z = LogZipper(how="left")
    left = _left(("a", 1), ("b", 2))
    right = _right(("b", 10))
    keys = {r["request_id"] for r in z.zip(left, right)}
    assert keys == {"a", "b"}


def test_left_excludes_right_only_entries():
    z = LogZipper(how="left")
    left = _left(("a", 1))
    right = _right(("a", 10), ("z", 99))
    keys = {r["request_id"] for r in z.zip(left, right)}
    assert "z" not in keys


# ---------------------------------------------------------------------------
# right join
# ---------------------------------------------------------------------------

def test_right_keeps_all_right_entries():
    z = LogZipper(how="right")
    left = _left(("a", 1))
    right = _right(("a", 10), ("c", 30))
    keys = {r["request_id"] for r in z.zip(left, right)}
    assert keys == {"a", "c"}


# ---------------------------------------------------------------------------
# outer join
# ---------------------------------------------------------------------------

def test_outer_keeps_all_entries():
    z = LogZipper(how="outer")
    left = _left(("a", 1), ("b", 2))
    right = _right(("b", 10), ("c", 30))
    keys = {r["request_id"] for r in z.zip(left, right)}
    assert keys == {"a", "b", "c"}


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_left_inner_yields_nothing():
    z = LogZipper(how="inner")
    assert list(z.zip([], _right(("a", 1)))) == []


def test_empty_both_yields_nothing():
    z = LogZipper(how="outer")
    assert list(z.zip([], [])) == []


def test_duplicate_keys_last_write_wins():
    """If a stream has duplicate keys the last entry for that key is used."""
    z = LogZipper(how="inner")
    left = [
        {"request_id": "a", "val": 1},
        {"request_id": "a", "val": 2},
    ]
    right = [{"request_id": "a", "rval": 9}]
    result = list(z.zip(left, right))
    assert len(result) == 1
    assert result[0]["val"] == 2
