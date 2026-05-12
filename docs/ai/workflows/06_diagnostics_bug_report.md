# Workflow 06 — Diagnostics and bug report

## Scope
Improve diagnostics and bug report generation. Mask secrets. Include structured runtime summaries, missing assets, and active strategy/node/config status.

## Tasks

### 6.1 Bug report content
Bug report must include:
- Masked logs (last N audit events).
- Current config/state summary.
- Active strategy name and status.
- Active node status without secrets (no UUID, no password, no subscription token).
- Runtime file tree summary (list of files in runtime/zapret/ and runtime/sing-box/).
- Missing assets list (fake files, list files, ipset files that strategies reference but are absent).
- Process status (winws, sing-box PID/not running).
- Port status (which ports are listening).
- Last errors from audit log.
- Upstream sync status (Flowseal, StressOzz last sync).
- Package/version info.
- Environment summary (OS, Python version, admin status).

### 6.2 Secret masking
- Apply `mask.py` to all logs, diagnostics, and bug report artifacts.
- Never include:
  - Node UUIDs
  - Node passwords
  - Subscription tokens
  - Raw private subscription URLs
  - Authorization headers
  - API keys

### 6.3 Bug report artifacts
Include in bug report ZIP:
- `strategy_runs.jsonl` (masked)
- `latest_strategy_ranking.json` (masked)
- `problem_domains.json` (raw, it's just domain names)
- `singbox_nodes_summary.json` (masked, no secrets)
- Audit log excerpt

Exclude from bug report:
- Raw `nodes.json` with secrets.
- Raw subscription URLs.
- Developer machine personal paths.

### 6.4 Diagnostics menu
- Quick diagnostics (30-second overview).
- Full diagnostics (collect all data).
- Trigger bug report creation from diagnostics.

## Acceptance criteria
- [ ] Bug report masks secrets.
- [ ] Bug report includes runtime summary.
- [ ] Bug report includes missing assets.
- [ ] Bug report does not leak node UUIDs/passwords/subscription tokens.
- [ ] Bug report does not include raw personal local paths unless explicitly allowed.