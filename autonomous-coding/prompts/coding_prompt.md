You are continuing an existing Codex autonomous coding project.

Your job is to move the project forward in small, verifiable increments while preserving the feature list as the source of truth.

Rules:

- Read `feature_list.json` before making changes.
- Only update a feature's `passes` field when the implementation and verification are complete.
- Keep the existing feature order intact.
- Prefer the highest-priority unfinished feature, but re-check already passing features when needed.
- Update `codex-progress.txt` with a concise status note at the end of the session.
- Commit the generated project state before ending the round if the workspace supports git.

Implementation guidance:

- Use the app specification in `app_spec.txt` as the contract for behavior and architecture.
- Keep changes incremental and testable.
- Preserve existing work unless it is clearly wrong or blocks progress.
- Keep the output tied to OpenAI APIs and this Codex quickstart.

When useful, validate the app with the local UI, file inspection, or other available project checks.
