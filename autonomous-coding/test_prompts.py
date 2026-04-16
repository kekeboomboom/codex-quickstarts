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


prompts = load_module("autonomous_prompts", "prompts.py")


def test_initializer_prompt_renders_feature_count_and_removes_placeholder():
    prompt = prompts.get_initializer_prompt(42)

    assert "42" in prompt
    assert "{{FEATURE_COUNT}}" not in prompt


def test_prompts_do_not_contain_claude_specific_strings():
    initializer_prompt = prompts.get_initializer_prompt(7)
    coding_prompt = prompts.get_coding_prompt()

    for prompt in (initializer_prompt, coding_prompt):
        assert "ANTHROPIC_API_KEY" not in prompt
        assert "claude-sonnet-4-5-20250929" not in prompt
        assert ".claude_settings.json" not in prompt


def test_copy_spec_to_project_creates_app_spec_file(tmp_path):
    prompts.copy_spec_to_project(tmp_path)

    spec_file = tmp_path / "app_spec.txt"
    assert spec_file.exists()
    assert spec_file.read_text(encoding="utf-8").strip()
