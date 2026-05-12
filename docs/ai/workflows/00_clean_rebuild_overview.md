# Workflow 00 — Clean rebuild overview

## Purpose
This is the strategic overview for the entire clean rebuild/stabilization effort.

This is not a feature sprint.
This is a stabilization, cleanup, path normalization, release packaging, strategy validation, diagnostics, and UX simplification sprint.

## Principles
- Preserve functionality. Do not remove features.
- Normalize paths. Separate upstream cache from working data.
- Clean up releases. No test-state in releases.
- Simplify menu. Move low-level functions to submenus.
- Replace crashes with diagnostics. No raw tracebacks in normal UI.
- All work is staged. Stages must be executed in order.

## Key separation model
- **bol-van/zapret** — technical source of winws/desync behavior.
- **Flowseal** — source of Windows runtime examples. Source material only.
- **StressOzz** — source of UX/menu/workflow ideas. Source material only.
- **DedZapret** — product layer: normalizer, validator, launcher, diagnostics.

## Stages overview
| #  | Name | Focus |
|----|------|-------|
| 00 | Clean rebuild overview | This file |
| 01 | Release packaging cleanup | Clean release archives, exclude stale state |
| 02 | Path resolver + runtime assets | Canonical paths, upstream cache vs working data |
| 03 | Strategy import + validation | Flowseal/StressOzz import, normalize, validate |
| 04 | Menu simplification | Short main menu, status-first UI |
| 05 | sing-box pipeline | Node import, config build, validate, start/stop |
| 06 | Diagnostics + bug report | Masked secrets, structured runtime summary |
| 07 | Release verification | Unit tests, package tests, smoke tests |

## Target portable layout
```
DedZapret.exe
DedZapretData/
  config.yaml
  sources.yaml
  runtime/
    zapret/          # winws.exe, winws2.exe, WinDivert, fake files, lists
    sing-box/        # sing-box.exe
  data/
    strategies/      # builtin/, generated/, custom/
    lists/           # user list files
    nodes/           # subscriptions, nodes.json
    profiles/        # user profiles
    state/           # state.json, current.json
    logs/            # audit logs
    backups/
    reports/
```

## Rules
- Do not implement app logic in planning stages.
- Do not invent new features.
- Do not delete existing features — relocate or mark Future/Planned.
- Stages must be executed in order 01→07.
- After each stage, run tests and update PROGRESS.md + ACCEPTANCE_CHECKLIST.md.