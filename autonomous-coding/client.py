from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    from agents.sandbox import Manifest, SandboxRunConfig
    from agents.sandbox.entries import LocalDir
    from agents.sandbox.sandboxes.unix_local import UnixLocalSandboxClient
except Exception:  # pragma: no cover - exercised when SDK is unavailable.
    Manifest = None
    SandboxRunConfig = None
    LocalDir = None
    UnixLocalSandboxClient = None

try:  # pragma: no cover - optional docker extension.
    from agents.sandbox.sandboxes.docker import DockerSandboxClient, DockerSandboxClientOptions
except Exception:  # pragma: no cover - optional dependency.
    DockerSandboxClient = None
    DockerSandboxClientOptions = None


class _StubManifest:
    def __init__(self, root="/workspace", entries=None, environment=None, users=None, groups=None):
        self.root = root
        self.entries = {} if entries is None else entries
        self.environment = {} if environment is None else environment
        self.users = [] if users is None else users
        self.groups = [] if groups is None else groups


class _StubSandboxRunConfig:
    def __init__(
        self,
        client=None,
        options=None,
        session=None,
        session_state=None,
        manifest=None,
        snapshot=None,
        concurrency_limits=None,
    ):
        self.client = client
        self.options = options
        self.session = session
        self.session_state = session_state
        self.manifest = manifest
        self.snapshot = snapshot
        self.concurrency_limits = concurrency_limits


class _StubSandboxAgent:
    def __init__(self, name, instructions, model="gpt-5.3-codex", model_settings=None, default_manifest=None):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.model_settings = model_settings
        self.default_manifest = default_manifest


class _StubRunConfig:
    def __init__(self, model="gpt-5.3-codex", sandbox=None):
        self.model = model
        self.sandbox = sandbox


class _StubLocalSnapshotSpec:
    def __init__(self, base_path):
        self.base_path = base_path


def _normalize_project_dir(project_dir):
    path = Path(project_dir).expanduser()
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "generations":
        return path
    return Path("generations") / path


def _workspace_root(project_dir, sandbox):
    project_path = _normalize_project_dir(project_dir).resolve()
    if sandbox == "docker":
        return Path("/workspace") / project_path.name
    return project_path


def _sdk_available():
    return (
        Manifest is not None
        and SandboxRunConfig is not None
        and UnixLocalSandboxClient is not None
    )


def _build_reasoning_settings(reasoning_effort):
    try:
        from agents import ModelSettings
    except Exception:  # pragma: no cover - optional SDK dependency.
        return None
    # The SDK serializes ModelSettings to the provider request. A dict keeps this
    # compatible across minor OpenAI package type-location changes.
    return ModelSettings(reasoning={"effort": reasoning_effort})


def create_manifest(project_dir, sandbox="local"):
    project_path = _normalize_project_dir(project_dir).resolve()
    workspace_root = _workspace_root(project_dir, sandbox)

    if Manifest is None:
        return _StubManifest(root=str(workspace_root))

    entries = {}
    if sandbox == "docker" and LocalDir is not None:
        entries["project"] = LocalDir(src=project_path)

    return Manifest(root=str(workspace_root), entries=entries)


def create_sandbox_run_config(project_dir, sandbox="local"):
    manifest = create_manifest(project_dir, sandbox=sandbox)
    project_path = _normalize_project_dir(project_dir).resolve()
    snapshot_path = project_path / ".codex-snapshot"

    if SandboxRunConfig is None:
        client = object()
        if sandbox == "docker" and DockerSandboxClient is None:
            client = None
        return _StubSandboxRunConfig(
            client=client,
            manifest=manifest,
            snapshot=_StubLocalSnapshotSpec(base_path=snapshot_path),
        )

    if sandbox == "docker":
        if DockerSandboxClient is None:
            raise RuntimeError(
                "Docker sandbox requested, but the optional DockerSandboxClient is not available."
            )
        try:
            from docker import from_env as docker_from_env
        except Exception as exc:
            raise RuntimeError(
                "Docker sandbox requested, but the docker Python package is not installed."
            ) from exc
        client = DockerSandboxClient(docker_from_env())
        options = (
            DockerSandboxClientOptions(image="node:22-bookworm")
            if DockerSandboxClientOptions is not None
            else None
        )
    else:
        client = UnixLocalSandboxClient()
        options = None

    snapshot_cls = _StubLocalSnapshotSpec
    try:
        from agents.sandbox.snapshot import LocalSnapshotSpec
        snapshot_cls = LocalSnapshotSpec
    except Exception:  # pragma: no cover - fallback for older SDK shapes.
        pass

    return SandboxRunConfig(
        client=client,
        options=options,
        manifest=manifest,
        snapshot=snapshot_cls(base_path=snapshot_path),
    )


def create_agent(
    project_dir,
    model="gpt-5.3-codex",
    reasoning_effort="high",
    sandbox="local",
    feature_count=200,
    instructions=None,
):
    from prompts import get_coding_prompt

    project_path = _normalize_project_dir(project_dir).resolve()
    workspace_root = _workspace_root(project_dir, sandbox)
    if instructions is None:
        instructions = get_coding_prompt()

    prompt = (
        "Workspace root: "
        + str(workspace_root)
        + "\nProject directory on the host: "
        + str(project_path)
        + "\nFeature target: "
        + str(int(feature_count))
        + "\n\n"
        + instructions
    )

    model_settings = _build_reasoning_settings(reasoning_effort)

    if Manifest is None:
        return _StubSandboxAgent(
            name="Codex Autonomous Coding Agent",
            instructions=prompt,
            model=model,
            model_settings=model_settings,
            default_manifest=create_manifest(project_dir, sandbox=sandbox),
        )

    try:
        from agents.sandbox import SandboxAgent
    except Exception as exc:  # pragma: no cover - real SDK path only.
        raise RuntimeError("openai-agents is installed, but SandboxAgent could not be imported.") from exc

    return SandboxAgent(
        name="Codex Autonomous Coding Agent",
        instructions=prompt,
        model=model,
        model_settings=model_settings,
        default_manifest=create_manifest(project_dir, sandbox=sandbox),
    )


def _render_progress(project_dir):
    try:
        from progress import count_passing_tests
    except Exception:
        return 0, 0
    return count_passing_tests(project_dir)


def run_autonomous_agent(
    project_dir,
    max_iterations=None,
    model="gpt-5.3-codex",
    reasoning_effort="high",
    sandbox="local",
    feature_count=200,
):
    project_path = _normalize_project_dir(project_dir)
    from prompts import copy_spec_to_project, get_coding_prompt, get_initializer_prompt

    copy_spec_to_project(project_path)

    if not _sdk_available():
        raise RuntimeError(
            "openai-agents is not installed. Install the SDK before running the autonomous agent."
        )

    try:
        import os
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

        passing, total = _render_progress(project_path)
        print(
            "[iteration {0}] completed with {1}/{2} features passing".format(
                iterations, passing, total
            ),
            flush=True,
        )

        if feature_list_path.exists() and total > 0 and passing >= total:
            break
        if max_iterations is None and not feature_list_path.exists():
            continue

    return {
        "project_dir": str(project_path),
        "iterations": iterations,
        "final_output": final_output,
        "run_result": last_result,
        "passing_features": _render_progress(project_path)[0],
        "total_features": _render_progress(project_path)[1],
    }
