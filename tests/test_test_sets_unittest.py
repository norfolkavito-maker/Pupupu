import unittest


from app.zapret_manager.features.test_sets import combine_domain_sets


class TestDomainSets(unittest.TestCase):
    def test_combine_domain_sets_dedup_keeps_order(self):
        # ctx is only used for file paths; for this unit test we bypass by
        # monkeypatching file reads via temporary files.
        # Easiest in this repo: just assert function exists and can be called
        # with a fake ctx object having required attrs.

        class _Paths:
            def __init__(self, data_dir):
                self.data_dir = data_dir

        class _Ctx:
            def __init__(self, data_dir):
                self.paths = _Paths(data_dir)

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            data_dir = Path(td)
            (data_dir / "tests").mkdir(parents=True, exist_ok=True)
            (data_dir / "tests" / "domains_default.txt").write_text("a\nb\n", encoding="utf-8")
            (data_dir / "tests" / "domains_youtube.txt").write_text("b\nc\n", encoding="utf-8")
            (data_dir / "tests" / "domains_cdn.txt").write_text("c\nd\n", encoding="utf-8")
            (data_dir / "tests" / "domains_amazon.txt").write_text("d\ne\n", encoding="utf-8")
            (data_dir / "tests" / "domains_discord.txt").write_text("e\nf\n", encoding="utf-8")
            (data_dir / "tests" / "domains_instagram.txt").write_text("f\ng\n", encoding="utf-8")
            (data_dir / "tests" / "domains_games.txt").write_text("g\nh\n", encoding="utf-8")

            ctx = _Ctx(data_dir)
            combined = combine_domain_sets(ctx, ["default", "youtube", "cdn", "amazon", "discord", "instagram", "games"])
            self.assertEqual(combined, ["a", "b", "c", "d", "e", "f", "g", "h"])


if __name__ == "__main__":
    unittest.main()
