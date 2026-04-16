from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from client import (
    _sdk_available,
    create_agent,
    create_sandbox_run_config,
)
from progress import count_passing_tests
from prompts import copy_spec_to_project, get_coding_prompt, get_initializer_prompt


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
    if _codex_cli_logged_in():
        return "codex-cli"
    if os.environ.get("OPENAI_API_KEY"):
        return "agents-sdk"
    return "codex-cli"


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


def run_autonomous_agent(
    project_dir,
    max_iterations=None,
    model="gpt-5.3-codex",
    reasoning_effort="high",
    sandbox="local",
    runtime="auto",
    codex_sandbox="workspace-write",
    feature_count=200,
):
    project_path = _normalize_project_dir(project_dir)
    copy_spec_to_project(project_path)
    selected_runtime = resolve_runtime(runtime)

    if selected_runtime == "codex-cli":
        iterations = 0
        feature_list_path = project_path / "feature_list.json"
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
                "[iteration {0}] {1} phase via Codex CLI, {2}/{3} features passing".format(
                    iterations, phase, passing, total
                ),
                flush=True,
            )
            _run_codex_cli_session(project_path, prompt, model, codex_sandbox)

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

    if not _sdk_available():
        raise RuntimeError(
            "openai-agents is not installed. Install the SDK before running the autonomous agent."
        )

    try:
        from agents import Runner
        from agents.run import RunConfig
    except Exception as exc:  # pragma: no cover - SDK runtime path only.
        raise RuntimeError("Unable to import the OpenAI Agents SDK runtime.") from exc

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY must be set before running the autonomous agent.")

    feature_list_path = project_path / "feature_list.json"
    iterations = 0
    final_output = None
    last_result = None
    previous_state = None

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
            "[iteration {0}] {1} phase, {2}/{3} features passing".format(
                iterations, phase, passing, total
            ),
            flush=True,
        )

        agent = create_agent(
            project_path,
            model=model,
            reasoning_effort=reasoning_effort,
            sandbox=sandbox,
            feature_count=feature_count,
            instructions=prompt,
        )
        run_config = RunConfig(
            sandbox=create_sandbox_run_config(project_path, sandbox=sandbox),
            workflow_name="Codex autonomous coding",
        )

        task = (
            "Continue the autonomous coding workflow for this project. "
            "Use the workspace instructions and update the project files in place."
        )
        last_result = Runner.run_sync(agent, task, run_config=run_config)
        final_output = getattr(last_result, "final_output", None)

        passing_after, total_after = _render_progress(project_path)
        current_state = (feature_list_path.exists(), passing_after, total_after)
        print(
            "[iteration {0}] completed with {1}/{2} features passing".format(
                iterations, passing_after, total_after
            ),
            flush=True,
        )

        if feature_list_path.exists() and total_after > 0 and passing_after >= total_after:
            break
        if max_iterations is None and not feature_list_path.exists() and previous_state == current_state:
            break

        previous_state = current_state

    return {
        "project_dir": str(project_path),
        "iterations": iterations,
        "runtime": selected_runtime,
        "final_output": final_output,
        "run_result": last_result,
        "passing_features": _render_progress(project_path)[0],
        "total_features": _render_progress(project_path)[1],
    }
