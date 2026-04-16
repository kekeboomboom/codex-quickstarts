from __future__ import annotations

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))


PROMPTS_DIR = CURRENT_DIR / "prompts"


def _normalize_project_dir(project_dir):
    path = Path(project_dir).expanduser()
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "generations":
        return path
    return Path("generations") / path


def _load_prompt_file(name):
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def get_initializer_prompt(feature_count):
    prompt = _load_prompt_file("initializer_prompt.md")
    return prompt.replace("{{FEATURE_COUNT}}", str(int(feature_count)))


def get_coding_prompt():
    return _load_prompt_file("coding_prompt.md")


def copy_spec_to_project(project_dir):
    project_path = _normalize_project_dir(project_dir)
    project_path.mkdir(parents=True, exist_ok=True)
    spec_path = project_path / "app_spec.txt"
    if not spec_path.exists():
        spec_path.write_text(_load_prompt_file("app_spec.txt") + "\n", encoding="utf-8")
    return spec_path
