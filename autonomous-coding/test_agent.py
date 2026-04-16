from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module(name: str, filename: str):
    path = ROOT / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


agent = load_module("autonomous_agent_runtime", "agent.py")


def test_resolve_runtime_prefers_codex_sdk(monkeypatch):
    monkeypatch.setattr(agent, "_codex_sdk_available", lambda: True)
    monkeypatch.setattr(agent, "_codex_cli_logged_in", lambda: True)

    assert agent.resolve_runtime("auto") == "codex-sdk"


def test_resolve_runtime_falls_back_to_codex_cli(monkeypatch):
    monkeypatch.setattr(agent, "_codex_sdk_available", lambda: False)
    monkeypatch.setattr(agent, "_codex_cli_logged_in", lambda: True)

    assert agent.resolve_runtime("auto") == "codex-cli"


def test_resolve_runtime_defaults_to_sdk_when_no_runtime_is_ready(monkeypatch):
    monkeypatch.setattr(agent, "_codex_sdk_available", lambda: False)
    monkeypatch.setattr(agent, "_codex_cli_logged_in", lambda: False)

    assert agent.resolve_runtime("auto") == "codex-sdk"


def test_resolve_runtime_respects_explicit_runtime(monkeypatch):
    monkeypatch.setattr(agent, "_codex_sdk_available", lambda: True)
    monkeypatch.setattr(agent, "_codex_cli_logged_in", lambda: True)

    assert agent.resolve_runtime("codex-cli") == "codex-cli"
