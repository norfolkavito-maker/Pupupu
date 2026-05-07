# Workflow 01 — Strategy Compatibility and Optimization

## Goal

Build a strategy compatibility model before implementing or changing runtime execution.

## Strategy source roles

- Flowseal strategies: preferred Windows `winws2` strategies.
- StressOzz strategies: imported workflow/strategy references requiring normalization.
- bol-van docs: technical semantics and validation reference.
- User custom strategies: never trust blindly; always validate.

## Required statuses

- `FLOWSEAL_WINWS2_READY`
- `STRESSOZZ_IMPORTED_NEEDS_NORMALIZATION`
- `CUSTOM_NEEDS_VALIDATION`
- `GENERATED_WINWS2_READY`
- `LEGACY_WINWS_NEEDS_CONVERSION`
- `INVALID_MISSING_ASSETS`
- `INVALID_UNSUPPORTED_ENGINE`
- `DUPLICATE_EQUIVALENT`
- `EXPERIMENTAL_NEEDS_CONFIRMATION`
- `UNKNOWN_NEEDS_VERIFICATION`

## Compatibility checks for every strategy

Record:

- source;
- original file;
- original engine;
- normalized engine;
- required executable;
- required WinDivert files;
- required fake files;
- required hostlist files;
- required ipset/list files;
- placeholders resolved;
- unsupported Linux paths removed;
- dangerous arguments rejected;
- duplicate command blocks detected;
- TCP/UDP filters validated;
- QUIC/fake packet dependencies validated;
- RKN/exclude/wssize compatibility checked;
- Discord/YouTube/Games layer conflicts checked.

## Optimization rules

- Deduplicate strategies with equivalent final argv.
- Keep provenance even for duplicates.
- Prefer strategies that pass baseline comparison.
- Do not auto-apply experimental strategies.
- Rank strategies by:
  - domain success rate;
  - DNS/TCP/UDP/HTTP/HTTPS result;
  - crash rate;
  - missing assets;
  - latency;
  - service-specific success: Discord, YouTube, Games.
- Store results in telemetry.
- Pin top 5 only after successful tests.

## Output

Update `docs/ai/STRATEGY_COMPATIBILITY_MATRIX.md` with the strategy inventory and compatibility status.
