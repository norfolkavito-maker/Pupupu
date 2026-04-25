from __future__ import annotations

import traceback
from pathlib import Path
import os
import sys

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

        # Collect extra context for crash log.
        try:
            from zapret_manager import __version__
            from zapret_manager.core.paths import Paths
            from zapret_manager.utils.platform import is_admin
            from zapret_manager.features.zapret_runtime import runtime_health

            root = Paths.detect_root()
            paths = Paths.from_root(root)
            paths.ensure_dirs()
            admin_flag = is_admin()

            # runtime_health needs context; create minimal ctx-like wrapper
            # via AppContext.bootstrap is too risky (might crash). We'll build a
            # small object with .paths and .state enough for runtime_health.
            from types import SimpleNamespace
            from zapret_manager.core.state import load_state

            state = load_state(paths.state_file)
            ctx = SimpleNamespace(root=root, paths=paths, state=state)
            rh = runtime_health(ctx)  # type: ignore[arg-type]
        except Exception:
            __version__ = "unknown"  # type: ignore[assignment]
            root = None
            paths = None
            admin_flag = None
            rh = None

        header_lines = [
            "DEDZAPRET crash report",
            "====================",
            f"version: {locals().get('__version__', 'unknown')}",
            f"cwd: {os.getcwd()}",
            f"argv0: {sys.argv[0] if sys.argv else ''}",
        ]
        if root is not None:
            header_lines.append(f"detected root: {root}")
        if paths is not None:
            header_lines.append(f"DedZapretData: {paths.data_root}")
            header_lines.append(f"config path: {paths.config_file} (exists={paths.config_file.exists()})")
            header_lines.append(f"runtime path: {paths.runtime_dir} (exists={paths.runtime_dir.exists()})")
        if admin_flag is not None:
            header_lines.append(f"admin rights: {'yes' if admin_flag else 'no'}")
        if isinstance(rh, dict):
            header_lines.append(f"runtime ok: {bool(rh.get('ok'))}")
            header_lines.append(f"runtime_dir: {rh.get('runtime_dir')}")
            header_lines.append(f"zapret_dir: {rh.get('zapret_dir')}")
            header_lines.append(f"winws: {rh.get('winws')}")
            header_lines.append(f"problems: {rh.get('problems')}")

        tb = "\n".join(header_lines) + "\n\n" + tb
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

