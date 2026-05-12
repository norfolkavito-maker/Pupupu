# Workflow 03 — Strategy import and validation

## Scope
Build a proper strategy import pipeline: sync upstream → parse → normalize paths → resolve placeholders → validate assets → generate DedZapret strategy → update index → mark valid/invalid.

## Tasks

### 3.1 Flowseal import pipeline
- Parse Flowseal strategies (`.bat`, YAML).
- Normalize paths:
  - `{FLOWSEAL_BIN}` → upstream cache bin directory
  - `{FLOWSEAL_LISTS}` → upstream cache lists directory
- Convert to DedZapret strategy model.
- Validate every referenced `{FAKE:...}`, `{LISTS:...}`, ipset file.

### 3.2 StressOzz import pipeline
- Parse StressOzz strategies.
- Normalize to DedZapret model.
- Mark imported strategies that need further validation.

### 3.3 Strategy validation
- Check that every referenced fake/list/ipset file exists.
- If assets are missing, strategy is INVALID.
- Invalid strategies must not be:
  - hidden from normal run menu, OR
  - visible but clearly marked INVALID and not runnable.

### 3.4 Builtin strategy fixes
- Fix or disable builtin strategies v3/v8 that reference missing assets:
  - `t2.bin` — source unknown, may need removal from strategy.
  - `4pda.bin` — possible alias for `tls_clienthello_4pda_to.bin`.

### 3.5 Strategy index
- Maintain a strategy index that records:
  - strategy ID
  - source (builtin/flowseal/stressozz/custom)
  - status (VALID/INVALID)
  - required files
  - missing assets
  - conflicts

## Acceptance criteria
- [ ] Flowseal strategies are imported and normalized.
- [ ] StressOzz strategies are imported and normalized or marked pending.
- [ ] All visible runnable strategies pass preflight validation.
- [ ] Invalid strategies are clearly marked and not runnable.
- [ ] Builtin v3/v8 are fixed or hidden as invalid.
- [ ] Strategy index is up to date.