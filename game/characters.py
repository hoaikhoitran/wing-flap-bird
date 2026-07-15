"""Dinh nghia 5 nhan vat co the chon - du lieu tap trung.

CONG BANG GAMEPLAY: moi nhan vat dung CUNG hitbox (config.PLAYER_RADIUS),
cung gravity/flap force/toc do (DifficultyConfig). Khac nhau CHI o hinh
dang, mau sac, animation va particle style. Khong khoa, khong yeu cau
donate, khong nhan vat nao co loi the.
"""
from __future__ import annotations

from dataclasses import dataclass

from game.animation import AnimationClip, Animator
from game.assets import assets

SPRITE_FRAME_W = 96
SPRITE_FRAME_H = 80


@dataclass(frozen=True)
class CharacterDefinition:
    id: str
    name_key: str
    description_key: str
    sprite_dir: str                  # assets/art/characters/<id>
    preview_offset: tuple[int, int] = (0, 0)
    particle_style: str = "feather"  # feather | ripple | leaf


CHARACTERS: dict[str, CharacterDefinition] = {
    "swallow": CharacterDefinition(
        id="swallow", name_key="char.swallow.name",
        description_key="char.swallow.desc",
        sprite_dir="assets/art/characters/swallow",
        particle_style="feather"),
    "duck": CharacterDefinition(
        id="duck", name_key="char.duck.name",
        description_key="char.duck.desc",
        sprite_dir="assets/art/characters/duck",
        particle_style="ripple"),
    "stork": CharacterDefinition(
        id="stork", name_key="char.stork.name",
        description_key="char.stork.desc",
        sprite_dir="assets/art/characters/stork",
        particle_style="feather"),
    "owl": CharacterDefinition(
        id="owl", name_key="char.owl.name",
        description_key="char.owl.desc",
        sprite_dir="assets/art/characters/owl",
        particle_style="leaf"),
    "sparrow": CharacterDefinition(
        id="sparrow", name_key="char.sparrow.name",
        description_key="char.sparrow.desc",
        sprite_dir="assets/art/characters/sparrow",
        particle_style="feather"),
}

CHARACTER_IDS: tuple[str, ...] = tuple(CHARACTERS.keys())
DEFAULT_CHARACTER = "swallow"


def get_character(char_id: str) -> CharacterDefinition:
    """Lay dinh nghia nhan vat; id sai -> fallback swallow."""
    return CHARACTERS.get(char_id, CHARACTERS[DEFAULT_CHARACTER])


def load_animator(char_id: str) -> Animator:
    """Tao Animator voi idle/flap/hurt tu sprite strip cua nhan vat.

    - idle : 4 frame loop (0.16s/frame)
    - flap : 4 frame KHONG loop (0.055s/frame) -> tu ve idle
    - hurt : 2 frame KHONG loop (0.12s/frame), giu frame cuoi
    """
    spec = get_character(char_id)

    def clip(state: str, frame_time: float, loop: bool) -> AnimationClip:
        frames = assets.strip(f"{spec.sprite_dir}/{state}.png",
                              SPRITE_FRAME_W)
        return AnimationClip(frames=frames, frame_time=frame_time, loop=loop)

    return Animator(
        clips={
            "idle": clip("idle", 0.16, True),
            "flap": clip("flap", 0.055, False),
            "hurt": clip("hurt", 0.12, False),
        },
        state="idle",
        fallback={"flap": "idle"},
    )
