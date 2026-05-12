# Workflow 05 — sing-box pipeline stabilization

## Scope
Stabilize the sing-box node import, config generation, validation, and process lifecycle. Keep sing-box nodes strictly separate from zapret strategies.

## Tasks

### 5.1 Node import
- Import nodes from subscription URLs.
- Save to `nodes.json`.
- Validate node schema after import.

### 5.2 Active node requirement
- Require active node selection before allowing Start.
- If only one valid node exists after import, auto-select it (with explicit message).
- Block start if `active_node` is None or invalid.

### 5.3 Config generation
- Build sing-box config from active node.
- Validate config JSON before launching.
- If config validation fails, show clear error: "Конфигурация sing-box невалидна: ..."

### 5.4 Process lifecycle
- Start: launch sing-box with validated config.
- Status: check if process is running.
- Stop: tolerate stale PID. If process already stopped, report idempotent success.
- Restart: stop + start.

### 5.5 System proxy
- Backup current system proxy before enabling sing-box proxy.
- On stop/rollback, restore system proxy.
- Do not enable system proxy silently — require user action.

## Acceptance criteria
- [ ] Imported nodes are stored and validated.
- [ ] Start is blocked if no active node exists.
- [ ] Single imported node can be auto-selected if safe.
- [ ] Config generation is validated before launch.
- [ ] Stop/restart is idempotent for stale PID.
- [ ] System proxy is backed up before enabling and restored on stop.