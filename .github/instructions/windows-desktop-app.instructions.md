---
applyTo: "**"
---

# Windows Desktop App Instructions

- Assume the app must remain portable where possible.
- Avoid admin-only behavior unless explicitly required.
- Store logs/state/backups under the app data root (not hardcoded user paths).
- Russian user-facing text should be clear and consistent.
- Distinguish implemented behavior from **Future / Planned**.
- Dangerous actions (proxy/DNS/routes/firewall/hosts changes) require:
  - explicit confirmation;
  - backup;
  - rollback/recovery steps.
