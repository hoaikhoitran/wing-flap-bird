"""GameSettings: cau hinh nguoi dung, luu tai %LOCALAPPDATA%\\WingFlapBird.

Nguyen tac:
  - File thieu -> dung mac dinh, khong crash.
  - File JSON hong -> dung mac dinh, khong crash.
  - Thieu field -> tu bo sung mac dinh.
  - Moi gia tri deu duoc validate kieu + range.
  - Nguoi dung KHONG can sua config.py cho cac setting thong thuong.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, Optional

from core.paths import get_settings_path

logger = logging.getLogger(__name__)

VALID_DIFFICULTIES = ("easy", "normal")
VALID_LANGUAGES = ("vi", "en")
SENSITIVITY_MIN, SENSITIVITY_MAX = 0.5, 1.5
CAMERA_INDEX_MAX = 10


@dataclass
class GameSettings:
    camera_index: int = 0
    difficulty: str = "easy"
    sound_enabled: bool = True
    music_enabled: bool = True
    volume: int = 100                    # 0..100
    webcam_preview_enabled: bool = True
    fullscreen: bool = False
    show_fps: bool = True
    language: str = "vi"
    debug_enabled: bool = False          # PHAI mac dinh False trong release
    sensitivity: float = 1.0             # 0.5..1.5
    privacy_accepted_version: int = 0    # < PRIVACY_VERSION -> hien notice

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, path: Optional[Path] = None) -> "GameSettings":
        """Doc settings; moi loi deu tra ve gia tri hop le, khong raise."""
        path = path or get_settings_path()
        raw: dict[str, Any] = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                raw = data
        except FileNotFoundError:
            logger.info("settings.json chua ton tai - dung mac dinh")
        except (OSError, ValueError) as exc:
            logger.warning("settings.json loi (%s) - dung mac dinh", exc)

        settings = cls()
        for field in fields(cls):
            if field.name in raw:
                setattr(settings, field.name, raw[field.name])
        settings.validate()
        return settings

    def save(self, path: Optional[Path] = None) -> bool:
        """Luu settings; tra ve False neu khong ghi duoc (khong raise)."""
        path = path or get_settings_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
            return True
        except OSError as exc:
            logger.warning("Khong luu duoc settings: %s", exc)
            return False

    @classmethod
    def reset_to_defaults(cls, path: Optional[Path] = None) -> "GameSettings":
        """Khoi phuc mac dinh va luu ngay."""
        settings = cls()
        settings.save(path)
        return settings

    # ------------------------------------------------------------------
    def validate(self) -> None:
        """Ep kieu + clamp range cho moi field; gia tri sai -> mac dinh."""
        defaults = GameSettings.__dataclass_fields__

        def _int(name: str, lo: int, hi: int) -> None:
            try:
                value = int(getattr(self, name))
            except (TypeError, ValueError):
                value = defaults[name].default  # type: ignore[assignment]
            setattr(self, name, max(lo, min(hi, value)))

        def _float(name: str, lo: float, hi: float) -> None:
            try:
                value = float(getattr(self, name))
            except (TypeError, ValueError):
                value = defaults[name].default  # type: ignore[assignment]
            setattr(self, name, max(lo, min(hi, value)))

        def _bool(name: str) -> None:
            value = getattr(self, name)
            if not isinstance(value, bool):
                setattr(self, name, bool(defaults[name].default))

        def _choice(name: str, valid: tuple[str, ...]) -> None:
            value = getattr(self, name)
            if not isinstance(value, str) or value not in valid:
                setattr(self, name, str(defaults[name].default))

        _int("camera_index", 0, CAMERA_INDEX_MAX)  # khong nhan index am
        _choice("difficulty", VALID_DIFFICULTIES)
        _choice("language", VALID_LANGUAGES)
        _float("sensitivity", SENSITIVITY_MIN, SENSITIVITY_MAX)
        _int("volume", 0, 100)
        _int("privacy_accepted_version", 0, 999)
        for flag in ("sound_enabled", "music_enabled",
                     "webcam_preview_enabled", "fullscreen", "show_fps",
                     "debug_enabled"):
            _bool(flag)
