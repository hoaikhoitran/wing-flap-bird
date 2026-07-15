"""Test man hinh chon nhan vat (headless, khong camera)."""
from __future__ import annotations

import pytest

from core.settings import GameSettings

DT = 1.0 / 60.0


@pytest.fixture
def game(isolated_user_data, monkeypatch):
    import vision.camera as cam
    monkeypatch.setattr(cam, "scan_available_cameras", lambda *a, **k: [])
    from game.game import Game
    g = Game(settings=GameSettings(), use_camera=False)
    g.screens[list(g.screens.keys())[0]]  # noqa - warm
    yield g
    g.shutdown()


def _accept_privacy(game):
    from game.game import GameState
    game.screens[GameState.PRIVACY_NOTICE]._accept()


def test_menu_has_characters_entry_and_opens(game):
    from game.game import GameState
    _accept_privacy(game)
    game.open_character_select()
    assert game.state is GameState.CHARACTER_SELECT
    for _ in range(10):
        game._update(DT)
        game._draw()


def test_pick_and_confirm_changes_character(game, isolated_user_data):
    from game.game import GameState
    _accept_privacy(game)
    game.open_character_select()
    screen = game.screens[GameState.CHARACTER_SELECT]
    screen._pick("owl")
    screen._confirm()
    assert game.settings.selected_character == "owl"
    assert game.player.character.id == "owl"
    # Persistence: settings da luu
    assert GameSettings.load().selected_character == "owl"
    # Ap dung ngay cho luot choi tiep theo
    game.request_play()
    assert game.player.character.id == "owl"


def test_back_returns_to_origin(game):
    from game.game import GameState
    _accept_privacy(game)
    game.open_character_select()
    screen = game.screens[GameState.CHARACTER_SELECT]
    screen._back()
    assert game.state is GameState.MAIN_MENU
    # Tu game over -> quay ve game over
    game.request_play()
    game._on_death()
    game.open_character_select(from_game_over=True)
    screen._back()
    assert game.state is GameState.GAME_OVER


def test_five_cards_and_focus_order(game):
    from game.game import GameState
    _accept_privacy(game)
    game.open_character_select()
    screen = game.screens[GameState.CHARACTER_SELECT]
    assert len(screen._cards) == 5
    focusables = screen._focusables()
    assert len(focusables) == 7  # 5 card + CHON + QUAY LAI
    # Focus di chuyen duoc het danh sach, khong trung lap
    seen = []
    for _ in range(len(focusables)):
        screen._move_focus(1)
        focused = screen._focused_widget()
        assert focused is not None
        seen.append(id(focused))
    assert len(set(seen)) == len(focusables)
