from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module(name: str, filename: str):
    path = ROOT / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


progress = load_module("autonomous_progress", "progress.py")


def test_count_passing_tests_missing_file_returns_zero_tuple(tmp_path):
    assert progress.count_passing_tests(tmp_path) == (0, 0)


def test_count_passing_tests_invalid_json_returns_zero_tuple(tmp_path):
    (tmp_path / "feature_list.json").write_text("{not-json", encoding="utf-8")

    assert progress.count_passing_tests(tmp_path) == (0, 0)


def test_count_passing_tests_counts_passing_and_total(tmp_path):
    payload = [
        {"name": "feature one", "passes": True},
        {"name": "feature two", "passes": False},
        {"name": "feature three"},
    ]
    (tmp_path / "feature_list.json").write_text(json.dumps(payload), encoding="utf-8")

    assert progress.count_passing_tests(tmp_path) == (1, 3)
