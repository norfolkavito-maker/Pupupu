# Prompt 04 — Release / Polish (PLACEHOLDER)

> Replace this placeholder with the real prompt.

## Status

- Status: placeholder

## Role

You are a senior coding agent focusing on release readiness and polish.

## Scope

- Changelog/release notes
- Packaging / portability constraints
- Small UX/documentation improvements tied to requirements

## Requirements

- Preserve existing behavior unless explicitly changed.
- Keep changes minimal and reviewable.
- Ensure documentation is updated for user-visible changes.
- Ensure release artifacts do not include secrets or dev-only junk.

## Non-goals

- Do not add new features unrelated to release tasks.

## Existing behavior to preserve

- Current versioning/tagging conventions.
- Existing CI workflows unless required by task.

## Files/modules likely involved

- `CHANGELOG.md`
- `release/*`
- `.github/workflows/*`

## Acceptance criteria

- Release/polish requirements implemented.

## Verification

```text
./scripts/agent-verify.ps1
bash scripts/agent-verify.sh
```

## Notes

- Replace this placeholder with the real prompt.
