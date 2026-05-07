# Runtime Source Policy

## Source roles

### bol-van/zapret

Canonical technical source for zapret semantics:

- desync methods;
- hostlist/ipset/autohostlist;
- fake packet behavior;
- blockcheck/test philosophy;
- low-level option meaning.

Do not port Linux/OpenWrt init scripts, iptables, nftables, systemd or `/opt/zapret` assumptions directly into DedZapret.

### Flowseal/zapret-discord-youtube

Canonical Windows runtime source:

- `winws2`;
- WinDivert layout;
- `bin/lists/fake/utils`;
- Windows `.bat` strategy examples;
- service lifecycle reference;
- Windows-oriented runtime assets.

DedZapret should build new runtime logic around Flowseal `winws2`.

### StressOzz/Zapret-Manager

Workflow and strategy reference:

- menu logic;
- Dv/Yv/Gv organization;
- Flowseal strategy selection;
- RKN/exclude/wssize logic;
- test flow ideas.

Do not execute or port Linux shell logic directly. Extract intent and normalize to DedZapret models.

## DedZapret role

DedZapret is the product layer:

- imports;
- normalizes;
- validates;
- tests;
- ranks;
- runs;
- logs;
- diagnoses;
- repairs;
- packages bug reports.

## Required strategy statuses

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

## Prohibited behavior

- Do not merge upstream scripts blindly.
- Do not silently fallback from `winws2` to `winws`.
- Do not execute downloaded runtime files before validation.
- Do not overwrite custom strategies or user lists during upstream sync.
- Do not remove provenance after deduplication.
