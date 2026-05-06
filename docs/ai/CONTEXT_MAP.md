# Context Map

## Purpose

This file is a **concise navigation map** for coding agents.
It exists to reduce repeated “scan the whole repository” behavior by providing
stable entry points, key modules, and commands.

It is **not** a progress log and **not** a task checklist.

## Maintenance rules

- Read this file before broad repository exploration.
- Update this file when project structure changes.
- Update this file when important entry points, modules, commands, paths, or workflows change.
- Keep it concise.
- Do not copy large code blocks.
- Do not include secrets.
- Do not use this file to track task progress.
- Task progress belongs in `docs/ai/PROGRESS.md`.
- Acceptance status belongs in `docs/ai/ACCEPTANCE_CHECKLIST.md`.
- Blockers belong in `docs/ai/BLOCKERS.md`.
- Completed checklist items must not be deleted.

## Quick start for agents

Recommended read order:
1. `AGENTS.md`
2. `LOCAL_AGENT_START_HERE.md`
3. `docs/ai/MASTER_TASK.md`
4. `docs/ai/CONTEXT_MAP.md`
5. `docs/ai/workflows/README.md`
6. `docs/ai/PROGRESS.md`
7. `docs/ai/ACCEPTANCE_CHECKLIST.md`
8. `docs/ai/BLOCKERS.md`

Verify command:
- macOS/Linux: `bash scripts/agent-verify.sh`
- Windows: `./scripts/agent-verify.ps1`

Where to track things:
- Progress: `docs/ai/PROGRESS.md`
- Acceptance checklist: `docs/ai/ACCEPTANCE_CHECKLIST.md`
- Blockers: `docs/ai/BLOCKERS.md`

## Repository overview

- Project type: Python application repository.
- Main language: Python.
- Test frameworks detected: `unittest` (and `pytest` via `pytest.ini`).
- High-level purpose (detectable from file names): Windows-focused console UI tool around
  “zapret / winws” runtime + optional `sing-box` features.

Main runtime entry points:
- `run.bat` (Windows wrapper)
- `app/zapret_manager/__main__.py` (Python module entry)
- `app/zapret_manager/main.py` (application bootstrap)

## Entry points

- App module entry:
  - `app/zapret_manager/__main__.py`
  - `app/zapret_manager/main.py`
- UI entry:
  - `app/zapret_manager/ui/main_menu.py`
  - `app/zapret_manager/ui/menus.py`
- Windows runner:
  - `run.bat`

## Important modules

### Core

- `app/zapret_manager/core/` — central app glue (context, commands, config, state, diagnostics).
  - `core/commands.py` — command execution layer + results.
  - `core/config.py` — config loading/validation.
  - `core/paths.py` — path layout / portable roots.
  - `core/state.py`, `core/current_state.py` — runtime state snapshots.
  - `core/diagnostics.py`, `core/report.py` — diagnostics + reporting.

### UI / GUI

- `app/zapret_manager/ui/` — console menus, colors, tray integration.
  - `ui/menus.py` — menu routing.
  - `ui/main_menu.py` — main menu screen.
  - `ui/tray.py` — tray-related integration.
- `app/zapret_manager/tray/` — optional system tray layer (lazy `pystray/Pillow`).
  - `tray_app.py` — tray lifecycle + refresh loop
  - `tray_menu.py` — menu spec builder + action router (calls `core/commands.py`)
  - `tray_status.py` — status mapping to tray tooltip/level
  - `tray_icons.py` — icon generation (lazy Pillow)
  - `tray_worker.py` — single-job worker for long tray actions

### Proxy / networking / sing-box / zapret

- `app/zapret_manager/features/zapret_runtime.py` — winws/zapret runtime management.
- `app/zapret_manager/features/tg_proxy.py` — Telegram proxy feature.
- `app/zapret_manager/core/singbox/` — sing-box integration.
  - `core/singbox/binary.py` — sing-box binary handling.
  - `core/singbox/process.py` — process management.
  - `core/singbox/system_proxy_win.py` — Windows proxy backup/restore.
  - `core/singbox/subscriptions.py` — subscription storage/parsing.

### Diagnostics / logs / reports

- `app/zapret_manager/core/diagnostics.py` — diagnostics gathering.
- `app/zapret_manager/features/diagnostics_artifacts.py` — extra artifacts for bug reports.
- `app/zapret_manager/features/dump.py` — dumps/export.

