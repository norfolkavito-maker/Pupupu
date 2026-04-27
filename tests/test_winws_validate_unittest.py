import unittest


from app.zapret_manager.features.zapret_runtime import validate_winws_command


class TestWinwsValidate(unittest.TestCase):
    def test_rejects_game_filter_tcp(self):
        class _Ctx:
            pass

        ctx = _Ctx()
        problems = validate_winws_command(ctx, cmd=["winws.exe", "--wf-tcp=%GameFilterTCP%"], cwd=__import__("pathlib").Path("."))
        self.assertTrue(any("placeholder" in p for p in problems))

    def test_rejects_game_filter_udp(self):
        class _Ctx:
            pass

        ctx = _Ctx()
        problems = validate_winws_command(ctx, cmd=["winws.exe", "--wf-udp=%GameFilterUDP%"], cwd=__import__("pathlib").Path("."))
        self.assertTrue(any("placeholder" in p for p in problems))

    def test_rejects_any_percent_var(self):
        class _Ctx:
            pass

        ctx = _Ctx()
        problems = validate_winws_command(ctx, cmd=["winws.exe", "--arg=%SOME_VAR%"], cwd=__import__("pathlib").Path("."))
        self.assertTrue(any("placeholder" in p for p in problems))

    def test_rejects_newline_inside_argv(self):
        class _Ctx:
            pass

        ctx = _Ctx()
        problems = validate_winws_command(ctx, cmd=["winws.exe", "--foo=a\n--bar=b"], cwd=__import__("pathlib").Path("."))
        self.assertTrue(any("newline" in p for p in problems))

    def test_rejects_carriage_return_inside_argv(self):
        class _Ctx:
            pass

        ctx = _Ctx()
        problems = validate_winws_command(ctx, cmd=["winws.exe", "--foo=a\r--bar=b"], cwd=__import__("pathlib").Path("."))
        self.assertTrue(any("newline" in p for p in problems))

    def test_hostlist_domains_is_not_file(self):
        class _Ctx:
            pass

        ctx = _Ctx()
        problems = validate_winws_command(ctx, cmd=["winws.exe", "--hostlist-domains=discord.media"], cwd=__import__("pathlib").Path("."))
        # should not complain about missing file
        self.assertFalse(any("missing file" in p for p in problems))

    def test_checks_hostlist_quoted_file_exists(self):
        class _Ctx:
            pass

        ctx = _Ctx()

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "list.txt"
            p.write_text("a\n", encoding="utf-8")
            cmd = ["winws.exe", f"--hostlist=\"{p}\""]
            problems = validate_winws_command(ctx, cmd=cmd, cwd=Path(td))
            self.assertEqual(problems, [])

    def test_checks_ipset_quoted_file_exists(self):
        class _Ctx:
            pass

        ctx = _Ctx()

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ipset.txt"
            p.write_text("1.1.1.1\n", encoding="utf-8")
            cmd = ["winws.exe", f"--ipset=\"{p}\""]
            problems = validate_winws_command(ctx, cmd=cmd, cwd=Path(td))
            self.assertEqual(problems, [])

    def test_checks_ipset_exclude_quoted_file_exists(self):
        class _Ctx:
            pass

        ctx = _Ctx()

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "exclude.txt"
            p.write_text("8.8.8.8\n", encoding="utf-8")
            cmd = ["winws.exe", f"--ipset-exclude=\"{p}\""]
            problems = validate_winws_command(ctx, cmd=cmd, cwd=Path(td))
            self.assertEqual(problems, [])

    def test_reports_missing_hostlist_file(self):
        class _Ctx:
            pass

        ctx = _Ctx()
        problems = validate_winws_command(ctx, cmd=["winws.exe", "--hostlist=missing_file.txt"], cwd=__import__("pathlib").Path("."))
        self.assertTrue(any("missing file" in p for p in problems))

    def test_reports_missing_fake_pattern_file(self):
        class _Ctx:
            pass

        ctx = _Ctx()
        problems = validate_winws_command(ctx, cmd=["winws.exe", "--dpi-desync-fake=missing_fake.bin"], cwd=__import__("pathlib").Path("."))
        self.assertTrue(any("missing file" in p for p in problems))

    def test_accepts_valid_command_with_existing_files(self):
        class _Ctx:
            pass

        ctx = _Ctx()

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            list_file = td_path / "list.txt"
            fake_file = td_path / "stun.bin"
            list_file.write_text("googlevideo.com\n", encoding="utf-8")
            fake_file.write_bytes(b"fakecontent")

            cmd = [
                "winws.exe",
                "--hostlist=list.txt",
                "--dpi-desync-fake=stun.bin",
                "--dpi-desync=fake",
                "--hostlist-domains=discord.media"
            ]
            problems = validate_winws_command(ctx, cmd=cmd, cwd=td_path)
            self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
