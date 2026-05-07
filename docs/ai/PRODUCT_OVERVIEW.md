# PRODUCT OVERVIEW

This document provides a high‑level overview of the DedZapret Manager product.  It describes what the program is and is not, maps upstream sources to internal layers, outlines the user workflow and main capabilities, explains the runtime and data model, summarises the safety model and lists the guiding agent rules.  It serves as an executive summary for stakeholders and a starting point for new contributors.

## One‑line description

**DedZapret Manager** is a portable Windows 10/11 manager for DPI desynchronisation (`zapret/winws2`), strategies, testing, proxy/VPN connectivity, autostart/tray, profiles and diagnostics.

## What this program is

* A **Windows operations manager** that wraps the low‑level `zapret/winws2` runtime and provides a safe interface for choosing and composing strategies.
* A **strategy orchestrator** that imports, validates, classifies and combines base strategies with service‑specific layers (Discord, YouTube, Games) and optional modes (RKN/exclude, wssize).
* A **test engine** that measures the effectiveness of strategies via DNS, TCP/UDP and HTTP/HTTPS probes and ranks them for the user.
* An **optional proxy/VPN client** that manages sing‑box nodes and subscriptions, providing SOCKS/HTTP/Mixed proxy and system proxy integration.
* A **profile manager** allowing users to save sets of settings for different scenarios and automatically start/stop runtime based on watched processes.
* A **system integrator** that modifies DNS, hosts, QUIC blocking, TCP timestamps and autostart safely with backup and rollback.
* A **diagnostics and reporting tool** that checks system and runtime health and creates masked bug report archives.

## What this program is not

* Not just a bat launcher; users should never edit `.bat` files manually.
* Not a simple clone of Flowseal or StressOzz; it unifies and normalises their behaviour.
* Not a general VPN client; the proxy layer is optional and separate from DPI desynchronisation.
* Not a random collection of scripts; it must follow a layered architecture with clear responsibilities.
* Not a replacement for bol‑van/zapret’s Linux tooling; it targets Windows only.

## Upstream source model

The program uses three upstreams:

* **bol‑van/zapret** – canonical semantics of DPI desynchronisation; reference for desync methods, hostlist/ipset, blockcheck.  Not a source of Windows code.
* **Flowseal/zapret‑discord‑youtube** – provides the Windows runtime (`winws2.exe`), runtime assets (bin/lists/fake), example strategies and service management scripts.  This is the base for runtime operations.
* **StressOzz/Zapret‑Manager** – supplies workflow ideas, additional strategies (Dv/Yv/Gv), update logic and menu organisation.  Used as a reference for features and imported as data.

Mapping these sources to layers ensures that semantics (bol‑van), runtime (Flowseal) and workflow (StressOzz) are kept separate and can be updated independently.

## User workflow

1. **Installation:** User extracts DedZapret and runs the executable.  Preflight checks verify system readiness and prompt for missing runtime or strategies.
2. **Choosing a strategy:** User selects a base strategy and adds layers (Discord/YouTube/Games/RKN/wssize).  The program composes and applies the strategy.
3. **Testing:** User runs quick or full tests.  The test engine compares baseline and strategy performance and provides a ranking.
4. **Proxy/VPN (optional):** User imports nodes or subscriptions for sing‑box, previews them, updates and starts proxy.  System proxy can be toggled.
5. **Profiles:** User saves combinations of settings as profiles, assigns watchers for processes, enables autostart and tray.
6. **Updating:** User updates Flowseal runtime and imports new strategies from StressOzz.  Repair operations fix missing assets.
7. **Diagnostics and reporting:** User runs diagnostics to see system health; bug reports package logs and configs with secrets masked.

## Main capabilities

* **Strategy selection and composition** – choose from built‑in, imported, generated and custom strategies and combine them with service‑specific layers.
* **Testing and ranking** – run baseline and per‑strategy tests, save results and recommend the best strategies.
* **Proxy/VPN management** – import nodes/subscriptions, configure ports, start/stop proxy and system proxy.
* **Network operations** – toggle DoH, edit hosts file, block QUIC, toggle TCP timestamps.
* **Profiles and autostart/tray** – manage named scenarios, auto‑start when Windows boots, control via system tray.
* **Diagnostics and bug reports** – perform health checks, collect logs, mask secrets and package reports.
* **Updates and repair** – sync with upstream sources, replace runtime safely, repair missing assets and backup important data.

## Runtime and data model

* All runtime assets live under `DedZapretData/runtime/zapret` for winws2 and under `DedZapretData/runtime/singbox` for proxy binaries.
* Configuration resides in `config.yaml`; persistent state in `state.json`; runtime state in `current.json`.
* Logs are stored in `logs/`, telemetry in `data/telemetry`, reports in `reports/` and imported upstream data in `data/upstreams`.
* Strategies are stored in `strategies/builtin`, `strategies/generated`, `strategies/custom` and imported locations; registry holds metadata and classification.
* Tests produce JSONL files and ranking JSONs; profiles are stored alongside config.

## Safety model

* **Preflight checks** ensure that runtime binaries and drivers exist and that user has necessary privileges.
* **Atomic writes and backups** are used for config/state/log modifications and updates.
* **Validation** of strategies prevents unsupported or dangerous arguments from being executed.
* **Rollback** is available for hosts/DNS modifications, runtime updates and autostart tasks.
* **Masking** of sensitive data ensures that bug reports do not expose secrets.
* **Agent rules** (see `AGENT_RULES_RUNTIME_REBUILD.md`) protect against unsafe refactoring and enforce upstream separation.

## Agent rules summary

* Do not mix upstream sources; treat bol‑van, Flowseal and StressOzz as separate roles.
* Prefer winws2 and avoid silent fallback to winws.
* Preserve behaviour; mark unused code for later verification rather than deleting.
* Verify downloads and checksums; do not execute staged binaries immediately.
* Log and audit all operations; mask secrets.
* Ask the user before making high‑impact changes (e.g. removing legacy support).

## Future architecture direction

Refer to `PROGRAM_BLUEPRINT.md` and `REBUILD_PLAN.md` for a detailed blueprint and migration sequence.  In summary, the program will be rebuilt into layers: core utilities, upstream sync, runtime management, strategy registry, test engine, proxy layer, Windows operations, profiles, and user interfaces (console, tray and future GUI).  Each layer will have clear interfaces and unit tests.  Characterization tests will ensure that the new implementation preserves all existing behaviour while enabling safer and more powerful features.
