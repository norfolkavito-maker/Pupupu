import unittest
from pathlib import Path
import tempfile
from types import SimpleNamespace


class TestWinws2Compat(unittest.TestCase):
    def _ctx(self, tmp: Path):
        data_dir = tmp / "DedZapretData"
        runtime_dir = tmp / "runtime"
        zapret_dir = runtime_dir / "zapret"
        lists_dir = data_dir / "data" / "lists"
        logs_dir = data_dir / "data" / "logs"

        zapret_dir.mkdir(parents=True, exist_ok=True)
        lists_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        paths = SimpleNamespace(
            runtime_dir=runtime_dir,
            data_dir=data_dir,
            lists_dir=lists_dir,
            logs_dir=logs_dir,
            config_file=(tmp / "config.yaml"),
            sources_file=(tmp / "sources.yaml"),
            state_file=(tmp / "state.json"),
            # upstreams_dir intentionally missing (must not break resolver)
        )

        runtime = SimpleNamespace(winws_path=str(zapret_dir / "winws.exe"), winws2_path=str(zapret_dir / "winws2.exe"), installed=True)
        zapret_state = SimpleNamespace(
            pid=None,
            running=False,
            selected_strategy="",
            discord_profile=False,
            games_profile=False,
            rkn_enabled=False,
            wssize_enabled=False,
            discord_script=False,
        )
        state = SimpleNamespace(runtime=runtime, zapret=zapret_state)
        return SimpleNamespace(paths=paths, state=state)

    def test_build_command_uses_winws2_when_engine_winws2(self):
        from app.zapret_manager.features.zapret_runtime import build_command
        from app.zapret_manager.strategies.model import Strategy

        with tempfile.TemporaryDirectory(prefix="dedzapret_winws2_build_") as td:
            tmp = Path(td).resolve()
            ctx = self._ctx(tmp)
            # create core files
            zr = ctx.paths.runtime_dir / "zapret"
            (zr / "winws.exe").write_bytes(b"x")
            (zr / "winws2.exe").write_bytes(b"y")
            (zr / "WinDivert.dll").write_bytes(b"d")
            (zr / "WinDivert64.sys").write_bytes(b"s")
            (ctx.paths.lists_dir / "google.txt").write_text("x", encoding="utf-8")
            (ctx.paths.lists_dir / "exclude.txt").write_text("x", encoding="utf-8")
            (ctx.paths.lists_dir / "rkn.txt").write_text("x", encoding="utf-8")

            st = Strategy(name="t", engine="winws2", args=["--wf-tcp=443"], source_file="", upstream="", kind="base")
            cmd = build_command(ctx, st)
            self.assertTrue(cmd)
            self.assertTrue(str(cmd[0]).lower().endswith("winws2.exe"))

    def test_preflight_diagnostics_reports_missing_winws2(self):
        from app.zapret_manager.features.zapret_runtime import format_preflight_diagnostics_ru

        with tempfile.TemporaryDirectory(prefix="dedzapret_winws2_preflight_") as td:
            tmp = Path(td).resolve()
            ctx = self._ctx(tmp)
            zr = ctx.paths.runtime_dir / "zapret"
            # create only WinDivert; no winws2
            (zr / "WinDivert.dll").write_bytes(b"d")
            (zr / "WinDivert64.sys").write_bytes(b"s")
            (zr / "winws.exe").write_bytes(b"x")

            cmd = [str(zr / "winws2.exe"), "--wf-tcp=443"]
            text = format_preflight_diagnostics_ru(
                strategy_name="t",
                cmd=cmd,
                problems=["some error"],
                warnings=[],
                ctx=ctx,
            )
            self.assertIn("winws2.exe", text.lower())

    def test_runtime_asset_report_includes_winws2(self):
        from app.zapret_manager.features.diagnostics_artifacts import build_runtime_asset_report

        with tempfile.TemporaryDirectory(prefix="dedzapret_winws2_asset_report_") as td:
            tmp = Path(td).resolve()
            ctx = self._ctx(tmp)
            zr = ctx.paths.runtime_dir / "zapret"
            (zr / "winws.exe").write_bytes(b"x")
            (zr / "WinDivert.dll").write_bytes(b"d")
            (zr / "WinDivert64.sys").write_bytes(b"s")

            rep = build_runtime_asset_report(ctx)
            self.assertIn("winws2.exe", rep.get("checks", {}))


if __name__ == "__main__":
    unittest.main()
