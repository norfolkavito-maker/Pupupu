import unittest
from pathlib import Path
from types import SimpleNamespace


from app.zapret_manager.features.zapret_runtime import resolve_winws_args


class TestListsResolution(unittest.TestCase):
    def _ctx(self, root: Path):
        # minimal ctx for resolve_winws_args
        paths = SimpleNamespace(
            data_dir=root / "DedZapretData" / "data",
            lists_dir=root / "DedZapretData" / "data" / "lists",
            runtime_dir=root / "DedZapretData" / "runtime",
            zapret_runtime_dir=root / "DedZapretData" / "runtime" / "zapret",
            flowseal_lists_dir=root / "DedZapretData" / "data" / "upstreams" / "flowseal" / "lists",
            flowseal_bin_dir=root / "DedZapretData" / "data" / "upstreams" / "flowseal" / "bin",
        )
        return SimpleNamespace(paths=paths, state=SimpleNamespace(zapret=SimpleNamespace(discord_profile="", games_profile="")))

    def test_lists_placeholder_points_to_manager_lists(self):
        root = Path(".tmp_test_lists").resolve()
        (root / "DedZapretData" / "data" / "lists").mkdir(parents=True, exist_ok=True)
        ctx = self._ctx(root)
        out = resolve_winws_args(ctx, exe_dir=root, args=["--hostlist={LISTS}google.txt"])
        self.assertTrue(out[0].startswith("--hostlist="))
        p = Path(out[0].split("=", 1)[1])
        self.assertEqual(p, (root / "DedZapretData" / "data" / "lists" / "google.txt"))

    def test_rt_lists_placeholder_points_to_runtime_lists(self):
        root = Path(".tmp_test_rt_lists").resolve()
        (root / "DedZapretData" / "runtime" / "zapret" / "lists").mkdir(parents=True, exist_ok=True)
        ctx = self._ctx(root)
        out = resolve_winws_args(ctx, exe_dir=root, args=["--hostlist={RT_LISTS}google.txt"])
        self.assertTrue(out[0].startswith("--hostlist="))
        p = Path(out[0].split("=", 1)[1])
        self.assertEqual(p, (root / "DedZapretData" / "runtime" / "zapret" / "lists" / "google.txt"))

    def test_google_txt_alias_to_list_google_txt(self):
        root = Path(".tmp_test_alias").resolve()
        lists = root / "DedZapretData" / "data" / "lists"
        lists.mkdir(parents=True, exist_ok=True)
        # strategy asks google.txt, but only list-google.txt exists
        (lists / "list-google.txt").write_text("googlevideo.com\n", encoding="utf-8")
        ctx = self._ctx(root)
        out = resolve_winws_args(ctx, exe_dir=root, args=["--hostlist={LISTS}google.txt"])
        p = Path(out[0].split("=", 1)[1])
        self.assertEqual(p, (lists / "list-google.txt").resolve())


if __name__ == "__main__":
    unittest.main()
