import io
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from app.zapret_manager.utils.fsx import safe_extract_zip


class SafeExtractZipTests(unittest.TestCase):
    def test_extract_normal_zip(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            archive = root / "ok.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("dir/file.txt", "hello")

            out = root / "out"
            out.mkdir()
            with zipfile.ZipFile(archive, "r") as zf:
                safe_extract_zip(zf, out)

            self.assertEqual((out / "dir" / "file.txt").read_text(encoding="utf-8"), "hello")

    def test_rejects_path_traversal(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("../evil.txt", "boom")

            out = root / "out"
            out.mkdir()
            with zipfile.ZipFile(archive, "r") as zf:
                with self.assertRaises(RuntimeError):
                    safe_extract_zip(zf, out)


if __name__ == "__main__":
    unittest.main()