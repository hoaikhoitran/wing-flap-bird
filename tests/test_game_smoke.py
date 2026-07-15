"""Smoke test headless: khoi tao game khong camera, di qua toan bo flow
menu -> play -> game over -> restart, va do cac tieu chi gameplay.
"""
from __future__ import annotations

import pytest

import config
from core.settings import GameSettings

DT = 1.0 / 60.0


@pytest.fixture
def game(isolated_user_data, monkeypatch):
    # Khong quet camera that trong test
    import vision.camera as cam
    monkeypatch.setattr(cam, "scan_available_cameras", lambda *a, **k: [])

    from game.game import Game
    g = Game(settings=GameSettings(), use_camera=False)
    yield g
    g.shutdown()


def _step(g, frames: int) -> None:
    for _ in range(frames):
        g._update(DT)
        g._draw()


def test_boot_shows_privacy_notice_first_run(game):
    from game.game import GameState
    assert game.state is GameState.PRIVACY_NOTICE
    # Bam "TOI DA HIEU" -> vao menu + luu privacy version
    game.screens[GameState.PRIVACY_NOTICE]._accept()
    assert game.state is GameState.MAIN_MENU
    assert game.settings.privacy_accepted_version >= 1


def test_menu_screens_render_without_camera(game):
    from game.game import GameState
    game.screens[GameState.PRIVACY_NOTICE]._accept()
    for state in (GameState.MAIN_MENU, GameState.SETTINGS,
                  GameState.HOW_TO_PLAY, GameState.CREDITS,
                  GameState.DONATE):
        game.change_state(state)
        _step(game, 5)
    game.change_state(GameState.MAIN_MENU)
    assert game.vision is None  # menu KHONG mo camera


def test_play_flow_and_gameplay_criteria(game):
    from game.game import GameState
    game.screens[GameState.PRIVACY_NOTICE]._accept()

    # PLAY (khong camera) -> vao thang GET_READY, chua co trong luc
    game.request_play()
    assert game.state is GameState.GET_READY
    assert len(game.obstacles.pipes) == 0

    frames = 0
    while game.state is GameState.GET_READY and frames < 300:
        _step(game, 1)
        frames += 1
    assert game.state is GameState.PLAYING
    assert game.player.vel_y == 0.0

    # Mot lan vo bay len 70-120 px (do sau grace)
    game._grace_timer = 0.0
    game.player.y = 400.0
    game.player.vel_y = 0.0
    game._do_flap()
    min_y = game.player.y
    for _ in range(120):
        game.player.update(DT)
        min_y = min(min_y, game.player.y)
        if game.player.vel_y >= 0:
            break
    rise = 400.0 - min_y
    assert 70.0 <= rise <= 120.0, f"rise={rise:.1f}px"

    # Roi tu do tu giua man hinh >= 1.5s
    game._start_game()
    frames = 0
    while game.state is GameState.GET_READY and frames < 300:
        _step(game, 1); frames += 1
    fall_frames = 0
    while game.state is GameState.PLAYING and fall_frames < 600:
        _step(game, 1); fall_frames += 1
    assert game.state is GameState.GAME_OVER
    assert fall_frames * DT >= 1.5

    # Restart: khong giu van toc / diem / cot cu
    game._start_game()
    assert game.state is GameState.GET_READY
    assert game.player.vel_y == 0.0
    assert game.player.angle == 0.0
    assert game.score == 0
    assert len(game.obstacles.pipes) == 0


def test_pause_freezes_gameplay(game):
    from game.game import GameState
    game.screens[GameState.PRIVACY_NOTICE]._accept()
    game.request_play()
    while game.state is GameState.GET_READY:
        _step(game, 1)
    _step(game, 30)
    y_before = game.player.y
    game.pause()
    assert game.state is GameState.PAUSED
    _step(game, 60)  # 1 giay pause
    assert game.player.y == y_before  # physics dung han
    game.resume_from_pause()
    assert game.state is GameState.PLAYING


def test_difficulty_change_applies_next_run(game):
    from game.game import GameState
    game.screens[GameState.PRIVACY_NOTICE]._accept()
    game.settings.difficulty = "normal"
    game.request_play()
    assert game.diff.name == "normal"
    assert game.player.diff.gravity == 1300.0


def test_high_score_saved_on_death(game, isolated_user_data):
    from core import storage
    from game.game import GameState
    game.screens[GameState.PRIVACY_NOTICE]._accept()
    game.request_play()
    game.score = 5
    game._on_death()
    assert game.state is GameState.GAME_OVER
    assert storage.load_high_score() == 5


def test_back_to_menu_resets_session(game):
    from game.game import GameState
    game.screens[GameState.PRIVACY_NOTICE]._accept()
    game.request_play()
    game.back_to_menu()
    assert game.state is GameState.MAIN_MENU
    assert game.vision is None
