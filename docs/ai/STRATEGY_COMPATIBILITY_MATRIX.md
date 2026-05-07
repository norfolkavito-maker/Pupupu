# Strategy Compatibility Matrix

This file records strategy compatibility findings. Fill it during strategy import, runtime rebuild and test engine work.

## Status legend

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

## Matrix template

| ID | Source | Kind | Engine | Status |
|---|---|---|---|---|
| _fill_ | _flowseal/stressozz/custom/generated_ | _base/youtube/discord/games_ | _winws2/winws/bat/unknown_ | _status_ |

## Required detail per strategy

For each strategy, record:

- original path;
- normalized id;
- source ref/tag/commit if known;
- final argv hash;
- required fake files;
- required list files;
- missing assets;
- conflicts;
- last test result;
- notes.
