import unittest
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
        ctx = MagicMock()
        ctx.paths = MagicMock()
        ctx.paths.root = Path("/tmp/DedZapretRoot")
        ctx.paths.cache_dir = Path("/tmp/cache")
        ctx.paths.logs_dir = Path("/tmp/logs")
        ctx.paths.data_root = Path("/tmp/DedZapretRoot/DedZapretData")
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

    @patch("app.zapret_manager.features.app_update.os.name", "nt")
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
    ):
        ctx = self._fake_ctx()
        plan = MagicMock()
        plan.repo = "o/r"
        plan.current_version = "0"
        plan.latest_tag = "v1"
        plan.asset = ReleaseAsset(name="DedZapret-portable-v1.zip", url="u", size=1)
        plan.download_path = Path("/tmp/cache/DedZapret-portable-v1.zip")
        plan.update_log = Path("/tmp/logs/update.log")
        plan.lock_file = Path("/tmp/lock")
        plan.updater_bat = Path("/tmp/updater.bat")
        mock_plan.return_value = plan
        mock_backup.return_value = Path("/tmp/backup.zip")
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "stat") as st:
            st.return_value.st_size = 123
            run_update(ctx)
        mock_popen.assert_called()

    @patch("app.zapret_manager.features.app_update.os.name", "posix")
    @patch("app.zapret_manager.features.app_update.build_update_plan")
    def test_run_update_windows_only(self, mock_plan):
        ctx = self._fake_ctx()
        plan = MagicMock()
        plan.repo = "o/r"
        plan.current_version = "0"
        plan.latest_tag = "v1"
        plan.asset = ReleaseAsset(name="DedZapret-portable-v1.zip", url="u", size=1)
        plan.download_path = Path("/tmp/cache/DedZapret-portable-v1.zip")
        plan.update_log = Path("/tmp/logs/update.log")
        plan.lock_file = Path("/tmp/lock")
        plan.updater_bat = Path("/tmp/updater.bat")
        mock_plan.return_value = plan
        with self.assertRaises(AppUpdateError):
            run_update(ctx)


if __name__ == "__main__":
    unittest.main()
