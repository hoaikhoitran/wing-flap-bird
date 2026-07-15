"""Test capture mode: chay renderer that, sinh du screenshot chat luong."""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from core.paths import app_root

EXPECTED = ("main-menu.png", "character-select.png", "settings.png",
            "how-to-play.png", "gameplay.png", "game-over.png")


@pytest.fixture(scope="module")
def captured(tmp_path_factory):
    out = tmp_path_factory.mktemp("shots")
    from tools.capture_readme import run_capture
    code = run_capture(str(out))
    return code, out


def test_capture_exits_zero(captured):
    code, _ = captured
    assert code == 0


def test_all_screenshots_generated_nonempty(captured):
    _, out = captured
    for name in EXPECTED:
        path = out / name
        assert path.exists(), f"Thieu {name}"
        assert path.stat().st_size > 10_000, f"{name} qua nho"


def test_screenshots_not_single_color(captured):
    """Screenshot khong duoc toan 1 mau (man hinh den/trang)."""
    _, out = captured
    pygame.init()
    for name in EXPECTED:
        surf = pygame.image.load(str(out / name))
        small = pygame.transform.scale(surf, (60, 42))
        colors = {small.get_at((x, y))[:3]
                  for x in range(60) for y in range(42)}
        # Man hinh menu toi gian van >10 mau; man hinh blank ~1-3 mau
        assert len(colors) > 10, f"{name} chi co {len(colors)} mau"


def test_gameplay_screenshot_rich(captured):
    """Gameplay: nhieu mau (background 2.5D + obstacle + HUD)."""
    _, out = captured
    pygame.init()
    surf = pygame.image.load(str(out / "gameplay.png"))
    assert surf.get_size() == (1000, 700)
    small = pygame.transform.scale(surf, (100, 70))
    colors = {small.get_at((x, y))[:3]
              for x in range(100) for y in range(70)}
    assert len(colors) > 200, f"gameplay ngheo mau: {len(colors)}"


def test_capture_does_not_open_browser_or_camera():
    """Source capture khong dung webbrowser / khong yeu cau camera."""
    src = (app_root() / "tools" / "capture_readme.py").read_text(
        encoding="utf-8")
    assert "webbrowser" not in src
    assert "use_camera=False" in src
