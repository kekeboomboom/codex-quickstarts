# autonomous-coding

`autonomous-coding` is a long-running coding harness built with the Codex SDK.
It is meant to bootstrap a project, plan features, implement them in repeated sessions, and preserve progress across runs.

## Runtime Options

The harness supports two runtimes:

- `codex-sdk`: first-class runtime. Uses `@openai/codex-sdk` to start or resume Codex threads and run prompts against the target project.
- `codex-cli`: second-class fallback. Uses `codex exec` when you explicitly select `--runtime codex-cli` or when `auto` cannot load the SDK but can find an active Codex CLI login.

The Agents SDK / API-key route is intentionally not supported.
The SDK runtime requires Node.js 18 or newer and the npm dependencies in this directory.

## Quick Start

1. Install the SDK dependency.
2. Run the demo entrypoint against a project directory.

Example:

```bash
npm install
python3 autonomous_agent_demo.py --runtime codex-sdk --project-dir ./autonomous_demo_project
```

For fallback execution through `codex exec`:

```bash
python3 autonomous_agent_demo.py --runtime codex-cli --project-dir ./autonomous_demo_project
```

## Options

The harness is expected to support these controls:

- `--project-dir`: target workspace for the generated app
- `--max-iterations`: limit the number of autonomous rounds
- `--model`: model name used by the agent
- `--reasoning-effort`: reasoning budget selection
- `--runtime`: `auto`, `codex-sdk`, or `codex-cli`
- `--codex-sandbox`: Codex sandbox policy for SDK and CLI runtimes
- `--feature-count`: number of starter features to seed in the first pass

## Generated Files

The generated project is expected to include:

- `app_spec.txt`
- `feature_list.json`
- `init.sh`
- `codex-progress.txt`
- `.codex-thread.json`, which stores the resumable Codex SDK thread ID

The feature list is the source of truth for progress. Only the `passes` field should change after features are authored.

## Timing Expectations

The first run should spend time on project bootstrap, task discovery, and initial scaffolding.
Later runs should resume from saved state, verify already passing features, and continue the remaining work.
Longer projects may require multiple sessions. That is normal for this harness.

## Local Checks

Before running a long autonomous session, run the local checks below:

```bash
python3 -m compileall autonomous-coding
python3 -m pytest autonomous-coding
python3 autonomous-coding/autonomous_agent_demo.py --help
npm --prefix autonomous-coding install --package-lock-only
```
