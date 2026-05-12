# Blockers

## Current Blockers

**Test Failures in Stage 04 (2026-05-12)**

**test_main_menu_unittest.py failures:**
- `test_menu_routing_maps_to_correct_handlers` - TypeError: Object of type MagicMock is not JSON serializable
  - **Cause:** test calls `run_main_menu()` which triggers `detect_runtime_files()` -> `save_state()` with MagicMock
  - **Impact:** Test infrastructure issue, not production functionality
  - **Status:** RESOLVED - Fixed by using StringIO and sys.stdout patching
  - **Resolution:** Used unittest's built-in fixtures for proper output capture

**Previous Critical Fixes Resolved:**

**SingBox Node Persistence Regression (2026-05-12)**
- **Issue:** save_nodes() was using shareable_report mode, permanently masking raw links in local storage
- **Impact:** Users would lose connection data after restart, breaking reconnect capability
- **Resolution:** Removed shareable_report mode from save_nodes(), added serialize_nodes_for_report() for shareable exports
- **Status:** RESOLVED - All tests passing, agent-verify successful

## Recent Critical Fixes Resolved

**SingBox Node Persistence Regression (2026-05-12)**
- **Issue:** save_nodes() was using shareable_report mode, permanently masking raw links in local storage
- **Impact:** Users would lose connection data after restart, breaking reconnect capability
- **Resolution:** Removed shareable_report mode from save_nodes(), added serialize_nodes_for_report() for shareable exports
- **Status:** RESOLVED - All tests passing, agent-verify successful

Potential decisions needed:

1. **Builtin v3/v8 fake assets**
   Whether to bundle missing fake assets for builtin v3/v8 or disable these strategies.
   - `t2.bin` — source unknown. May need to be removed from the strategy or marked unavailable.
   - `4pda.bin` — possible alias for `tls_clienthello_4pda_to.bin`. Need to decide whether to alias or correct strategy reference.

2. **StressOzz upstream cache in releases**
   Whether StressOzz upstream cache should be bundled in release or downloaded on demand.

3. **Final desired main menu structure**
   Needs human review before menu simplification implementation.

4. **Default problem_domains.json in releases**
   Whether release should include default `problem_domains.json` template or generate it on first run.

5. **Windows-only verification**
   Some features (WinDivert, winws2, system proxy) cannot be tested on non-Windows CI.
   Requires documented manual Windows smoke test procedure.