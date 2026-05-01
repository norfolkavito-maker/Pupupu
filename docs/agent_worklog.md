# Agent Worklog

Rules:
- append only;
- do not delete previous entries;
- one entry per phase/change;
- include exact commands and results.

Template:

## YYYY-MM-DD HH:MM — <task title>

### Scope
...

### Files changed
- ...

### Commands run
```text
...
```

### Results
...

### Not verified
...

### Next step
...

## 2026-05-01 00:16 — Phase 0: Agent rules and worklog bootstrap

### Scope
Initialize mandatory agent governance files before feature implementation.

### Files changed
- AGENTS.md
- docs/agent_worklog.md

### Commands run
```text
date '+%Y-%m-%d %H:%M %Z'
```

### Results
- Added root `AGENTS.md` with permanent rules for planning/execution, safety, secrets, console output, zapret/winws, sing-box, updater.
- Created `docs/agent_worklog.md` with append-only rules and entry template.

### Not verified
- No functional runtime behavior verified in this phase (documentation-only changes).

### Next step
Implement Phase 1: package `sing-box.exe` into portable release and add CI validation check.

## 2026-05-01 00:26 — Phase 1: sing-box packaging + CI smoke/runtime hooks

### Scope
Add portable packaging for `sing-box.exe`, add artifact validation, and extend CI smoke output for sing-box binary/version visibility.

### Files changed
- .github/workflows/build.yml
- app/zapret_manager/__main__.py
- tests/test_singbox_binary_unittest.py
- app/zapret_manager/core/app_context.py

### Commands run
```text
python3 -m unittest tests/test_singbox_nodes_unittest.py tests/test_singbox_config_builder_unittest.py -v
python3 -m unittest tests/test_singbox_binary_unittest.py -v && python3 -m app.zapret_manager --ci-smoke
python3 -m unittest tests/test_singbox_binary_unittest.py tests/test_singbox_nodes_unittest.py tests/test_singbox_config_builder_unittest.py -v && python3 -m app.zapret_manager --ci-smoke
date '+%Y-%m-%d %H:%M %Z'
```

### Results
- Workflow now downloads latest official sing-box Windows amd64 zip and extracts `sing-box.exe`.
- Portable bundle now includes `bundle/DedZapret/bin/sing-box/sing-box.exe`.
- Workflow validation now fails if `sing-box.exe` is missing from bundle.
- `--ci-smoke` now reports `sing-box binary: OK|MISSING` and prints version first line when present.
- Added binary detection unit tests (`tests/test_singbox_binary_unittest.py`).
- Fixed pre-existing syntax issue in `app_context.py` that broke `--ci-smoke` import path.

### Not verified
- GitHub Actions run for updated workflow not executed locally (requires remote CI).
- Windows runtime invocation of `sing-box version` not verified on real Windows host in this phase.

### Next step
Implement Phase 2: subscriptions storage/import/update pipeline with dedup and safe masking boundaries.

## 2026-05-01 00:30 — Phase 2: subscriptions import/update foundation

### Scope
Implement subscription data model + parsing + menu wiring for add/update subscription URLs while keeping sing-box isolated from zapret strategies.

### Files changed
- app/zapret_manager/core/singbox/subscriptions.py
- app/zapret_manager/features/singbox_menu.py
- tests/test_singbox_subscriptions_unittest.py

### Commands run
```text
python3 -m unittest tests/test_singbox_binary_unittest.py tests/test_singbox_nodes_unittest.py tests/test_singbox_config_builder_unittest.py tests/test_singbox_subscriptions_unittest.py -v
date '+%Y-%m-%d %H:%M %Z'
```

### Results
- Added `SubscriptionRecord` storage/load/save + add logic in new `core/singbox/subscriptions.py`.
- Added subscription payload parser supporting:
  - plain text links (line-by-line),
  - base64 payload with links,
  - comments/empty lines skip.
- Added merge function with dedup by `node_id` and counters (`imported/skipped/errors`).
- Extended sing-box menu with:
  - `Add subscription URL`,
  - `Update subscriptions`.
- Added tests for plain-text and base64 subscription parsing.
- Targeted unit tests pass (8/8).

### Not verified
- Real network download/update against live subscription URL not verified on this host.
- Full end-to-end interactive menu flow not manually verified in Windows terminal yet.

### Next step
Implement Phase 3: Windows system proxy mode with backup/restore and explicit user confirmation.

