"""Doc/ghi du lieu nguoi dung: high score va ket qua calibration.

Tach thanh ham thuan de test duoc. Moi loi I/O deu duoc nuot va log,
khong bao gio lam crash game.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from core.paths import (get_calibration_path, get_high_score_path,
                        legacy_high_score_path)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# High score
# ---------------------------------------------------------------------
def load_high_score(path: Optional[Path] = None) -> int:
    """Doc high score; file thieu/hong -> 0. Tu migrate tu vi tri cu."""
    path = path or get_high_score_path()
    value = _read_score(path)
    if value is not None:
        return value

    # Migrate mot lan tu data/high_score.json (phien ban chay tu source cu)
    legacy = _read_score(legacy_high_score_path())
    if legacy is not None and legacy > 0:
        logger.info("Migrate high score cu (%d) sang LocalAppData", legacy)
        save_high_score(legacy, path)
        return legacy
    return 0


def _read_score(path: Path) -> Optional[int]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return max(0, int(data.get("high_score", 0)))
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def save_high_score(score: int, path: Optional[Path] = None) -> bool:
    path = path or get_high_score_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"high_score": int(score)}, f)
        return True
    except OSError as exc:
        logger.warning("Khong luu duoc high score: %s", exc)
        return False


def reset_high_score(path: Optional[Path] = None) -> None:
    save_high_score(0, path)


# ---------------------------------------------------------------------
# Calibration (chi luu threshold SO, khong luu hinh anh webcam)
# ---------------------------------------------------------------------
CALIBRATION_FORMAT_VERSION = 1


@dataclass(frozen=True)
class StoredCalibration:
    """Ket qua calibration gan voi mot camera index cu the."""
    camera_index: int
    up_margin_ratio: float
    down_margin_ratio: float
    measured_raise_range: float
    version: int = CALIBRATION_FORMAT_VERSION


def save_calibration(calib: StoredCalibration,
                     path: Optional[Path] = None) -> bool:
    path = path or get_calibration_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(calib), f, indent=2)
        return True
    except OSError as exc:
        logger.warning("Khong luu duoc calibration: %s", exc)
        return False


def load_calibration(camera_index: int,
                     path: Optional[Path] = None
                     ) -> Optional[StoredCalibration]:
    """Doc calibration da luu. Tra ve None neu thieu/hong/khac camera.

    Calibration gan voi camera index: doi camera -> None -> de nghi
    calibration lai.
    """
    path = path or get_calibration_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        calib = StoredCalibration(
            camera_index=int(data["camera_index"]),
            up_margin_ratio=float(data["up_margin_ratio"]),
            down_margin_ratio=float(data["down_margin_ratio"]),
            measured_raise_range=float(data["measured_raise_range"]),
            version=int(data.get("version", 1)),
        )
    except (OSError, ValueError, TypeError, KeyError):
        return None
    if calib.camera_index != camera_index:
        return None
    # Sanity check range de file bi sua tay khong pha detector
    if not (0.05 <= calib.up_margin_ratio <= 1.5):
        return None
    if not (0.0 <= calib.down_margin_ratio < calib.up_margin_ratio):
        return None
    return calib


def clear_calibration(path: Optional[Path] = None) -> None:
    path = path or get_calibration_path()
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
