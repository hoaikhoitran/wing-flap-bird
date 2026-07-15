"""Test asset art: manifest, file bat buoc, PNG load, sprite sheet dims."""
from __future__ import annotations

from pathlib import Path

import pygame

from core.paths import resource_path
from game.characters import CHARACTER_IDS, SPRITE_FRAME_H, SPRITE_FRAME_W

REQUIRED = [
    "assets/art/backgrounds/sky.png",
    "assets/art/backgrounds/clouds_far.png",
    "assets/art/backgrounds/mountains_far.png",
    "assets/art/backgrounds/clouds_mid.png",
    "assets/art/backgrounds/kites_mid.png",
    "assets/art/backgrounds/village_mid.png",
    "assets/art/backgrounds/foliage_near.png",
    "assets/art/backgrounds/ground_near.png",
    "assets/art/obstacles/bamboo_gate_top.png",
    "assets/art/obstacles/bamboo_gate_bottom.png",
    "assets/art/obstacles/gate_cap.png",
    "assets/art/obstacles/gate_shadow.png",
    "assets/art/obstacles/ribbon_red.png",
    "assets/art/obstacles/ribbon_yellow.png",
    "assets/art/effects/feather.png",
    "assets/art/effects/wind_streak.png",
    "assets/art/effects/sparkle.png",
    "assets/art/effects/flap_ring.png",
    "assets/art/effects/contact_shadow.png",
    "assets/art/ui/panel.png",
    "assets/art/ui/button.png",
    "assets/art/ui/button_pressed.png",
    "assets/art/ui/logo_mark.png",
    "assets/art/ui/icons.png",
]
REQUIRED += [f"assets/art/characters/{c}/{s}.png"
             for c in CHARACTER_IDS for s in ("idle", "flap", "hurt")]

AUDIO_REQUIRED = [f"assets/audio/{n}.wav" for n in (
    "flap_1", "flap_2", "flap_3", "score", "collision", "game_over",
    "menu_move", "menu_confirm", "calibration_complete")]


def test_asset_manifest_exists_with_license():
    manifest = resource_path("assets/ASSET_MANIFEST.md")
    assert manifest.exists()
    text = manifest.read_text(encoding="utf-8")
    assert "MIT" in text
    assert "generate_game_assets.py" in text


def test_required_assets_exist_nonzero():
    for rel in REQUIRED + AUDIO_REQUIRED:
        path = resource_path(rel)
        assert path.exists(), f"Thieu {rel}"
        assert path.stat().st_size > 0, f"File 0 byte: {rel}"


def test_all_art_pngs_load():
    pygame.init()
    art_root = Path(resource_path("assets/art"))
    pngs = list(art_root.rglob("*.png"))
    assert len(pngs) >= 39
    for png in pngs:
        surf = pygame.image.load(str(png))
        assert surf.get_width() > 0 and surf.get_height() > 0


def test_character_sprite_sheet_dimensions():
    pygame.init()
    expected_frames = {"idle": 4, "flap": 4, "hurt": 2}
    for char in CHARACTER_IDS:
        for state, count in expected_frames.items():
            path = resource_path(f"assets/art/characters/{char}/{state}.png")
            surf = pygame.image.load(str(path))
            assert surf.get_width() == SPRITE_FRAME_W * count, \
                f"{char}/{state}: rong {surf.get_width()}"
            assert surf.get_height() == SPRITE_FRAME_H


def test_qr_still_loads_without_decoding():
    """QR ung ho van load duoc (KHONG decode/scan theo yeu cau)."""
    pygame.init()
    surf = pygame.image.load(
        str(resource_path("assets/support/vietqr-support.png")))
    assert surf.get_width() > 300 and surf.get_height() > 300
