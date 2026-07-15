"""Thong tin phien ban duy nhat cho toan bo ung dung.

Moi noi khac (window title, credits, log, build metadata, release notes)
PHAI import tu day, khong hard-code version o cho khac.
"""
from __future__ import annotations

APP_NAME = "Wing Flap Bird"
APP_VERSION = "0.1.0-beta"
APP_AUTHOR = "hoaikhoitran"

# Tang so nay khi PRIVACY.md thay doi noi dung quan trong ->
# nguoi dung se thay lai man hinh privacy notice.
PRIVACY_VERSION = 1


def window_title() -> str:
    return f"{APP_NAME} v{APP_VERSION}"
