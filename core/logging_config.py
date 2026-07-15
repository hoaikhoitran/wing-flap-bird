"""Cau hinh logging: rotating file trong LocalAppData + global exception hook.

Quy tac:
  - Release mac dinh INFO, debug mode dung DEBUG.
  - Khong ghi frame webcam, khong ghi landmark lien tuc trong release.
  - Loi ghi log khong bao gio lam crash game.
"""
from __future__ import annotations

import logging
import logging.handlers
import platform
import sys
from pathlib import Path

from core.paths import get_log_dir
from core.version import APP_NAME, APP_VERSION

LOG_FILE_NAME = "wing_flap_bird.log"
_MAX_BYTES = 512 * 1024
_BACKUP_COUNT = 3


def get_log_file_path() -> Path:
    return get_log_dir() / LOG_FILE_NAME


def setup_logging(debug: bool = False) -> logging.Logger:
    """Khoi tao root logger. Goi mot lan luc app start."""
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    try:
        handler = logging.handlers.RotatingFileHandler(
            get_log_file_path(), maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT, encoding="utf-8")
        handler.setFormatter(fmt)
        root.addHandler(handler)
    except Exception:
        pass  # khong ghi duoc log (thu muc chi doc?) -> van chay tiep

    if debug:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        root.addHandler(console)

    return logging.getLogger("wingflap")


def log_system_info(logger: logging.Logger) -> None:
    logger.info("%s v%s starting", APP_NAME, APP_VERSION)
    logger.info("OS: %s %s (%s)", platform.system(), platform.release(),
                platform.machine())
    logger.info("Python: %s", sys.version.split()[0])
    logger.info("Frozen build: %s", bool(getattr(sys, "frozen", False)))


def install_excepthook(logger: logging.Logger) -> None:
    """Ghi moi unhandled exception vao log truoc khi thoat."""
    def hook(exc_type, exc_value, exc_tb):
        try:
            logger.critical("Unhandled exception",
                            exc_info=(exc_type, exc_value, exc_tb))
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = hook
