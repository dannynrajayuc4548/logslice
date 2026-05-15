"""Tests for logslice.checkpoint.LogCheckpoint."""

import json
import os
import pytest

from logslice.checkpoint import LogCheckpoint


@pytest.fixture()
def cp_path(tmp_path):
    return str(tmp_path / "ckpt.json")


# ---------------------------------------------------------------------------
# Construction / disk persistence
# ---------------------------------------------------------------------------

def test_new_checkpoint_file_does_not_exist_yet(cp_path):
    cp = LogCheckpoint(cp_path)
    assert cp.all() == {}


def test_save_creates_file(cp_path):
    cp = LogCheckpoint(cp_path)
    cp.save("/var/log/app.log", 1024)
    assert os.path.exists(cp_path)


def test_save_and_reload(cp_path):
    cp = LogCheckpoint(cp_path)
    cp.save("/var/log/app.log", 512)
    cp2 = LogCheckpoint(cp_path)
    assert cp2.load("/var/log/app.log") == 512


def test_file_contains_valid_json(cp_path):
    cp = LogCheckpoint(cp_path)
    cp.save("/var/log/x.log", 99)
    with open(cp_path) as fh:
        data = json.load(fh)
    assert data["/var/log/x.log"] == 99


# ---------------------------------------------------------------------------
# load / save semantics
# ---------------------------------------------------------------------------

def test_load_unknown_returns_none(cp_path):
    cp = LogCheckpoint(cp_path)
    assert cp.load("/nonexistent.log") is None


def test_save_updates_existing_entry(cp_path):
    cp = LogCheckpoint(cp_path)
    cp.save("/a.log", 10)
    cp.save("/a.log", 20)
    assert cp.load("/a.log") == 20


def test_save_negative_offset_raises(cp_path):
    cp = LogCheckpoint(cp_path)
    with pytest.raises(ValueError):
        cp.save("/a.log", -1)


def test_save_zero_offset_allowed(cp_path):
    cp = LogCheckpoint(cp_path)
    cp.save("/a.log", 0)
    assert cp.load("/a.log") == 0


# ---------------------------------------------------------------------------
# delete / clear
# ---------------------------------------------------------------------------

def test_delete_existing_returns_true(cp_path):
    cp = LogCheckpoint(cp_path)
    cp.save("/a.log", 5)
    assert cp.delete("/a.log") is True
    assert cp.load("/a.log") is None


def test_delete_nonexistent_returns_false(cp_path):
    cp = LogCheckpoint(cp_path)
    assert cp.delete("/ghost.log") is False


def test_delete_persists_to_disk(cp_path):
    """Deleting an entry should be reflected when the checkpoint is reloaded."""
    cp = LogCheckpoint(cp_path)
    cp.save("/a.log", 42)
    cp.delete("/a.log")
    cp2 = LogCheckpoint(cp_path)
    assert cp2.load("/a.log") is None


def test_clear_removes_all(cp_path):
    cp = LogCheckpoint(cp_path)
    cp.save("/a.log", 1)
    cp.save("/b.log", 2)
    cp.clear()
    assert cp.all() == {}


def test_clear_persists_to_disk(cp_path):
    cp = LogCheckpoint(cp_path)
    cp.save("/a.log", 1)
    cp.clear()
    cp2 = LogCheckpoint(cp_path)
    assert cp2.all() == {}


# ---------------------------------------------------------------------------
# all()
# ---------------------------------------------------------------------------

def test_all_returns_copy(cp_path):
    cp = LogCheckpoint(cp_path)
    cp.save("/a.log", 7)
    snapshot = cp.all()
    snapshot["/a.log"] = 999
    assert cp.load("/a.log") == 7  #
