import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


from app.zapret_manager.features import singbox_menu


class TestSingBoxMenuImportSingleLink(unittest.TestCase):
    def _make_ctx(self, td: Path) -> MagicMock:
        ctx = MagicMock()
        ctx.paths = MagicMock()
        ctx.paths.data_dir = td
        ctx.paths.logs_dir = td / "logs"
        ctx.paths.root = td
        return ctx

    def test_http_url_is_not_imported_as_node(self):
        # If user pastes http(s) URL into "Import single link",
        # we should NOT call import_node_from_link.
        with patch.object(singbox_menu, "clear", return_value=None), patch.object(
            singbox_menu, "ask", return_value="https://example.com/sub.txt"
        ), patch.object(singbox_menu, "pause", return_value=None), patch.object(
            singbox_menu, "safe_print", return_value=None
        ) as sp, patch.object(singbox_menu, "import_node_from_link") as imp:
            singbox_menu._sb_import_link(self._make_ctx(Path("/tmp")))
            imp.assert_not_called()
            # Ensure we printed a hint
            printed = "\n".join(str(c.args[0]) for c in sp.call_args_list if c.args)
            self.assertIn("subscription URL", printed)


if __name__ == "__main__":
    unittest.main()
