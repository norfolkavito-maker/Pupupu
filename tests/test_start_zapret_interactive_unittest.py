#!/usr/bin/env python3
"""
Tests for start_zapret_interactive() wiring to real pipeline.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

from app.zapret_manager.strategies.model import Strategy, Command, CommandType
from app.zapret_manager.core.app_context import AppContext
from app.zapret_manager.core.config import AppConfig
from app.zapret_manager.core.diagnostics import SessionRecorder
from app.zapret_manager.core.state import AppState, ZapretRunState, RuntimeState
from app.zapret_manager.core.paths import Paths
from app.zapret_manager.features.zapret_runtime import start_zapret_interactive, WinwsStartError


class TestStartZapretInteractive(unittest.TestCase):
    """Test start_zapret_interactive wiring to real pipeline."""

    def setUp(self):
        """Set up test context with minimal paths."""
        with tempfile.TemporaryDirectory() as td:
            self.root = Path(td)
            self.data_dir = self.root / "DedZapretData"
            self.data_dir.mkdir()
            self.runtime_dir = self.data_dir / "runtime"
            self.runtime_dir.mkdir()
            self.zapret_dir = self.runtime_dir / "zapret"
            self.zapret_dir.mkdir()
            self.fake_dir = self.zapret_dir / "files" / "fake"
            self.fake_dir.mkdir(parents=True)
            self.lists_dir = self.data_dir / "data" / "lists"
            self.lists_dir.mkdir(parents=True)

            # Create fake winws.exe
            self.winws = self.zapret_dir / "winws.exe"
            self.winws.write_bytes(b"fake exe")

            # Create WinDivert files
            (self.zapret_dir / "WinDivert.dll").write_bytes(b"fake dll")
            (self.zapret_dir / "WinDivert64.sys").write_bytes(b"fake sys")
            (self.zapret_dir / "blockcheck.cmd").write_bytes(b"@echo off")

            # Create required fake asset
            (self.fake_dir / "tls_clienthello_www_google_com.bin").write_bytes(b"fake bin")

            # Create required list file
            (self.lists_dir / "google.txt").write_text("google.com\n")

            self.paths = Paths.from_root(self.root)
            self.state = AppState(
                runtime=RuntimeState(
                    installed=True,
                    runtime_path=str(self.runtime_dir),
                    winws_path=str(self.winws),
                ),
                zapret=ZapretRunState(running=False, pid=None, base_strategy="", selected_strategy=""),
            )
            self.config = AppConfig()
            self.diagnostics = SessionRecorder(
                logs_dir=self.paths.logs_dir,
                enabled=False,
                record_console_io=False,
                record_subprocess=False,
            )
            self.ctx = AppContext(
                root=self.root,
                paths=self.paths,
                config=self.config,
                state=self.state,
                diagnostics=self.diagnostics,
            )

    def test_start_zapret_interactive_calls_command_builder(self):
        """Test that start_zapret_interactive calls build_command."""
        strategy = Strategy(
            id="test",
            name="test",
            commands=[Command(type=CommandType.WINWS, command="--new --filter-tcp=443")],
            engine="winws",
            kind="base",
            is_valid=True,
        )

        with patch("app.zapret_manager.features.zapret_runtime.is_windows", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.is_admin", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.require_runtime_ok"), \
             patch("app.zapret_manager.features.zapret_runtime.detect_runtime_files"), \
             patch("app.zapret_manager.features.zapret_runtime.validate_winws_command", return_value=[]), \
             patch("app.zapret_manager.features.zapret_runtime.popen_detached") as mock_popen, \
             patch("app.zapret_manager.features.zapret_runtime.verify_winws_started"):
            mock_proc = Mock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            cmd = start_zapret_interactive(self.ctx, strategy)

            # Verify command was built
            self.assertTrue(len(cmd) > 0)
            self.assertEqual(cmd[0], str(self.winws))

    def test_missing_assets_prevents_subprocess(self):
        """Test that missing assets prevents subprocess call."""
        strategy = Strategy(
            id="test",
            name="test",
            commands=[Command(type=CommandType.WINWS, command="--new")],
            engine="winws",
            kind="base",
            is_valid=False,
            missing_assets=["fake.bin"],
        )

        with patch("app.zapret_manager.features.zapret_runtime.is_windows", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.is_admin", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.require_runtime_ok"), \
             patch("app.zapret_manager.features.zapret_runtime.detect_runtime_files"):
            with self.assertRaises(WinwsStartError) as cm:
                start_zapret_interactive(self.ctx, strategy)

            self.assertIn("невалидна", str(cm.exception))

    def test_unresolved_placeholder_prevents_subprocess(self):
        """Test that unresolved placeholders prevent subprocess call."""
        strategy = Strategy(
            id="test",
            name="test",
            commands=[Command(type=CommandType.WINWS, command="--new")],
            engine="winws",
            kind="base",
            is_valid=False,
            unresolved_placeholders=["{FLOWSEAL_BIN}"],
        )

        with patch("app.zapret_manager.features.zapret_runtime.is_windows", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.is_admin", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.require_runtime_ok"), \
             patch("app.zapret_manager.features.zapret_runtime.detect_runtime_files"):
            with self.assertRaises(WinwsStartError) as cm:
                start_zapret_interactive(self.ctx, strategy)

            self.assertIn("невалидна", str(cm.exception))

    def test_valid_command_calls_subprocess_mocked(self):
        """Test that valid command calls subprocess.Popen (mocked)."""
        strategy = Strategy(
            id="test",
            name="test",
            commands=[Command(type=CommandType.WINWS, command="--new --filter-tcp=443")],
            engine="winws",
            kind="base",
            is_valid=True,
        )

        with patch("app.zapret_manager.features.zapret_runtime.is_windows", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.is_admin", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.require_runtime_ok"), \
             patch("app.zapret_manager.features.zapret_runtime.detect_runtime_files"), \
             patch("app.zapret_manager.features.zapret_runtime.validate_winws_command", return_value=[]), \
             patch("app.zapret_manager.features.zapret_runtime.popen_detached") as mock_popen, \
             patch("app.zapret_manager.features.zapret_runtime.verify_winws_started"):
            mock_proc = Mock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            cmd = start_zapret_interactive(self.ctx, strategy)

            # Verify subprocess was called
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            self.assertEqual(call_args[0][0][0], str(self.winws))

    def test_state_running_pid_saved_on_success(self):
        """Test that state.running and state.pid are saved on success."""
        strategy = Strategy(
            id="test",
            name="test",
            commands=[Command(type=CommandType.WINWS, command="--new --filter-tcp=443")],
            engine="winws",
            kind="base",
            is_valid=True,
        )

        with patch("app.zapret_manager.features.zapret_runtime.is_windows", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.is_admin", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.require_runtime_ok"), \
             patch("app.zapret_manager.features.zapret_runtime.detect_runtime_files"), \
             patch("app.zapret_manager.features.zapret_runtime.validate_winws_command", return_value=[]), \
             patch("app.zapret_manager.features.zapret_runtime.popen_detached") as mock_popen, \
             patch("app.zapret_manager.features.zapret_runtime.verify_winws_started"), \
             patch("app.zapret_manager.core.state.save_state"):
            mock_proc = Mock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            start_zapret_interactive(self.ctx, strategy)

            # Verify state was updated
            self.assertTrue(self.ctx.state.zapret.running)
            self.assertEqual(self.ctx.state.zapret.pid, 12345)
            self.assertEqual(self.ctx.state.zapret.base_strategy, "test")
            self.assertEqual(self.ctx.state.zapret.selected_strategy, "test")

    def test_readable_error_on_failure(self):
        """Test that readable Russian error is saved on failure."""
        strategy = Strategy(
            id="test",
            name="test",
            commands=[Command(type=CommandType.WINWS, command="--new")],
            engine="winws",
            kind="base",
            is_valid=False,
            missing_assets=["missing.bin"],
        )

        with patch("app.zapret_manager.features.zapret_runtime.is_windows", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.is_admin", return_value=True), \
             patch("app.zapret_manager.features.zapret_runtime.require_runtime_ok"), \
             patch("app.zapret_manager.features.zapret_runtime.detect_runtime_files"):
            with self.assertRaises(WinwsStartError) as cm:
                start_zapret_interactive(self.ctx, strategy)

            # Verify readable Russian error
            error_msg = str(cm.exception)
            self.assertIn("Стратегия невалидна", error_msg)


if __name__ == "__main__":
    unittest.main()
