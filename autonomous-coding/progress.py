from __future__ import annotations

import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))


def _normalize_project_dir(project_dir):
    path = Path(project_dir).expanduser()
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "generations":
        return path
    return Path("generations") / path


def _feature_list_path(project_dir):
    return _normalize_project_dir(project_dir) / "feature_list.json"


def _load_feature_list(project_dir):
    path = _feature_list_path(project_dir)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return []

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("features", "tests", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def count_passing_tests(project_dir):
    features = _load_feature_list(project_dir)
    count = 0
    for feature in features:
        if isinstance(feature, dict) and feature.get("passes"):
            count += 1
    return count, len(features)


def count_total_tests(project_dir):
    return count_passing_tests(project_dir)[1]
