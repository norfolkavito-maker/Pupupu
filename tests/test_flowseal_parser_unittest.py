import unittest

from app.zapret_manager.strategies.flowseal_parser import extract_winws_command


class FlowsealParserTests(unittest.TestCase):
    def test_extract_winws_basic(self):
        txt = r"""
@echo off
set BIN=%~dp0bin\
set LISTS=%~dp0lists\
"%BIN%winws.exe" --wf-tcp=80,443 ^
  --hostlist="%LISTS%list-general.txt" ^
  --dpi-desync=fake
"""
        cmd = extract_winws_command(txt)
        self.assertIsNotNone(cmd)
        assert cmd is not None
        self.assertEqual(cmd.engine, "winws")
        self.assertIn("--wf-tcp=80,443", cmd.args)
        # Flowseal's %LISTS% should map to upstream-local lists dir, not manager lists.
        self.assertTrue(any("{FLOWSEAL_LISTS}" in a for a in cmd.args))

    def test_extract_winws2(self):
        txt = r"""
REM comment
%BIN%winws2.exe --new --filter-tcp=443 --dpi-desync=multisplit
"""
        cmd = extract_winws_command(txt)
        self.assertIsNotNone(cmd)
        assert cmd is not None
        self.assertEqual(cmd.engine, "winws2")


if __name__ == "__main__":
    unittest.main()

