from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from progress import count_passing_tests
from prompts import copy_spec_to_project, get_coding_prompt, get_initializer_prompt

CODEX_SDK_RUNNER = CURRENT_DIR / "codex_sdk_runner.mjs"


def _normalize_project_dir(project_dir):
    path = Path(project_dir).expanduser()
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "generations":
        return path
    return Path("generations") / path


def _render_progress(project_dir):
    return count_passing_tests(project_dir)


def _codex_cli_available():
    return shutil.which("codex") is not None


def _node_available():
    return shutil.which("node") is not None


def _codex_sdk_available():
    if not _node_available():
        return False
    result = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            "import('@openai/codex-sdk')",
        ],
        cwd=CURRENT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _codex_cli_logged_in():
    if not _codex_cli_available():
        return False
    result = subprocess.run(
        ["codex", "login", "status"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result.returncode == 0 and "Logged in" in result.stdout


def resolve_runtime(runtime):
    if runtime != "auto":
        return runtime
    if _codex_sdk_available():
        return "codex-sdk"
    if _codex_cli_logged_in():
        return "codex-cli"
    return "codex-sdk"


def _run_codex_sdk_session(project_dir, prompt, model, reasoning_effort, codex_sandbox):
    if not _node_available():
        raise RuntimeError(
            "Codex SDK runtime requested, but Node.js was not found on PATH. "
            "Install Node.js 18 or newer before running this harness."
        )
    if not CODEX_SDK_RUNNER.exists():
        raise RuntimeError("Codex SDK runner is missing: {0}".format(CODEX_SDK_RUNNER))
    if not _codex_sdk_available():
        raise RuntimeError(
            "Codex SDK runtime requested, but @openai/codex-sdk is not installed. "
            "Run `npm install` inside autonomous-coding before running this harness."
        )

    project_path = _normalize_project_dir(project_dir).resolve()
    state_file = project_path / ".codex-thread.json"
    command = [
        "node",
        str(CODEX_SDK_RUNNER),
        "--project-dir",
        str(project_path),
        "--state-file",
        str(state_file),
        "--model",
        model,
        "--reasoning-effort",
        reasoning_effort,
        "--sandbox",
        codex_sandbox,
    ]
    result = subprocess.run(
        command,
        input=prompt,
        text=True,
        check=False,
        cwd=CURRENT_DIR,
    )
    if result.returncode != 0:
        raise RuntimeError("Codex SDK session failed with exit code {0}.".format(result.returncode))
    return result


def _run_codex_cli_session(project_dir, prompt, model, codex_sandbox):
    if not _codex_cli_available():
        raise RuntimeError(
            "Codex CLI runtime requested, but the `codex` command was not found on PATH."
        )
    if not _codex_cli_logged_in():
        raise RuntimeError(
            "Codex CLI runtime requested, but Codex is not logged in. Run `codex login` first."
        )

    command = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--cd",
        str(project_dir),
        "--sandbox",
        codex_sandbox,
        "--model",
        model,
        "-",
    ]
    result = subprocess.run(command, input=prompt, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError("Codex CLI session failed with exit code {0}.".format(result.returncode))
    return result


def _run_runtime_session(project_dir, prompt, selected_runtime, model, reasoning_effort, codex_sandbox):
    if selected_runtime == "codex-sdk":
        return _run_codex_sdk_session(
            project_dir=project_dir,
            prompt=prompt,
            model=model,
            reasoning_effort=reasoning_effort,
            codex_sandbox=codex_sandbox,
        )
    if selected_runtime == "codex-cli":
        return _run_codex_cli_session(
            project_dir=project_dir,
            prompt=prompt,
            model=model,
            codex_sandbox=codex_sandbox,
        )
    raise RuntimeError(
        "Unsupported runtime `{0}`. Use `auto`, `codex-sdk`, or `codex-cli`.".format(
            selected_runtime
        )
    )


def _runtime_label(selected_runtime):
    if selected_runtime == "codex-sdk":
        return "Codex SDK"
    if selected_runtime == "codex-cli":
        return "Codex CLI"
    return selected_runtime


def run_autonomous_agent(
    project_dir,
    max_iterations=None,
    model="gpt-5.3-codex",
    reasoning_effort="high",
    runtime="auto",
    codex_sandbox="workspace-write",
    feature_count=200,
):
    project_path = _normalize_project_dir(project_dir)
    copy_spec_to_project(project_path)
    selected_runtime = resolve_runtime(runtime)

    feature_list_path = project_path / "feature_list.json"
    iterations = 0

    while True:
        if max_iterations is not None and iterations >= max_iterations:
            break

        iterations += 1
        passing, total = _render_progress(project_path)
        if not feature_list_path.exists():
            prompt = get_initializer_prompt(feature_count)
            phase = "initializer"
            total = int(feature_count)
        else:
            prompt = get_coding_prompt()
            phase = "coding"

        print(
            "[iteration {0}] {1} phase via {2}, {3}/{4} features passing".format(
                iterations,
                phase,
                _runtime_label(selected_runtime),
                passing,
                total,
            ),
            flush=True,
        )

        _run_runtime_session(
            project_dir=project_path,
            prompt=prompt,
            selected_runtime=selected_runtime,
            model=model,
            reasoning_effort=reasoning_effort,
            codex_sandbox=codex_sandbox,
        )

        passing_after, total_after = _render_progress(project_path)
        print(
            "[iteration {0}] completed with {1}/{2} features passing".format(
                iterations, passing_after, total_after
            ),
            flush=True,
        )

        if feature_list_path.exists() and total_after > 0 and passing_after >= total_after:
            break

    passing, total = _render_progress(project_path)
    return {
        "project_dir": str(project_path),
        "iterations": iterations,
        "runtime": selected_runtime,
        "passing_features": passing,
        "total_features": total,
    }
