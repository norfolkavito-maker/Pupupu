# PROGRESS

## Current status

- Status: Not started
- Current milestone: Phase 0 — Read and plan
- Last verification: Not run

## Milestones

- [ ] Phase 0 — Read and plan
- [ ] Phase 1 — Implement safely (milestone-by-milestone)
- [ ] Phase 2 — Self-review
- [ ] Finalize — DoD + Acceptance checklist + Verification

## Change log

Use one entry per milestone.

### 2026-05-03 11:45 — Add CONTEXT_MAP and enforce reading/maintenance rules

- Scope:
  - Created `docs/ai/CONTEXT_MAP.md` (concise repository navigation map).
  - Updated agent workflow rules to require reading `CONTEXT_MAP.md` before broad exploration and maintaining it when structure changes.
  - Updated acceptance checklist with CONTEXT_MAP global checkboxes.
- Files changed:
  - docs/ai/CONTEXT_MAP.md
  - AGENTS.md
  - docs/ai/MASTER_TASK.md
  - LOCAL_AGENT_START_HERE.md
  - docs/ai/OTHER_AGENT_RULES.md
  - docs/ai/AGENT_COMMANDS.md
  - .github/copilot-instructions.md
  - .github/instructions/agent-general.instructions.md
  - .github/prompts/local-full-task.prompt.md
  - .github/prompts/self-review.prompt.md
  - .windsurf/rules/agent-general.md
  - .windsurf/rules/project-local-workflow.md
  - docs/ai/ACCEPTANCE_CHECKLIST.md
- Verification:
  - Command(s):
    - (pending) `bash scripts/agent-verify.sh`
  - Result: PENDING
- Notes:
  - No project logic changed (docs/rules only).
- Next step:
  - Run verification and commit changes.

### Milestone — Added AI Workflow Documentation

