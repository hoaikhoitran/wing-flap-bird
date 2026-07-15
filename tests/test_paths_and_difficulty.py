"""Test core.paths (source mode) va config.get_difficulty_config."""
from __future__ import annotations

import config
from core.paths import app_root, get_user_data_dir, resource_path


def test_resource_path_resolves_project_files():
    assert resource_path("main.py").exists()
    assert resource_path("assets").is_dir()


def test_resource_path_does_not_depend_on_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert resource_path("main.py").exists()


def test_bundled_pose_model_present_and_valid():
    """Model PHAI duoc bundle de release khong can Internet lan dau."""
    model = resource_path("assets/models/pose_landmarker_lite.task")
    assert model.exists()
    assert model.stat().st_size > 1_000_000


def test_user_data_dir_created():
    d = get_user_data_dir()
    assert d.exists()
    assert d.name == "WingFlapBird"


def test_app_root_is_project_root():
    assert (app_root() / "config.py").exists()


# ----------------------------------------------------------------------
def test_difficulty_easy_values():
    diff = config.get_difficulty_config("easy")
    assert diff.gravity == 800.0
    assert diff.flap_force == -400.0
    assert diff.max_fall_speed == 210.0
    assert diff.pipe_speed == 150.0
    assert 210 <= diff.pipe_gap_min <= diff.pipe_gap_max <= 250
    assert diff.flap_cooldown_ms == 220
    assert abs(diff.flap_cooldown - 0.22) < 1e-9
    assert abs(diff.pipe_spacing - 150.0 * 2.2) < 1e-6


def test_difficulty_normal_is_harder_than_easy():
    easy = config.get_difficulty_config("easy")
    normal = config.get_difficulty_config("normal")
    assert normal.gravity > easy.gravity
    assert normal.pipe_speed > easy.pipe_speed
    assert normal.pipe_gap_min < easy.pipe_gap_min


def test_unknown_difficulty_falls_back_to_easy():
    assert config.get_difficulty_config("nightmare").name == "easy"
    assert config.get_difficulty_config("").name == "easy"
