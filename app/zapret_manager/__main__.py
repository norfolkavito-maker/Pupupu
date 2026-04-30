from __future__ import annotations

import os
from pathlib import Path
import sys
import traceback


def _parse_smoke_flag(argv: list[str]) -> bool:
    return "--ci-smoke" in argv


def _run_ci_smoke() -> int:
    """Non-interactive smoke check for CI.

    Must:
    - NOT request admin/UAC
    - NOT open interactive menus
    - exit quickly with code 0 if imports/bootstrap are OK
    """
    print("[ci-smoke] starting")
    try:
        from app.zapret_manager.core.app_context import AppContext
        from app.zapret_manager.core.paths import Paths
        from app.zapret_manager.features.zapret_runtime import runtime_health
        from app.zapret_manager import __version__
        from app.zapret_manager.core.singbox.binary import detect_singbox_binary, singbox_version

        root = Paths.detect_root()
        print(f"[ci-smoke] version: {__version__}")
        print(f"[ci-smoke] detected root: {root}")

        ctx = AppContext.bootstrap(argv=["--ci-smoke"])
        h = runtime_health(ctx)
        # Runtime is not expected to exist in CI (it is shipped in release bundle),
        # so we do NOT fail on runtime missing.
        print(f"[ci-smoke] runtime ok: {bool(h.get('ok'))}")
        if h.get("problems"):
            print(f"[ci-smoke] runtime problems: {h.get('problems')}")

        sb = detect_singbox_binary(root)
        print(f"[ci-smoke] sing-box binary: {'OK' if sb else 'MISSING'}")
        if sb:
            ver = singbox_version(sb.path)
            first = (ver.splitlines()[0].strip() if ver else "")
            print(f"[ci-smoke] sing-box version: {first or 'unknown'}")

        print("[ci-smoke] OK")
        return 0
    except Exception as e:
        print(f"[ci-smoke] FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        return 2

def _write_crash_log(text: str) -> Path | None:
    try:
        from app.zapret_manager.core.paths import Paths

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
        # CI smoke mode (must be before any privileged actions and UI).
        if _parse_smoke_flag(sys.argv[1:]):
            raise SystemExit(_run_ci_smoke())

        # Defer imports so we can capture ImportError into crash.log even when
        # module imports fail inside PyInstaller bundle.
        from app.zapret_manager.main import main

        # Setup logging as early as possible to capture admin-check decisions.
        try:
            from app.zapret_manager.core.log import setup_logging
            from app.zapret_manager.core.paths import Paths

            _root = Paths.detect_root()
            _paths = Paths.from_root(_root)
            _paths.ensure_dirs()
            setup_logging(_paths.logs_dir / "zapret_manager.log")
        except Exception:
            # Logging will be configured later in AppContext.bootstrap.
            pass

        # Must be before any privileged actions and before UI starts.
        from app.zapret_manager.utils.platform import ensure_admin_or_relaunch

        ensure_admin_or_relaunch()
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        tb = traceback.format_exc()

        # Collect extra context for crash log.
        try:
            from app.zapret_manager import __version__
            from app.zapret_manager.core.paths import Paths
            from app.zapret_manager.utils.platform import is_admin
            from app.zapret_manager.features.zapret_runtime import runtime_health

            root = Paths.detect_root()
            paths = Paths.from_root(root)
            paths.ensure_dirs()
            admin_flag = is_admin()

            # runtime_health needs context; create minimal ctx-like wrapper
            # via AppContext.bootstrap is too risky (might crash). We'll build a
            # small object with .paths and .state enough for runtime_health.
            from types import SimpleNamespace
            from app.zapret_manager.core.state import load_state

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

