import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


from app.zapret_manager.features.app_update import (
    AppUpdateError,
    build_update_plan,
    generate_updater_bat,
    run_update,
)
from app.zapret_manager.upstreams.github_release import GitHubRelease, ReleaseAsset


class TestAppUpdate(unittest.TestCase):
    def _fake_ctx(self):
        td = tempfile.TemporaryDirectory(prefix="dedzapret_test_")
        self.addCleanup(td.cleanup)

        root = Path(td.name).resolve() / "DedZapretRoot"
        cache = root / "DedZapretData" / "data" / "cache"
        logs = root / "DedZapretData" / "data" / "logs"
        data_root = root / "DedZapretData"

        # create minimal dirs to avoid accidental real FS writes outside temp
        logs.mkdir(parents=True, exist_ok=True)
        cache.mkdir(parents=True, exist_ok=True)

        ctx = MagicMock()
        ctx.paths = MagicMock()
        ctx.paths.root = root
        ctx.paths.cache_dir = cache
        ctx.paths.logs_dir = logs
        ctx.paths.data_root = data_root
        return ctx

    def test_generate_updater_bat_excludes_dedzapretdata(self):
        txt = generate_updater_bat(
            root_dir=Path("C:/DedZapret"),
            zip_path=Path("C:/tmp/DedZapret.zip"),
            log_path=Path("C:/DedZapretData/data/logs/update.log"),
        )
        self.assertIn("/XD DedZapretData", txt)

    @patch("app.zapret_manager.features.app_update.latest_release")
    def test_build_update_plan_selects_portable_asset(self, mock_latest):
        rel = GitHubRelease(
            tag="v1.2.3",
            assets=[
                ReleaseAsset(name="something.zip", url="u", size=1),
                ReleaseAsset(name="DedZapret-portable-v1.2.3.zip", url="u2", size=2),
            ],
        )
        mock_latest.return_value = rel
        ctx = self._fake_ctx()
        plan = build_update_plan(ctx, github_repo="o/r")
        self.assertEqual(plan.latest_tag, "v1.2.3")
        self.assertEqual(plan.asset.name, "DedZapret-portable-v1.2.3.zip")

    @patch("app.zapret_manager.features.app_update._is_windows", return_value=True)
    @patch("app.zapret_manager.features.app_update._write_update_log")
    @patch("app.zapret_manager.features.app_update._backup_dedzapret_data")
    @patch("app.zapret_manager.features.app_update._validate_zip")
    @patch("app.zapret_manager.features.app_update.download_asset")
    @patch("app.zapret_manager.features.app_update._acquire_lock")
    @patch("app.zapret_manager.features.app_update._release_lock")
    @patch("app.zapret_manager.features.app_update.generate_updater_bat", return_value="@echo off\r\n")
    @patch("app.zapret_manager.features.app_update.build_update_plan")
    @patch("app.zapret_manager.features.app_update.subprocess.Popen")
    def test_run_update_happy_path(
        self,
        mock_popen,
        mock_plan,
        _mock_gen_bat,
        _mock_release_lock,
        _mock_acquire_lock,
        mock_dl,
        mock_validate,
        mock_backup,
        _mock_write_log,
        _mock_is_windows,
    ):
        ctx = self._fake_ctx()
        # Make plan paths relative to our temp root (avoid /tmp hardcoding which breaks on Windows)
        plan_download = ctx.paths.cache_dir / "DedZapret-portable-v1.zip"
        plan_log = ctx.paths.logs_dir / "update.log"
        plan_lock = ctx.paths.data_root / "update.lock"
        plan_updater = ctx.paths.data_root / "updater.bat"

        plan = MagicMock()
        plan.repo = "o/r"
        plan.current_version = "0"
        plan.latest_tag = "v1"
        plan.asset = ReleaseAsset(name="DedZapret-portable-v1.zip", url="u", size=1)
        plan.download_path = plan_download
        plan.update_log = plan_log
        plan.lock_file = plan_lock
        plan.updater_bat = plan_updater
        mock_plan.return_value = plan
        mock_backup.return_value = ctx.paths.data_root / "backups" / "app_update" / "backup.zip"
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "stat") as st:
            st.return_value.st_size = 123
            run_update(ctx)
        mock_popen.assert_called()

    @patch("app.zapret_manager.features.app_update._is_windows", return_value=False)
    @patch("app.zapret_manager.features.app_update.build_update_plan")
    def test_run_update_windows_only(self, mock_plan, _mock_is_windows):
        ctx = self._fake_ctx()
        plan = MagicMock()
        plan.repo = "o/r"
        plan.current_version = "0"
        plan.latest_tag = "v1"
        plan.asset = ReleaseAsset(name="DedZapret-portable-v1.zip", url="u", size=1)
        plan.download_path = ctx.paths.cache_dir / "DedZapret-portable-v1.zip"
        plan.update_log = ctx.paths.logs_dir / "update.log"
        plan.lock_file = ctx.paths.data_root / "update.lock"
        plan.updater_bat = ctx.paths.data_root / "updater.bat"
        mock_plan.return_value = plan
        with self.assertRaises(AppUpdateError):
            run_update(ctx)


if __name__ == "__main__":
    unittest.main()
