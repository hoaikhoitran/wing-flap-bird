"""Test layout: khong overlap widget, text vua nut, QR khong bi de."""
from __future__ import annotations

import itertools

import pygame
import pytest

from core import font_manager as fm
from core.settings import GameSettings
from game import i18n

DT = 1.0 / 60.0


@pytest.fixture
def game(isolated_user_data, monkeypatch):
    import vision.camera as cam
    monkeypatch.setattr(cam, "scan_available_cameras", lambda *a, **k: [])
    from game.game import Game
    g = Game(settings=GameSettings(), use_camera=False)
    from game.game import GameState
    g.screens[GameState.PRIVACY_NOTICE]._accept()
    yield g
    g.shutdown()


def _assert_no_overlap(screen, name: str) -> None:
    widgets = [w for w in screen.widgets
               if w.focusable and w.visible]
    for a, b in itertools.combinations(widgets, 2):
        assert not a.rect.colliderect(b.rect), \
            f"{name}: overlap {a.rect} vs {b.rect}"


def _assert_labels_fit(screen, name: str) -> None:
    from game.widgets import Button
    font = fm.get("button")
    for w in screen.widgets:
        if isinstance(w, Button) and w.visible:
            tw = font.size(fm.nfc(w.label))[0]
            assert tw <= w.rect.width - 8, \
                f"{name}: '{w.label}' rong {tw} > nut {w.rect.width}"


@pytest.mark.parametrize("lang", ["vi", "en"])
def test_main_menu_layout(game, lang):
    from game.game import GameState
    i18n.set_language(lang)
    game.rebuild_screens()
    screen = game.screens[GameState.MAIN_MENU]
    _assert_no_overlap(screen, f"main_menu[{lang}]")
    _assert_labels_fit(screen, f"main_menu[{lang}]")


@pytest.mark.parametrize("lang", ["vi", "en"])
def test_character_select_layout(game, lang):
    from game.game import GameState
    i18n.set_language(lang)
    game.change_state(GameState.CHARACTER_SELECT)
    screen = game.screens[GameState.CHARACTER_SELECT]
    _assert_no_overlap(screen, f"char_select[{lang}]")
    _assert_labels_fit(screen, f"char_select[{lang}]")


@pytest.mark.parametrize("lang", ["vi", "en"])
def test_settings_all_tabs_layout(game, lang):
    from game.game import GameState
    i18n.set_language(lang)
    game.change_state(GameState.SETTINGS)
    screen = game.screens[GameState.SETTINGS]
    for tab in range(5):
        screen._on_tab(tab)
        _assert_no_overlap(screen, f"settings[{lang}] tab{tab}")
        _assert_labels_fit(screen, f"settings[{lang}] tab{tab}")
        for _ in range(3):
            game._update(DT)
            game._draw()


def test_game_over_layout(game):
    from game.game import GameState
    game.request_play()
    game._on_death()
    screen = game.screens[GameState.GAME_OVER]
    _assert_no_overlap(screen, "game_over")
    _assert_labels_fit(screen, "game_over")


def test_qr_not_covered_by_widgets(game):
    """Vung anh QR (nua trai) khong bi button nao de len."""
    from game.game import GameState
    game.change_state(GameState.DONATE)
    screen = game.screens[GameState.DONATE]
    if not screen._has_qr:
        pytest.skip("Khong co anh QR trong moi truong test")
    qr = screen._qr_scaled
    qw, qh = qr.get_size()
    panel = pygame.Rect(0, 0, qw + 28, qh + 28)
    panel.center = (270, 380)
    for w in screen.widgets:
        assert not w.rect.colliderect(panel), \
            f"Widget {w.rect} de len vung QR {panel}"
