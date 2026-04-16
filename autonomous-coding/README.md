# autonomous-coding

`autonomous-coding` is a long-running coding harness built with the OpenAI Agents SDK Sandbox Agents workflow.
It is meant to bootstrap a project, plan features, implement them in repeated sessions, and preserve progress across runs.

## Runtime Options

The harness supports two runtimes:

- `codex-cli`: uses your local Codex CLI login, including ChatGPT account login. This is the default when `codex login status` reports an active login.
- `agents-sdk`: uses the OpenAI Agents SDK Sandbox Agents runtime and requires `OPENAI_API_KEY`.

Both modes need a workspace that can be used as a sandbox root. The Agents SDK runtime requires Python 3.10 or newer.

## Quick Start

1. Confirm Codex CLI is logged in with `codex login status`.
2. Run the demo entrypoint against a project directory.

Example:

```bash
python autonomous_agent_demo.py --runtime codex-cli --project-dir ./autonomous_demo_project
```

If you have API credentials and want the SDK sandbox runtime:

```bash
export OPENAI_API_KEY="..."
python autonomous_agent_demo.py --runtime agents-sdk --project-dir ./autonomous_demo_project
```

## Options

The harness is expected to support these controls:

- `--project-dir`: target workspace for the generated app
- `--max-iterations`: limit the number of autonomous rounds
- `--model`: model name used by the agent
- `--reasoning-effort`: reasoning budget selection
- `--sandbox`: sandbox backend selection
- `--runtime`: `auto`, `codex-cli`, or `agents-sdk`
- `--codex-sandbox`: Codex CLI sandbox policy for `codex-cli` runtime
- `--feature-count`: number of starter features to seed in the first pass

## Generated Files

The generated project is expected to include:

- `app_spec.txt`
- `feature_list.json`
- `init.sh`
- `codex-progress.txt`
- a sandbox snapshot or equivalent resume state

The feature list is the source of truth for progress. Only the `passes` field should change after features are authored.

## Timing Expectations

The first run should spend time on project bootstrap, task discovery, and initial scaffolding.
Later runs should resume from saved state, verify already passing features, and continue the remaining work.
Longer projects may require multiple sessions. That is normal for this harness.

## Local Checks

Before running a long autonomous session, run the local checks below:

```bash
python -m compileall autonomous-coding
pytest autonomous-coding
python autonomous-coding/autonomous_agent_demo.py --help
```
