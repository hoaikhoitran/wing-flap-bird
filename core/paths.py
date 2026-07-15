"""He thong duong dan: phan biet RESOURCE (chi doc, dong goi cung game)
va USER DATA (ghi duoc, nam trong %LOCALAPPDATA%\\WingFlapBird).

Quy tac:
  - KHONG dung os.chdir() de giai quyet duong dan.
  - KHONG phu thuoc current working directory.
  - KHONG ghi du lieu runtime vao thu muc cai dat game.
Ho tro: chay tu source, PyInstaller onedir (sys._MEIPASS tro vao _internal),
va PyInstaller onefile.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "WingFlapBird"


def is_frozen() -> bool:
    """True khi dang chay duoi dang .exe do PyInstaller dong goi."""
    return bool(getattr(sys, "frozen", False))


def app_root() -> Path:
    """Thu muc goc cua ung dung (noi chua exe hoac source)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    # core/paths.py -> core/ -> project root
    return Path(__file__).resolve().parent.parent


def resource_path(relative_path: str) -> Path:
    """Duong dan toi resource CHI DOC (model, font, sound, icon...).

    - PyInstaller (onedir/onefile): sys._MEIPASS tro toi thu muc bundle.
    - Source mode: tinh tu project root, khong phu thuoc cwd.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        return Path(meipass) / relative_path
    return app_root() / relative_path


# ---------------------------------------------------------------------
# User data (ghi duoc)
# ---------------------------------------------------------------------
def get_user_data_dir() -> Path:
    """%LOCALAPPDATA%\\WingFlapBird (tu tao neu chua co)."""
    try:
        from platformdirs import user_data_dir
        base = Path(user_data_dir(APP_DIR_NAME, appauthor=False,
                                  roaming=False))
    except Exception:
        # Fallback khi thieu platformdirs (chi xay ra o moi truong dev)
        local = os.environ.get("LOCALAPPDATA")
        base = (Path(local) if local else Path.home()) / APP_DIR_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_settings_path() -> Path:
    return get_user_data_dir() / "settings.json"


def get_high_score_path() -> Path:
    return get_user_data_dir() / "high_score.json"


def get_calibration_path() -> Path:
    return get_user_data_dir() / "calibration.json"


def get_log_dir() -> Path:
    d = get_user_data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_user_models_dir() -> Path:
    """Noi luu model tai ve o development mode (KHONG phai thu muc cai dat)."""
    d = get_user_data_dir() / "models"
    d.mkdir(parents=True, exist_ok=True)
    return d


def legacy_high_score_path() -> Path:
    """File high score cu (data/high_score.json canh source) de migrate."""
    return app_root() / "data" / "high_score.json"