## 2026-05-01 00:37 — Phase 3-5: system proxy + health + expanded sing-box menu

### Scope
Implement guarded Windows system proxy controls, add sing-box health summary, and extend sing-box UI section with explicit proxy actions and rollback on stop.

### Files changed
- app/zapret_manager/core/singbox/system_proxy_win.py
- app/zapret_manager/core/singbox/health.py
- app/zapret_manager/features/singbox_menu.py
- tests/test_singbox_system_proxy_unittest.py
- tests/test_singbox_health_unittest.py

### Commands run
```text
python3 -m unittest tests/test_singbox_system_proxy_unittest.py tests/test_singbox_subscriptions_unittest.py tests/test_singbox_binary_unittest.py -v && python3 -m app.zapret_manager --ci-smoke
python3 -m unittest tests/test_singbox_health_unittest.py tests/test_singbox_system_proxy_unittest.py tests/test_singbox_subscriptions_unittest.py tests/test_singbox_binary_unittest.py tests/test_singbox_nodes_unittest.py tests/test_singbox_config_builder_unittest.py -v && python3 -m app.zapret_manager --ci-smoke && python3 -m pytest -q
date '+%Y-%m-%d %H:%M %Z' && git status --porcelain
```

### Results
- Added Windows system proxy helper module with backup/restore and explicit local proxy enable helper.
- Added sing-box health checker (running/pid/ports 2080/2081/ok).
- Extended sing-box menu with:
  - enable system proxy (explicit confirmation),
  - restore system proxy,
  - health data in status output.
- Added rollback behavior on `singbox.stop`: attempts to restore system proxy backup.
- Added/updated unit tests for system proxy and health.
- Validation passed:
  - targeted unittest suites,
  - ci-smoke,
  - full pytest (`111 passed`).

### Not verified
- Real Windows registry writes/restore and browser behavior not verified on live Windows host in this environment.
- TUN/VPN mode still not implemented in this iteration.

### Next step
Create focused commit for sing-box phases implemented in this iteration, push branch, and create next test tag for CI release verification.

### 2026-05-01 11:26 (Europe/Moscow)
- task: P0 fix(strategies/runtime): diagnose bundled v3/v8 fake assets
- scope: Add bundled v3/v8 fake assets into runtime asset repair/manifest and tests
- files changed:
  - app/zapret_manager/features/runtime_assets.py
  - tests/test_runtime_assets_fake_repair_unittest.py
- commands run:
  - python3 -m unittest tests/test_runtime_assets_fake_repair_unittest.py -v
- results:
  - tests passed
- not verified:
  - Real Windows bundle assets presence and repair behavior on actual release ZIP
- next step:
  - commit as: "fix(strategies/runtime): diagnose bundled v3/v8 fake assets"
  - run related runtime_assets test suites

### 2026-05-01 12:00 (Europe/Moscow)
- task: P1 fix(singbox): improve subscription import and auto-select active node
- scope: subscription parsing (plain/base64 + clash yaml + sing-box json), safer UI import, counters, auto-select first imported node
- files changed:
  - app/zapret_manager/core/singbox/subscriptions.py
  - app/zapret_manager/features/singbox_menu.py
  - tests/test_singbox_subscriptions_unittest.py
  - tests/test_singbox_menu_import_single_link_unittest.py
  - tests/test_singbox_autoselect_active_node_unittest.py
- commands run:
  - python3 -m unittest tests/test_singbox_subscriptions_unittest.py -v
  - python3 -m unittest tests/test_singbox_menu_import_single_link_unittest.py -v
  - python3 -m unittest tests/test_singbox_autoselect_active_node_unittest.py -v
  - python3 -m unittest tests/test_singbox_binary_unittest.py tests/test_singbox_nodes_unittest.py tests/test_singbox_config_builder_unittest.py tests/test_singbox_subscriptions_unittest.py tests/test_singbox_menu_import_single_link_unittest.py tests/test_singbox_autoselect_active_node_unittest.py -v
- results:
  - tests passed
- not verified:
  - Real-world parsing of full Clash YAML variants and sing-box JSON variants beyond minimal cases
  - Real network download from subscription URL on Windows host
- next step:
  - commit as: "fix(singbox): improve subscription import and auto-select active node"
  - optional: extend sing-box json parser to handle v2ray/vmess outbounds
