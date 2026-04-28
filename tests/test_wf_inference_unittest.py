import unittest
from pathlib import Path
from types import SimpleNamespace


from app.zapret_manager.features.zapret_runtime import build_command, validate_winws_command
from app.zapret_manager.strategies.model import Strategy


class _Ctx(SimpleNamespace):
    pass


def _make_ctx(tmp: Path) -> _Ctx:
    # Minimal ctx stub for build_command/validate_winws_command.
    # NOTE: build_command expects ctx.state.runtime.winws_path, ctx.paths.runtime_dir, ctx.paths.lists_dir.
    runtime_dir = tmp / "DedZapretData" / "runtime"
    zapret_dir = runtime_dir / "zapret"
    zapret_dir.mkdir(parents=True, exist_ok=True)
    winws = zapret_dir / "winws.exe"
    winws.write_bytes(b"stub")

    lists_dir = tmp / "DedZapretData" / "data" / "lists"
    lists_dir.mkdir(parents=True, exist_ok=True)
    (lists_dir / "google.txt").write_text("google", encoding="utf-8")
    (lists_dir / "exclude.txt").write_text("", encoding="utf-8")

    state = SimpleNamespace(
        runtime=SimpleNamespace(winws_path=str(winws), winws2_path="", installed=True, runtime_path=str(runtime_dir)),
        zapret=SimpleNamespace(
            pid=None,
            running=False,
            selected_strategy="",
            discord_profile="",
            games_profile="",
            discord_script="",
            rkn_enabled=False,
            wssize_enabled=False,
        ),
    )
    paths = SimpleNamespace(runtime_dir=runtime_dir, lists_dir=lists_dir, state_file=tmp / "state.json", logs_dir=tmp / "logs")
    return _Ctx(root=tmp, paths=paths, state=state)


class TestWfInference(unittest.TestCase):
    def test_infer_wf_tcp_single(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            ctx = _make_ctx(Path(td))
            st = Strategy(name="t", engine="winws", args=["--filter-tcp=443"], kind="base")
            cmd = build_command(ctx, st)
            self.assertIn("--wf-tcp=443", cmd)
            # must be right after exe
            self.assertEqual(cmd[1], "--wf-tcp=443")

    def test_infer_wf_tcp_union_dedup_sort(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            ctx = _make_ctx(Path(td))
            st = Strategy(
                name="t",
                engine="winws",
                args=["--filter-tcp=443", "--new", "--filter-tcp=80,443"],
                kind="base",
            )
            cmd = build_command(ctx, st)
            self.assertIn("--wf-tcp=80,443", cmd)

    def test_existing_wf_not_duplicated(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            ctx = _make_ctx(Path(td))
            st = Strategy(name="t", engine="winws", args=["--wf-tcp=443", "--filter-tcp=443"], kind="base")
            cmd = build_command(ctx, st)
            self.assertEqual(sum(1 for a in cmd if a.startswith("--wf-tcp=")), 1)

    def test_infer_wf_udp(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            ctx = _make_ctx(Path(td))
            st = Strategy(name="t", engine="winws", args=["--filter-udp=443"], kind="base")
            cmd = build_command(ctx, st)
            self.assertIn("--wf-udp=443", cmd)


class TestPortValidation(unittest.TestCase):
    def test_invalid_ports_rejected(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            ctx = _make_ctx(Path(td))
            cwd = Path(td) / "DedZapretData" / "runtime" / "zapret"
            problems = validate_winws_command(ctx, cmd=["winws.exe", "--wf-tcp=443,,80"], cwd=cwd)
            self.assertTrue(any("invalid --wf-tcp" in p for p in problems))

    def test_reversed_range_rejected(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            ctx = _make_ctx(Path(td))
            cwd = Path(td) / "DedZapretData" / "runtime" / "zapret"
            problems = validate_winws_command(ctx, cmd=["winws.exe", "--wf-tcp=9000-2000"], cwd=cwd)
            self.assertTrue(any("reversed range" in p for p in problems))


class TestNewSanity(unittest.TestCase):
    def test_command_ends_with_new_rejected(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            ctx = _make_ctx(Path(td))
            cwd = Path(td) / "DedZapretData" / "runtime" / "zapret"
            problems = validate_winws_command(ctx, cmd=["winws.exe", "--new"], cwd=cwd)
            self.assertTrue(any("ends with --new" in p for p in problems))

    def test_duplicate_new_rejected(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            ctx = _make_ctx(Path(td))
            cwd = Path(td) / "DedZapretData" / "runtime" / "zapret"
            problems = validate_winws_command(ctx, cmd=["winws.exe", "--new", "--new"], cwd=cwd)
            self.assertTrue(any("duplicate --new" in p for p in problems))


class TestAssets(unittest.TestCase):
    def test_missing_hostlist_exclude_is_error(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            ctx = _make_ctx(Path(td))
            cwd = Path(td) / "DedZapretData" / "runtime" / "zapret"
            problems = validate_winws_command(
                ctx,
                cmd=["winws.exe", f"--hostlist-exclude={Path(td) / 'nope.txt'}"],
                cwd=cwd,
            )
            self.assertTrue(any("missing file for --hostlist-exclude" in p for p in problems))

    def test_empty_hostlist_exclude_is_warn(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            ctx = _make_ctx(Path(td))
            cwd = Path(td) / "DedZapretData" / "runtime" / "zapret"
            exclude = Path(td) / "DedZapretData" / "data" / "lists" / "exclude.txt"
            problems = validate_winws_command(ctx, cmd=["winws.exe", f"--hostlist-exclude={exclude}"], cwd=cwd)
            self.assertTrue(any(p.startswith("WARN:") for p in problems))


if __name__ == "__main__":
    unittest.main()