- Date: 2026-05-03
- Goal: Add repository navigation and staged workflow docs for agents.
- Files changed:
  - docs/ai/CONTEXT_MAP.md
  - docs/ai/MASTER_TASK.md
  - docs/ai/PROGRESS.md
  - docs/ai/ACCEPTANCE_CHECKLIST.md
  - docs/ai/BLOCKERS.md
  - docs/ai/workflows/README.md
  - docs/ai/workflows/01_stabilization_fixes_test10.md
  - docs/ai/workflows/02_test_engine_performance.md
  - docs/ai/workflows/03_tray_and_menu_ux.md
  - AGENTS.md
  - LOCAL_AGENT_START_HERE.md
  - docs/ai/OTHER_AGENT_RULES.md
  - docs/ai/AGENT_COMMANDS.md
  - .github/* agent rules/prompts
  - .windsurf/rules/*
- What changed:
  - Added stable project navigation map.
  - Added staged workflow docs under `docs/ai/workflows/`.
  - Updated agent rules to read and maintain `CONTEXT_MAP.md` and follow workflow stage order.
  - No project logic changed.
- Verification command:
  - Docs-only check + `bash scripts/agent-verify.sh`
- Verification result:
  - Pending
- Remaining work:
  - Execute workflow Stage 1 (stabilization) when requested.

### YYYY-MM-DD HH:MM — <milestone title>

- Scope:
  - ...
- Files changed:
  - ...
- Verification:
  - Command(s):
    - ...
  - Result: PASS/FAIL
- Notes:
  - ...
- Next step:
  - ...

### 2026-05-03 13:03 — Fix Problem Domains recording from control test

- Scope:
  - Restored backward-compatible API `add_from_domain_checks(...)` so control test baseline can record failing domains into `problem_domains.json`.
- Files changed:
  - `app/zapret_manager/features/problem_domains.py`
- Verification:
  - Command(s):
    - `python3 -m pytest -q tests/test_control_test_menu_unittest.py -q`
    - `python3 -m unittest tests.test_control_test_menu_unittest -v`
  - Result: PASS
- Notes:
  - Minimal change: compatibility helper delegates to canonical v2 storage.
  - No menu/UX redesign.
- Next step:
  - Stage 1 / Task 2: Flowseal asset resolution.

### 2026-05-03 14:35 — Fix Flowseal placeholder mapping for upstream BIN/LISTS

- Scope:
  - Fixed Flowseal `.bat` parsing so `%BIN%` / `%LISTS%` placeholders map to upstream-local paths (`{FLOWSEAL_BIN}` / `{FLOWSEAL_LISTS}`), instead of runtime `{BIN}` / manager `{LISTS}`.
  - This is required for imported Flowseal strategies to resolve assets under `DedZapretData/data/upstreams/flowseal/{bin,lists}`.
- Files changed:
  - `app/zapret_manager/strategies/flowseal_parser.py`
  - `tests/test_flowseal_parser_unittest.py`
- Verification:
  - Command(s):
    - `python3 -m pytest -q tests/test_flowseal_parser_unittest.py -q`
    - `python3 -m pytest -q tests/test_winws_validate_unittest.py -q`
  - Result: PASS
- Commit:
  - `5ee1eb0` — `fix(flowseal): map BIN/LISTS placeholders to upstream paths`
- Next step:
  - Stage 1 / Task 3: Runtime assets repair from upstreams.

### 2026-05-03 14:41 — Repair runtime assets using Flowseal upstreams

- Scope:
  - Extended runtime asset repair so it can source missing assets from Flowseal upstream directories:
    - Fake `.bin` assets from `DedZapretData/data/upstreams/flowseal/bin`
    - List assets (currently `list-general.txt`) from `DedZapretData/data/upstreams/flowseal/lists`
  - Guardrails preserved:
    - no downloads;
    - no empty fake `.bin` creation.
- Files changed:
  - `app/zapret_manager/features/runtime_assets.py`
  - `tests/test_runtime_assets_lists_repair_unittest.py`
  - `tests/test_runtime_assets_fake_repair_unittest.py`
- Verification:
  - Command(s):
    - `python3 -m pytest -q tests/test_runtime_assets_lists_repair_unittest.py -q`
    - `python3 -m pytest -q tests/test_runtime_assets_fake_repair_unittest.py -q`
    - `python3 -m pytest -q tests/test_runtime_assets_repair_unittest.py -q`
  - Result: PASS
- Commit:
  - `a88b915` — `fix(runtime-assets): repair fake/list assets from flowseal upstream`
- Next step:
  - Stage 1 / Task 4: `quic_initial_ietf.bin` in games profiles / overlays.

### 2026-05-03 14:47 — Fix missing quic_initial_ietf.bin for discord quic4all overlay

- Scope:
  - Replaced reference to non-existent `{FAKE:quic_initial_ietf.bin}` in the `quic4all` discord script overlay with existing `{FAKE:quic_initial_www_google_com.bin}`.
  - This avoids false INVALID preflight due to missing fake asset.
- Files changed:
  - `app/zapret_manager/strategies/composer.py`
- Verification:
  - Command(s):
    - `python3 -m pytest -q tests/test_composer_unittest.py -q`
    - `python3 -m pytest -q tests/test_winws_validate_unittest.py -q`
  - Result: PASS
- Commit:
  - `dc75303` — `fix(runtime): avoid missing quic_initial_ietf fake asset for discord quic4all`
- Next step:
  - Continue Stage 1 stabilization tasks (diagnostics decoding / sing-box health / bug report artifacts / etc.).

### 2026-05-03 14:59 — Fix Windows diagnostics output decoding (OEM/cp866 fallback)

- Scope:
  - Introduced best-effort decoding helper for Windows subprocess output to avoid mojibake in diagnostics/bug report (`ipconfig`, `route`, `netsh`).
  - Switched bug report network snapshot runner to bytes mode + decoding fallback.
  - Added a unit test asserting cp866 fallback works.
- Files changed:
  - `app/zapret_manager/utils/subprocessx.py`
  - `app/zapret_manager/core/report.py`
  - `tests/test_windows_decode_cp866_unittest.py`
- Verification:
  - Command(s):
    - `python3 -m pytest -q tests/test_windows_decode_cp866_unittest.py -q`
    - `python3 -m pytest -q tests/test_bug_report_unittest.py -q`
  - Result: PASS
- Commit:
  - `849f207` — `fix(diagnostics): decode Windows command output with OEM fallback`
- Next step:
  - Stage 1 / Task 6: sing-box nodes health schema/load errors report.

### 2026-05-03 15:16 — sing-box health: report nodes file schema and load errors

- Scope:
  - Extended sing-box health report with nodes file diagnostics:
    - `nodes_file_exists`, `nodes_file_size`, `nodes_schema_detected`, `load_nodes_error`.
  - Added `subscriptions_count` (enabled) to health report.
  - Improved recommendation text for the case when `nodes.json` exists and has size but parsing returns zero nodes.
  - Updated formatter + unit tests.
- Files changed:
  - `app/zapret_manager/features/singbox_health.py`
  - `tests/test_singbox_health_report_unittest.py`
- Verification:
  - Command(s):
    - `python3 -m pytest -q tests/test_singbox_health_report_unittest.py -q`
  - Result: PASS
- Commit:
  - `487f7b1` — `feat(singbox): report nodes file schema and load errors`
- Next step:
  - Stage 1 / Task 7: include strategy and node summaries in bug reports (no raw links/URLs).

### 2026-05-03 22:02 — Strategy test: show N/A for unmeasured metrics

- Scope:
  - Fixed misleading `0/N` metrics display for DNS/TCP/PING/UDP when a probe wasn't executed.
  - `TestResult.summary_text()` now prints `N/A` for unmeasured metrics, and preserves `0/N` only when metric was actually measured.
- Files changed:
  - `app/zapret_manager/features/strategy_test.py`
  - `tests/test_strategy_metrics_na_unittest.py`
- Verification:
  - Command(s):
    - `python3 -m pytest -q tests/test_strategy_metrics_na_unittest.py -q`
    - `python3 -m pytest -q tests/test_test_all_strategies_with_progress_unittest.py -q`
  - Result: PASS
- Next step:
  - Stage 1 / Task 9: Runtime preflight false file checks.

### 2026-05-03 22:19 — Runtime preflight: avoid false file checks for hex/modifiers

- Scope:
  - Preflight validator no longer treats common non-path tokens (e.g. `0x...` hex masks and `none`) as file paths.
  - Extended path heuristic to include certificate/key extensions (`.pem/.crt/.cer/.key`).
  - Added unit tests to ensure `--dpi-desync-ttl=0x0F0F0F0F` and `--dpi-desync-fooling=none` do not trigger `missing file`.
- Files changed:
  - `app/zapret_manager/features/zapret_runtime.py`
  - `tests/test_winws_validate_unittest.py`
- Verification:
  - Command(s):
    - `python3 -m pytest -q tests/test_winws_validate_unittest.py -q`
    - `bash scripts/agent-verify.sh`
  - Result: PASS
- Next step:
  - Continue Stage 1 stabilization tasks (next from workflow list).

## Final summary template

When the task is complete, fill this section.

- What was implemented:
  - ...
- Files created/changed:
  - ...
- Verification:
  - ...
- Future / Planned:
  - ...
- Blockers:
  - ...
