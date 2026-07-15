"""Test 5 nhan vat: id, fallback, cong bang gameplay, persistence."""
from __future__ import annotations

import pygame

import config
from core.settings import VALID_CHARACTERS, GameSettings
from game.characters import (CHARACTER_IDS, CHARACTERS, DEFAULT_CHARACTER,
                             get_character, load_animator)


def test_exactly_five_characters():
    assert len(CHARACTER_IDS) == 5
    assert set(CHARACTER_IDS) == {"swallow", "duck", "stork", "owl",
                                  "sparrow"}
    assert set(VALID_CHARACTERS) == set(CHARACTER_IDS)


def test_default_is_swallow():
    assert DEFAULT_CHARACTER == "swallow"
    assert GameSettings().selected_character == "swallow"


def test_invalid_id_falls_back_to_swallow():
    assert get_character("dragon").id == "swallow"
    assert get_character("").id == "swallow"


def test_invalid_setting_falls_back(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"selected_character": "phoenix"}', encoding="utf-8")
    settings = GameSettings.load(path)
    assert settings.selected_character == "swallow"


def test_each_character_has_idle_flap_hurt():
    pygame.init()
    for char_id in CHARACTER_IDS:
        anim = load_animator(char_id)
        assert set(anim.clips.keys()) == {"idle", "flap", "hurt"}
        assert len(anim.clips["idle"].frames) == 4
        assert len(anim.clips["flap"].frames) == 4
        assert len(anim.clips["hurt"].frames) == 2


def test_all_characters_same_hitbox_and_physics():
    """CONG BANG: cung hitbox + cung physics config cho moi nhan vat."""
    pygame.init()
    pygame.display.set_mode((100, 100))
    from game.player import Player
    players = [Player(100, 100, character_id=c) for c in CHARACTER_IDS]
    radii = {p.radius for p in players}
    assert radii == {config.PLAYER_RADIUS}
    diffs = {(p.diff.gravity, p.diff.flap_force, p.diff.max_fall_speed)
             for p in players}
    assert len(diffs) == 1  # cung gravity/flap/toc do roi
    # Flap cho ket qua van toc giong het nhau
    for p in players:
        p.flap()
    assert {p.vel_y for p in players} == {players[0].diff.flap_force}


def test_selection_persists(tmp_path):
    path = tmp_path / "settings.json"
    settings = GameSettings()
    settings.selected_character = "owl"
    settings.save(path)
    assert GameSettings.load(path).selected_character == "owl"


def test_no_character_locked_or_paid():
    """Khong co truong lock/price/donate trong dinh nghia nhan vat."""
    for spec in CHARACTERS.values():
        assert not hasattr(spec, "locked")
        assert not hasattr(spec, "price")
        assert not hasattr(spec, "requires_donation")
