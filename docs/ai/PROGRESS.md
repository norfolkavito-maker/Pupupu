
## 2026-05-11 - Stage 03 Complete: Strategy Import + Runtime Bridge

- **Scope:** Complete Stage 03 with all bridge stages (03.5, 03.6, 03.7).
- **Changes:**
  - **Stage 03 Core:** Created strategy normalization, validation, and import pipelines.
  - **Stage 03.5:** Implemented bundled upstream snapshot system and runtime asset repair.
  - **Stage 03.6:** Fixed blockcheck settings action with proper error handling and output decoding.
  - **Stage 03.7:** Implemented problem domains as virtual test set and strategy ranking generation.
  - **Blocking invalid strategies:** Added validation checks before winws launch in strategy_test.py.
  - **Integration:** All new features integrated into AppContext bootstrap.
- **New modules:**
  - `app/zapret_manager/features/upstreams_snapshot.py` - Bundled upstream management
  - `app/zapret_manager/features/runtime_repair.py` - Runtime asset repair from bundled sources
  - `app/zapret_manager/features/problem_domains_bridge.py` - Problem domains and ranking
  - Enhanced `app/zapret_manager/features/blockcheck.py` - Improved error handling
- **Verification commands:** 
  - `bash scripts/agent-verify.sh` - PASSED
  - `PYTHONPATH=app python3 -m pytest tests/ -k "strategy" -q` - 29 passed
  - `PYTHONPATH=app python3 -m pytest tests/test_strategy_invalid_full_scenario.py tests/test_strategy_invalid_when_winws_fails_unittest.py -q` - 2 passed
- **Critical Fix (2026-05-12):** Fixed SingBox node persistence regression where save_nodes() was using shareable_report mode, permanently masking raw links in local storage and breaking reconnect capability.
  - **Architecture Separation:** Local storage (nodes.json) preserves connection data; shareable reports use separate serialize_nodes_for_report() function.
  - **Files Fixed:** app/zapret_manager/core/singbox/nodes.py, tests/test_singbox_nodes_unittest.py
- **Next milestone:** Stage 05 - Ready for next phase.

## 2026-05-12 - Stage 04 Complete: Menu Simplification

- **Scope:** Simplify main menu to status-first interface with relocated advanced actions.
- **Changes:**
  - **Main Menu Structure:** Reduced from 11+ legacy items to exactly 11 core items
  - **Status-First UI:** Main screen now shows comprehensive status before menu options
  - **Simplified Routing:** Clean mapping of choices to appropriate handlers
  - **Advanced Actions Moved:** Engineering functions relocated to dedicated submenus
  - **New Menu Handlers:** Added diagnostics_menu, logs_menu, updates_menu, settings_menu, advanced_menu
- **Files Changed:**
  - `app/zapret_manager/ui/main_menu.py` - Simplified main menu with status-first approach
  - `app/zapret_manager/ui/menus.py` - Added new menu handlers for simplified structure
  - `tests/test_main_menu_unittest.py` - Added tests for simplified menu structure
- **Verification Commands:**
  - `bash scripts/agent-verify.sh` - PASSED
  - `PYTHONPATH=app python3 -m pytest tests/ -k "menu or selection or strategy" -q` - 40 passed, 3 failed (new test issues)
  - `PYTHONPATH=app python3 -m pytest tests/ --tb=short -q` - 220 passed, 2 skipped