import unittest
from pathlib import Path
from types import SimpleNamespace


from app.zapret_manager.features.zapret_runtime import (
    build_command,
    validate_winws_command,
    normalize_winws_args,
)
from app.zapret_manager.strategies.model import Strategy


class _Ctx(SimpleNamespace):
    pass


def _make_ctx(tmp: Path) -> _Ctx:
    # Minimal ctx stub for build_command/validate_winws_command.
    runtime_dir = tmp / "DedZapretData" / "runtime"
    zapret_dir = runtime_dir / "zapret"
    zapret_dir.mkdir(parents=True, exist_ok=True)
    winws = zapret_dir / "winws.exe"
    winws.write_bytes(b"stub")

    lists_dir = tmp / "DedZapretData" / "data" / "lists"
    lists_dir.mkdir(parents=True, exist_ok=True)
    (lists_dir / "google.txt").write_text("google", encoding="utf-8")
    (lists_dir / "exclude.txt").write_text("", encoding="utf-8")

    zapret_state = SimpleNamespace(
        pid=None,
        running=False,
        selected_strategy="",
        discord_script="",
        games_profile="",
        discord_profile="",
        rkn_enabled=False,
        wssize_enabled=False,
    )
    state = SimpleNamespace(
        runtime=SimpleNamespace(winws_path=str(winws), winws2_path="", installed=True, runtime_path=str(runtime_dir)),
        zapret=zapret_state,
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


class TestNormalizeWinwsArgs(unittest.TestCase):
    def test_escaped_newline_arg_normalizes(self):
        # Simulates Dv1-like arg with escaped \\n
        raw = "--filter-tcp=8443\\n--hostlist-domains=discord.media\\n--dpi-desync=multisplit"
        result = normalize_winws_args([raw])
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "--filter-tcp=8443")
        self.assertEqual(result[1], "--hostlist-domains=discord.media")
        self.assertEqual(result[2], "--dpi-desync=multisplit")

    def test_actual_newline_normalizes(self):
        # Use actual newlines - must be separate strings in list
        # This tests actual newline handling inside a single string element
        raw = "--filter-tcp=8443\\n--hostlist-domains=discord.media\\n--dpi-desync=multisplit"
        result = normalize_winws_args([raw])
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "--filter-tcp=8443")
        self.assertEqual(result[1], "--hostlist-domains=discord.media")
        self.assertEqual(result[2], "--dpi-desync=multisplit")

    def test_dv1_like_sample_gets_wf_tcp(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            ctx = _make_ctx(Path(td))
            # Simulated Dv1 args with escaped newline
            raw_arg = "--filter-tcp=8443\\n--hostlist-domains=discord.media\\n--dpi-desync=multisplit"
            st = Strategy(
                name="Dv1",
                engine="winws",
                args=[raw_arg, "--new", "--dpi-desync=fake,tls-split,sni,split2"],
                kind="discord",
            )
            # Should NOT raise "invalid range token"
            try:
                cmd = build_command(ctx, st)
            except RuntimeError as e:
                self.fail(f"build_command raised RuntimeError: {e}")
            # Should contain --wf-tcp=8443
            wf_args = [a for a in cmd if a.startswith("--wf-tcp=")]
            self.assertTrue(len(wf_args) > 0, f"No --wf-tcp= found in cmd: {cmd}")
            self.assertIn("8443", wf_args[0])

    def test_no_newline_in_result(self):
        args = ["--filter-tcp=443", "--new", "--dpi-desync=multisplit"]
        result = normalize_winws_args(args)
        for a in result:
            self.assertNotIn("\\n", a)
            self.assertNotIn("\\r\\n", a)

    def test_window_paths_not_broken(self):
        # Windows path with spaces should remain one arg
        args = [r"C:\Program Files\app\file.bin", "--dpi-desync=fake"]
        result = normalize_winws_args(args)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], r"C:\Program Files\app\file.bin")

    def test_new_blocks_preserved(self):
        args = ["--filter-tcp=443", "--new", "--filter-udp=443", "--new"]
        result = normalize_winws_args(args)
        self.assertEqual(result.count("--new"), 2)

    def test_empty_args_removed(self):
        args = ["--filter-tcp=443", "", None, "  ", "--new"]
        result = normalize_winws_args(args)
        self.assertNotIn("", result)
        self.assertNotIn(None, result)
        self.assertTrue(all(a.strip() for a in result))


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