### State / config / storage

- `config.yaml` — main configuration file (repo root).
- `app/zapret_manager/core/paths.py` — defines portable/data roots.
- `app/zapret_manager/core/state.py` — state model.
- `app/zapret_manager/features/strategy_conflicts.py` — conflict detection for strategy/layer combinations (UX helper).

### Updates / release / packaging

- `app/zapret_manager/features/app_update.py`
- `app/zapret_manager/features/app_update_v2.py`
- `release/` — release notes.
- `.github/workflows/` — CI pipelines.

### Tests

- `tests/` — unit tests.
- Naming convention: `tests/test_*_unittest.py` for unittest-discoverable suite.
- `pytest.ini` exists, so pytest runs are supported.

### Scripts / tools

- `scripts/agent-verify.ps1` — agent verification (Windows).
- `scripts/agent-verify.sh` — agent verification (macOS/Linux).

## Data, config, state, logs

Documented/detectable stable paths:

- Repo config:
  - `config.yaml`
- Lists / strategy data:
  - `data/strategies/` (built-in strategy YAMLs)
  - `data/lists/` (domain/IP lists)
- Runtime portable data root:
  - **Unknown** (likely derived in `app/zapret_manager/core/paths.py`; check that file when working on storage paths).
- Logs/state/backups:
  - **Unknown** (search in `core/paths.py`, `core/log.py`, `core/state.py`).

## Build, run, test, verify commands

Install dependencies:
- Documented: `pip install -r requirements.txt`
- Detected: `requirements-dev.txt` exists (dev deps).

Run app:
- Documented: `python -m app.zapret_manager` (module entry)
- Documented: `run.bat` (Windows)

Run tests:
- Detected (unittest): `python -m unittest discover -s tests -p "*_unittest.py"`
- Detected (pytest): `python -m pytest -q`

Lint:
- Unknown (no lint script detected in repository root).

Build/package:
- Unknown in this repo snapshot (check `.github/workflows/*.yml`).

Full agent verification:
- Detected:
  - `bash scripts/agent-verify.sh`
  - `./scripts/agent-verify.ps1`

## CI / release workflow

- GitHub Actions workflows:
  - `.github/workflows/build.yml`
  - `.github/workflows/check.yml`
- Release notes:
  - `release/`
- Artifacts:
  - Unknown without inspecting workflow YAML content (see `.github/workflows/*.yml`).

## Agent workflow files

- `AGENTS.md` — universal agent rules.
- `LOCAL_AGENT_START_HERE.md` — copy-paste prompts to start an agent.
- `docs/ai/MASTER_TASK.md` — main task contract and DoD.
- `docs/ai/CONTEXT_MAP.md` — this navigation map.
- `docs/ai/PROGRESS.md` — progress log.
- `docs/ai/ACCEPTANCE_CHECKLIST.md` — acceptance checklist.
- `docs/ai/BLOCKERS.md` — blocker log.
- `docs/ai/workflows/` — staged implementation plans (read all, execute in order).
  - `docs/ai/workflows/README.md` — stage order and execution rules.
  - `docs/ai/workflows/01_stabilization_fixes_test10.md` — stabilization fixes from test.10 audit.
  - `docs/ai/workflows/02_test_engine_performance.md` — test engine performance workflow.
  - `docs/ai/workflows/03_tray_and_menu_ux.md` — tray and menu UX workflow.
- `docs/ai/prompts/` — legacy prompt folder (optional / may be deprecated).
- `scripts/agent-verify.ps1` — Windows verification.
- `scripts/agent-verify.sh` — Unix verification.

## Known conventions

- Unit tests: `tests/test_*_unittest.py`.
- Features organized under `app/zapret_manager/features/`.
- Core modules under `app/zapret_manager/core/`.
- UI modules under `app/zapret_manager/ui/`.

## Do not scan unless needed

- Prefer this map before full-repo scans.
- Use targeted search (`rg`, `grep`, IDE search) after identifying likely paths.
- If this map is stale, update it.
- Do not paste large file contents into chat.

## Last updated

- Date: 2026-05-03
- Updated by: AI coding agent
- Reason: Add staged workflows folder references and recommended read order.
