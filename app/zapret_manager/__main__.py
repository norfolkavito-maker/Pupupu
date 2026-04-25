from __future__ import annotations

import traceback
from pathlib import Path

from zapret_manager.main import main


def _write_crash_log(text: str) -> Path | None:
    try:
        from zapret_manager.core.paths import Paths

        root = Paths.detect_root()
        paths = Paths.from_root(root)
        # ensure dirs enough for logs
        paths.ensure_dirs()
        crash = paths.logs_dir / "crash.log"
        crash.write_text(text, encoding="utf-8", errors="replace")
        return crash
    except Exception:
        return None


if __name__ == "__main__":
    try:
        # Setup logging as early as possible to capture admin-check decisions.
        try:
            from zapret_manager.core.log import setup_logging
            from zapret_manager.core.paths import Paths

            _root = Paths.detect_root()
            _paths = Paths.from_root(_root)
            _paths.ensure_dirs()
            setup_logging(_paths.logs_dir / "zapret_manager.log")
        except Exception:
            # Logging will be configured later in AppContext.bootstrap.
            pass

        # Must be before any privileged actions and before UI starts.
        from zapret_manager.utils.platform import ensure_admin_or_relaunch

        ensure_admin_or_relaunch()
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        tb = traceback.format_exc()
        crash_path = _write_crash_log(tb)
        print("\nDEDZAPRET crashed on startup.\n")
        if crash_path:
            print(f"Crash log written to: {crash_path}")
        print(tb)
        try:
            input("\nPress Enter to exit...")
        except Exception:
            pass
        raise

