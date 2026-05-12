
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from app.zapret_manager.core.paths import (
    AppPaths,
    get_project_root,
    create_app_paths,
    ensure_directories,
)


@pytest.fixture
def mock_project_root_env(tmp_path):
    # Create a dummy README.md in the mock root
    (tmp_path / "README.md").write_text("mock readme")
    # Create a nested structure to simulate app/zapret_manager/core
    (tmp_path / "app" / "zapret_manager" / "core").mkdir(parents=True)
    return tmp_path


def test_get_project_root_finds_readme(mock_project_root_env):
    # Simulate the script being run from a nested directory
    start_path = mock_project_root_env / "app" / "zapret_manager" / "core"
    root = get_project_root(start_path=start_path)
    assert root == mock_project_root_env


def test_get_project_root_falls_back_to_cwd(tmp_path):
    # No README.md, so it should fall back to cwd
    with patch("app.zapret_manager.core.paths.Path.cwd", return_value=tmp_path):
        root = get_project_root(start_path=tmp_path / "non_existent_dir")
        assert root == tmp_path


@pytest.fixture
def app_paths(mock_project_root_env):
    with patch(
        "app.zapret_manager.core.paths.get_project_root",
        return_value=mock_project_root_env,
    ):
        return create_app_paths()


def test_create_app_paths(mock_project_root_env, app_paths):
    assert app_paths.root_dir == mock_project_root_env
    assert app_paths.data_dir == mock_project_root_env / "DedZapretData" / "data"

    # Phase 2 canonical: config is stored under DedZapretData
    assert app_paths.config_file == mock_project_root_env / "DedZapretData" / "config.yaml"
    assert app_paths.sources_file == mock_project_root_env / "DedZapretData" / "sources.yaml"
    assert app_paths.state_file == mock_project_root_env / "DedZapretData" / "data" / "state" / "state.json"
    assert (
        app_paths.current_state_file
        == mock_project_root_env / "DedZapretData" / "data" / "state" / "current.json"
    )

    assert app_paths.logs_dir == mock_project_root_env / "DedZapretData" / "data" / "logs"
    assert app_paths.reports_dir == mock_project_root_env / "DedZapretData" / "data" / "reports"
    assert app_paths.backups_dir == mock_project_root_env / "DedZapretData" / "data" / "backups"
    assert app_paths.telemetry_dir == mock_project_root_env / "DedZapretData" / "data" / "telemetry"

    assert app_paths.runtime_dir == mock_project_root_env / "DedZapretData" / "runtime"
    assert (
        app_paths.zapret_runtime_dir
        == mock_project_root_env / "DedZapretData" / "runtime" / "zapret"
    )
    assert (
        app_paths.singbox_runtime_dir
        == mock_project_root_env / "DedZapretData" / "runtime" / "sing-box"
    )

    assert app_paths.strategies_dir == mock_project_root_env / "DedZapretData" / "data" / "strategies"
    assert (
        app_paths.strategies_builtin_dir
        == mock_project_root_env / "DedZapretData" / "data" / "strategies" / "builtin"
    )
    assert (
        app_paths.strategies_generated_dir
        == mock_project_root_env / "DedZapretData" / "data" / "strategies" / "generated"
    )
    assert (
        app_paths.strategies_custom_dir
        == mock_project_root_env / "DedZapretData" / "data" / "strategies" / "custom"
    )

    assert (
        app_paths.upstreams_dir
        == mock_project_root_env / "DedZapretData" / "data" / "upstreams"
    )


def test_ensure_directories(tmp_path):
    # Create a dummy root directory for testing ensure_directories
    test_root = tmp_path / "test_dedzapret_root"
    test_root.mkdir()
    
    with patch(
        "app.zapret_manager.core.paths.get_project_root", return_value=test_root
    ):
        paths = create_app_paths()
        ensure_directories(paths)

        expected_dirs = [
            paths.data_root,
            paths.data_dir,
            paths.logs_dir,
            paths.reports_dir,
            paths.backups_dir,
            paths.cache_dir,
            paths.results_dir,
            paths.telemetry_dir,
            paths.state_dir,
            paths.runtime_dir,
            paths.zapret_runtime_dir,
            paths.singbox_runtime_dir,
            paths.strategies_dir,
            paths.strategies_builtin_dir,
            paths.strategies_generated_dir,
            paths.strategies_custom_dir,
            paths.upstreams_dir,
            paths.flowseal_dir,
            paths.stressozz_dir,
            paths.nodes_dir,
            paths.profiles_dir,
        ]

        for d in expected_dirs:
            assert d.is_dir()