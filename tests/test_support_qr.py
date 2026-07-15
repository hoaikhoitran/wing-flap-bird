"""Test asset QR ung ho (crop tu anh MBBank goc cua developer).

LUU Y: theo yeu cau, test TUYET DOI KHONG scan / decode / OCR ma QR.
Chi kiem tra file, dinh dang, kich thuoc, kha nang load va viec game
khong crash khi thieu anh. Viec quet thu bang app ngan hang la
manual validation cua developer.
"""
from __future__ import annotations

import shutil
import sys

import pygame
import pytest

from core.links import SUPPORT_QR_RESOURCE
from core.paths import resource_path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

ORIGINAL = resource_path("assets/support/mbbank-qr-original.png")
CROPPED = resource_path(SUPPORT_QR_RESOURCE)


def test_original_mbbank_qr_asset_exists():
    """Anh goc phai duoc GIU NGUYEN trong source de doi chieu."""
    assert ORIGINAL.exists()
    assert ORIGINAL.stat().st_size > 0


def test_cropped_support_qr_asset_exists():
    assert CROPPED.exists()
    assert CROPPED.stat().st_size > 0


def test_cropped_qr_is_valid_png():
    assert CROPPED.read_bytes()[:8] == PNG_SIGNATURE


def test_cropped_qr_can_be_loaded_by_pygame():
    pygame.init()
    surface = pygame.image.load(str(CROPPED))
    w, h = surface.get_size()
    assert w > 0 and h > 0


def test_cropped_qr_has_reasonable_dimensions():
    pygame.init()
    surface = pygame.image.load(str(CROPPED))
    w, h = surface.get_size()
    # Du lon de dien thoai quet duoc sau khi scale trong game
    assert w > 300 and h > 300
    # Ban crop phai NHO hon poster goc (da bo nen trang tri phia duoi)
    original = pygame.image.load(str(ORIGINAL))
    ow, oh = original.get_size()
    assert w <= ow and h < oh


def test_missing_cropped_qr_does_not_crash(isolated_user_data, monkeypatch,
                                           tmp_path):
    """Thieu anh QR -> DonateScreen fallback text, game van chay."""
    import vision.camera as cam
    monkeypatch.setattr(cam, "scan_available_cameras", lambda *a, **k: [])

    from core.settings import GameSettings
    from game.game import Game, GameState
    game = Game(settings=GameSettings(), use_camera=False)
    try:
        # Tro resource_path cua donate screen toi file khong ton tai
        import game.screens.donate_screen as donate_mod
        monkeypatch.setattr(
            donate_mod, "resource_path",
            lambda rel: tmp_path / "khong_ton_tai" / rel)
        screen = game.screens[GameState.DONATE]
        screen._qr_raw = None
        screen._qr_scaled = None
        game.screens[GameState.PRIVACY_NOTICE]._accept()
        game.change_state(GameState.DONATE)
        assert not screen._has_qr
        for _ in range(5):
            game._update(1 / 60)
            game._draw()
    finally:
        game.shutdown()


def test_smoke_build_resolves_cropped_qr_resource(monkeypatch, tmp_path):
    """resource_path phai resolve dung ca o source mode lan frozen mode
    (sys._MEIPASS) - giong cach PyInstaller bundle assets/."""
    # Source mode
    assert resource_path(SUPPORT_QR_RESOURCE).exists()

    # Gia lap frozen mode: _MEIPASS tro toi thu muc bundle
    bundle = tmp_path / "bundle"
    target = bundle / SUPPORT_QR_RESOURCE
    target.parent.mkdir(parents=True)
    shutil.copyfile(CROPPED, target)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    frozen_resolved = resource_path(SUPPORT_QR_RESOURCE)
    assert frozen_resolved == target
    assert frozen_resolved.exists()
