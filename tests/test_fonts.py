"""Test font Be Vietnam Pro bundle + cam SysFont/Font(None) trong runtime."""
from __future__ import annotations

import unicodedata
from pathlib import Path

import pygame
import pytest

from core import font_manager as fm
from core.paths import app_root, resource_path

_WEIGHTS = ("Regular", "Medium", "SemiBold", "Bold", "ExtraBold")
_VN_SAMPLE = ("Trường Đại học – Vỗ cánh, Hiệu chỉnh, Cài đặt, Ủng hộ, "
              "Kỷ lục mới!")

# File runtime (KHONG gom tests/scripts/tools dev)
_RUNTIME_DIRS = ("game", "core", "vision")


def _runtime_files() -> list[Path]:
    root = app_root()
    files = [root / "main.py", root / "config.py"]
    for d in _RUNTIME_DIRS:
        files += sorted((root / d).rglob("*.py"))
    return files


def test_font_files_exist():
    for weight in _WEIGHTS:
        path = resource_path(f"assets/fonts/BeVietnamPro-{weight}.ttf")
        assert path.exists(), f"Thieu font {weight}"
        assert path.stat().st_size > 50_000


def test_ofl_license_bundled():
    ofl = resource_path("assets/fonts/OFL.txt")
    assert ofl.exists()
    text = ofl.read_text(encoding="utf-8", errors="ignore")
    assert "SIL OPEN FONT LICENSE" in text.upper()


def test_no_sysfont_in_runtime():
    for f in _runtime_files():
        text = f.read_text(encoding="utf-8", errors="ignore")
        assert "SysFont(" not in text, f"SysFont con trong {f}"


def test_no_font_none_in_runtime():
    for f in _runtime_files():
        text = f.read_text(encoding="utf-8", errors="ignore")
        assert "Font(None" not in text, f"Font(None con trong {f}"


def test_all_translations_render():
    """Moi chuoi vi/en trong i18n render khong exception, khong rong."""
    pygame.init()
    from game.i18n import STRINGS
    font = fm.get("body")
    for key, entry in STRINGS.items():
        for lang in ("vi", "en"):
            text = entry.get(lang, "")
            if not text:
                continue
            surf = font.render(fm.nfc(text), True, (255, 255, 255))
            assert surf.get_width() > 0, f"{key}/{lang} render rong"
            assert surf.get_height() > 0


def test_vietnamese_sample_renders_all_roles():
    pygame.init()
    for role in ("display", "title", "heading", "body", "button",
                 "caption", "score", "debug"):
        surf = fm.render(role, _VN_SAMPLE, (255, 255, 255))
        assert surf.get_width() > 100
        assert surf.get_height() > 0


def test_nfc_normalization():
    # Chuoi decomposed (NFD) phai duoc normalize ve NFC truoc khi render
    decomposed = unicodedata.normalize("NFD", "Vỗ cánh Kỷ lục")
    assert fm.nfc(decomposed) == unicodedata.normalize("NFC", decomposed)


def test_vietnamese_no_missing_glyph():
    """Khong co glyph .notdef: moi ky tu co dau phai co glyph rieng
    (do bang metrics - ky tu thieu glyph thuong tra ve cung 1 khuon)."""
    pygame.init()
    font = fm.get("body")
    # Neu font co glyph, cac ky tu nay co do rong metrics > 0
    for ch in "ỗơưậệỷủịếề":
        metrics = font.metrics(ch)
        assert metrics and metrics[0] is not None, f"Thieu glyph '{ch}'"
        assert metrics[0][4] > 0, f"Glyph '{ch}' rong"
