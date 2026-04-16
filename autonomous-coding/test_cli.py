from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent


def load_module(name: str, filename: str):
    path = ROOT / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


autonomous_agent_demo = load_module("autonomous_agent_demo", "autonomous_agent_demo.py")


def test_normalize_project_dir_places_relative_paths_under_generations(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    normalized = autonomous_agent_demo.normalize_project_dir("foo")

    assert normalized == Path("generations/foo")


def test_normalize_project_dir_leaves_absolute_paths_unchanged(tmp_path):
    absolute = tmp_path / "demo"

    assert autonomous_agent_demo.normalize_project_dir(str(absolute)) == absolute


def test_normalize_project_dir_does_not_double_prefix_generations(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    normalized = autonomous_agent_demo.normalize_project_dir("generations/foo")

    assert normalized == Path("generations/foo")


def test_parse_args_supports_help(capsys):
    with pytest.raises(SystemExit) as excinfo:
        autonomous_agent_demo.parse_args(["--help"])

    captured = capsys.readouterr()

    assert excinfo.value.code == 0
    assert "usage:" in captured.out.lower()


def test_parse_args_defaults_match_plan():
    args = autonomous_agent_demo.parse_args([])

    assert args.project_dir == "autonomous_demo_project"
    assert args.max_iterations is None
    assert args.model == "gpt-5.3-codex"
    assert args.reasoning_effort == "high"
    assert args.runtime == "auto"
    assert args.codex_sandbox == "workspace-write"
    assert args.feature_count == 200


def test_parse_args_rejects_agents_sdk_runtime():
    with pytest.raises(SystemExit):
        autonomous_agent_demo.parse_args(["--runtime", "agents-sdk"])
