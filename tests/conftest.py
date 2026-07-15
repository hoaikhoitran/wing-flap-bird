"""Cau hinh chung cho test: headless SDL + co lap du lieu nguoi dung."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Headless: khong can man hinh / loa khi chay test & CI
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Cho phep import project khi chay pytest tu bat ky dau
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@pytest.fixture
def isolated_user_data(monkeypatch, tmp_path):
    """Chuyen huong TOAN BO user data (settings/highscore/calibration)
    vao thu muc tam - test khong dung cham LocalAppData that."""
    import core.paths as paths
    import core.settings as settings_mod
    import core.storage as storage_mod

    data_dir = tmp_path / "userdata"
    data_dir.mkdir()

    monkeypatch.setattr(paths, "get_user_data_dir", lambda: data_dir)
    monkeypatch.setattr(settings_mod, "get_settings_path",
                        lambda: data_dir / "settings.json")
    monkeypatch.setattr(storage_mod, "get_high_score_path",
                        lambda: data_dir / "high_score.json")
    monkeypatch.setattr(storage_mod, "get_calibration_path",
                        lambda: data_dir / "calibration.json")
    monkeypatch.setattr(storage_mod, "legacy_high_score_path",
                        lambda: data_dir / "legacy" / "high_score.json")
    return data_dir
