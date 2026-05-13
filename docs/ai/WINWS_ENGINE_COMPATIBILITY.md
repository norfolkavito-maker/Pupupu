# winws/winws2 Engine Compatibility Audit

## Overview

This audit documents the current state of winws and winws2 engine support in the DedZapret Manager codebase, based on repository code and tests.

## Engine Sources

### winws.exe
- **Source**: `bol-van/zapret` (canonical technical source for zapret semantics)
- **Purpose**: Original zapret runtime
- **Status**: Legacy, currently default in config.yaml
- **Location**: Configured in `config.yaml` as `winws_path: ".\\runtime\\zapret\\winws.exe"`

### winws2.exe
- **Source**: `Flowseal/zapret-discord-youtube` (Windows runtime source)
- **Purpose**: Modern Windows runtime with WinDivert layout
- **Status**: Primary runtime for Windows
- **Location**: Expected in `DedZapretData/runtime/zapret/bin/`, `DedZapretData/data/upstreams/flowseal/bin/`, or bundled runtime

## Engine Mode Support

The codebase supports three engine modes:

1. **auto** (default): Automatically selects engine based on strategy requirements
2. **winws**: Forces use of winws.exe
3. **winws2**: Forces use of winws2.exe

### Implementation Locations

- `app/zapret_manager/core/commands.py`: `set_engine_mode(ctx, mode)`
- `app/zapret_manager/tray/tray_menu.py`: Tray menu engine selection (auto/winws/winws2)
- `app/zapret_manager/tray/tray_status.py`: Engine mode display in tray tooltip
- `app/zapret_manager/features/zapret_runtime.py`: Engine detection and command building

## Strategy Engine Requirements

Strategies can specify an `engine` field in their YAML configuration:

```yaml
engine: winws2  # or "winws" or "auto"
```

### Engine Resolution Logic

From `app/zapret_manager/features/zapret_runtime.py`:

1. If strategy specifies `engine: winws2`, use winws2.exe
2. If strategy specifies `engine: winws`, use winws.exe
3. If strategy specifies `engine: auto` or no engine, use system default (currently winws)

### Build Command Logic

From `build_command()` in `zapret_runtime.py`:

```python
engine = engine_override or strategy.engine

if engine == "winws2":
    exe = winws2 or _find_first(rt, ["winws2.exe"])
    if not exe:
        raise RuntimeError("winws2.exe not found in runtime")
else:
    # auto + winws default
    exe = winws or _find_first(rt, ["winws.exe"])
```

## Runtime Health Checks

From `runtime_health()` in `zapret_runtime.py`:

- Checks both `winws.exe` and `winws2.exe` existence
- Returns diagnostic information including:
  - `winws_exists`: boolean
  - `winws2_exists`: boolean
  - `requested_engine`: auto/winws/winws2
  - `selected_engine`: actual engine selected
  - `selected_binary`: path to selected binary
  - `strategy_requested_binary`: what the strategy requested

### Health Check Behavior

- Backward compatibility: "ok" status still reflects winws.exe readiness
- winws2 is checked only if explicitly requested
- Missing winws2 when strategy requires it is reported as actionable issue

## Bundled Binary Status

### Current Bundling
- **winws.exe**: Referenced in config.yaml as default
- **winws2.exe**: Expected in Flowseal runtime layout, but bundling status unclear from code

### Test Evidence
- `test_winws_validate_unittest.py`: Tests winws command validation (uses winws.exe in test commands)
- `test_strategy_invalid_when_winws_fails_unittest.py`: Tests behavior when winws fails
- No explicit tests for winws2-only scenarios found

## Strategy Compatibility

### Which Strategies Require winws2?

From code analysis:
- Strategies with `engine: winws2` field require winws2.exe
- YouTube/Discord strategies from Flowseal likely require winws2 (based on source attribution)
- Base strategies (v1-v9) likely work with winws (based on bol-van/zapret source)

### Which Strategies Can Run on winws?

- Base strategies (v1-v9) from bol-van/zapret: designed for winws
- Strategies without explicit engine field: default to winws
- Strategies with `engine: winws` or `engine: auto`: can run on winws

## Current Default Behavior

### Config.yaml Default
```yaml
winws_path: ".\\runtime\\zapret\\winws.exe"
```

### System Default
- When engine is "auto" or unspecified, code defaults to winws.exe
- This is backward compatible with existing strategies

### Tray Menu Default
- Engine mode: "auto" (checked by default)
- User can manually select winws or winws2

## What Breaks If Only winws2 is Kept?

### Breaking Changes
1. **Base strategies (v1-v9)**: Designed for winws, may not work with winws2 without testing
2. **Existing config.yaml**: Points to winws.exe, would need migration
3. **Backward compatibility**: Users with winws-only setups would break
4. **Test suite**: Many tests reference winws.exe, would need updates

### Migration Requirements
1. Test all base strategies (v1-v9) with winws2
2. Update config.yaml default to winws2.exe
3. Update all strategy YAMLs to specify `engine: winws2` if required
4. Update test suite to use winws2
5. Provide migration path for existing users

## Recommendations

### Based on Codebase Analysis

1. **Keep Both Engines** (Recommended for now):
   - winws.exe: Default for backward compatibility with base strategies
   - winws2.exe: Available for Flowseal/YouTube/Discord strategies
   - Engine mode "auto": Select based on strategy requirements

2. **Default to winws2** (Future, after testing):
   - Only after all strategies are tested with winws2
   - Only after test suite is updated
   - Only after migration path is documented
   - Keep winws.exe as fallback for legacy strategies

3. **Experimental Status**:
   - winws2 should be marked as "experimental/advanced" in UI until fully tested
   - Add clear warnings when selecting winws2 engine
   - Document which strategies require winws2

### What Needs Testing

1. Run all base strategies (v1-v9) with winws2
2. Run Flowseal strategies with winws2
3. Run YouTube/Discord strategies with winws2
4. Test engine mode switching (auto → winws → winws2 → auto)
5. Test fallback behavior when winws2 is missing
6. Test strategy loading with engine field

## Conclusion

**Current State**: Mixed support with winws as default, winws2 available but not default

**Recommendation**: 
- Keep both engines for now
- Use "auto" mode to select based on strategy requirements
- Mark winws2 as experimental/advanced in UI until comprehensive testing
- Plan migration to winws2 as default after all strategies are validated

**Blockers for winws2-only**:
- No evidence that base strategies (v1-v9) work with winws2
- Test suite uses winws.exe
- Config.yaml defaults to winws.exe
- No migration path documented

**Next Steps**:
1. Add comprehensive winws2 testing
2. Document strategy compatibility matrix
3. Create migration guide
4. Update UI to mark winws2 as experimental
