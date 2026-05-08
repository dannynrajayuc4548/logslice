"""Tests for LogPipeline with enricher integration."""

import json
import os
import tempfile

import pytest

from logslice.enricher import LogEnricher
from logslice.filters import RegexFilter
from logslice.formatters import JSONFormatter, PlainFormatter
from logslice.pipeline import LogPipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_tmp(lines):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
    for line in lines:
        f.write(line + "\n")
    f.flush()
    f.close()
    return f.name


# ---------------------------------------------------------------------------
# Basic pipeline
# ---------------------------------------------------------------------------

def test_no_filters_returns_all():
    path = _write_tmp(['{"level":"INFO","message":"a"}',
                       '{"level":"ERROR","message":"b"}'])
    try:
        results = LogPipeline(path).run()
        assert len(results) == 2
    finally:
        os.unlink(path)


def test_regex_filter_reduces_results():
    path = _write_tmp(['{"level":"INFO","message":"hello world"}',
                       '{"level":"ERROR","message":"goodbye"}'])
    try:
        results = LogPipeline(path).add_filter(RegexFilter("hello")).run()
        assert len(results) == 1
    finally:
        os.unlink(path)


def test_chaining_returns_self():
    path = _write_tmp([])
    try:
        p = LogPipeline(path)
        assert p.add_filter(RegexFilter("x")) is p
        assert p.set_formatter(JSONFormatter()) is p
        assert p.enrich("k", "v") is p
        assert p.set_field("level") is p
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Enrichment via pipeline
# ---------------------------------------------------------------------------

def test_enrich_adds_field_to_all_entries():
    path = _write_tmp(['{"level":"INFO","message":"hi"}',
                       '{"level":"WARN","message":"bye"}'])
    try:
        results = LogPipeline(path).enrich("env", "test").run()
        assert all(r["env"] == "test" for r in results)
    finally:
        os.unlink(path)


def test_enrich_callable_receives_entry():
    path = _write_tmp(['{"level":"info","message":"msg"}'])
    try:
        results = (
            LogPipeline(path)
            .enrich("LEVEL", lambda e: e["level"].upper())
            .run()
        )
        assert results[0]["LEVEL"] == "INFO"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Formatter integration
# ---------------------------------------------------------------------------

def test_json_formatter_output_is_string():
    path = _write_tmp(['{"level":"INFO","message":"hi"}'])
    try:
        results = LogPipeline(path).set_formatter(JSONFormatter()).run()
        assert isinstance(results[0], str)
        assert json.loads(results[0])["level"] == "INFO"
    finally:
        os.unlink(path)


def test_plain_formatter_output_is_string():
    path = _write_tmp(['{"level":"INFO","message":"hi"}'])
    try:
        results = LogPipeline(path).set_formatter(PlainFormatter()).run()
        assert isinstance(results[0], str)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# stream() terminal
# ---------------------------------------------------------------------------

def test_stream_is_lazy_iterator():
    path = _write_tmp(['{"level":"INFO","message":"a"}',
                       '{"level":"INFO","message":"b"}'])
    try:
        gen = LogPipeline(path).stream()
        first = next(gen)
        assert first["message"] == "a"
    finally:
        os.unlink(path)
