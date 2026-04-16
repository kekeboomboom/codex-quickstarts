from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from agent import run_autonomous_agent


DEFAULT_PROJECT_DIR = "autonomous_demo_project"
REASONING_EFFORT_CHOICES = ("low", "medium", "high", "xhigh")
SANDBOX_CHOICES = ("local", "docker")
RUNTIME_CHOICES = ("auto", "agents-sdk", "codex-cli")
CODEX_SANDBOX_CHOICES = ("read-only", "workspace-write", "danger-full-access")


def normalize_project_dir(project_dir):
    """Normalize relative project directories under generations/."""
    path = Path(project_dir).expanduser()
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "generations":
        return path
    return Path("generations") / path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run the Codex autonomous coding harness.")
    parser.add_argument(
        "--project-dir",
        default=DEFAULT_PROJECT_DIR,
        help="Project directory to create or resume.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum number of autonomous iterations to run.",
    )
    parser.add_argument(
        "--model",
        default="gpt-5.3-codex",
        help="Model name to use for the run.",
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=REASONING_EFFORT_CHOICES,
        default="high",
        help="Reasoning effort to send with GPT-5 class models.",
    )
    parser.add_argument(
        "--sandbox",
        choices=SANDBOX_CHOICES,
        default="local",
        help="Agents SDK sandbox backend to use for the run.",
    )
    parser.add_argument(
        "--runtime",
        choices=RUNTIME_CHOICES,
        default="auto",
        help="Runtime to use: auto, agents-sdk, or codex-cli.",
    )
    parser.add_argument(
        "--codex-sandbox",
        choices=CODEX_SANDBOX_CHOICES,
        default="workspace-write",
        help="Codex CLI sandbox policy when --runtime codex-cli is selected.",
    )
    parser.add_argument(
        "--feature-count",
        type=int,
        default=200,
        help="Number of features to request during initialization.",
    )
    args = parser.parse_args(argv)
    return args


def main(argv=None):
    args = parse_args(argv)
    project_dir = normalize_project_dir(args.project_dir)
    run_autonomous_agent(
        project_dir=project_dir,
        max_iterations=args.max_iterations,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        sandbox=args.sandbox,
        runtime=args.runtime,
        codex_sandbox=args.codex_sandbox,
        feature_count=args.feature_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
