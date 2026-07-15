"""Test animation theo elapsed time (khong theo frame count)."""
from __future__ import annotations

import pygame

from game.animation import AnimationClip, Animator


def _frames(n: int) -> list[pygame.Surface]:
    return [pygame.Surface((10, 10)) for _ in range(n)]


def _clip(n: int = 4, ft: float = 0.1, loop: bool = True) -> AnimationClip:
    return AnimationClip(frames=_frames(n), frame_time=ft, loop=loop)


def test_frame_advances_by_elapsed_time():
    clip = _clip(4, 0.1)
    assert clip.frames.index(clip.frame_at(0.00)) == 0
    assert clip.frames.index(clip.frame_at(0.15)) == 1
    assert clip.frames.index(clip.frame_at(0.35)) == 3
    assert clip.frames.index(clip.frame_at(0.45)) == 0  # loop


def test_30fps_and_60fps_equivalent():
    """Cung tong thoi gian -> cung frame, du dt khac nhau."""
    a30 = Animator(clips={"idle": _clip(4, 0.1)})
    a60 = Animator(clips={"idle": _clip(4, 0.1)})
    for _ in range(9):          # 9 x 1/30 = 0.3s
        a30.update(1 / 30)
    for _ in range(18):         # 18 x 1/60 = 0.3s
        a60.update(1 / 60)
    assert abs(a30.elapsed - a60.elapsed) < 1e-9
    assert a30.clips["idle"].frames.index(a30.frame) == \
        a60.clips["idle"].frames.index(a60.frame)


def test_loop_does_not_reset_each_frame():
    anim = Animator(clips={"idle": _clip(4, 0.1)})
    for _ in range(30):
        anim.play("idle")       # goi lai moi frame - KHONG duoc reset
        anim.update(1 / 60)
    assert anim.elapsed > 0.4   # da tich luy qua 1 vong loop


def test_flap_restarts_immediately_then_falls_back_to_idle():
    anim = Animator(
        clips={"idle": _clip(4, 0.1),
               "flap": _clip(4, 0.05, loop=False)},
        fallback={"flap": "idle"})
    anim.update(0.25)
    anim.play("flap", restart=True)
    assert anim.state == "flap" and anim.elapsed == 0.0
    # Flap giua chung -> restart ngay
    anim.update(0.08)
    anim.play("flap", restart=True)
    assert anim.elapsed == 0.0
    # Het clip -> tu ve idle
    for _ in range(30):
        anim.update(1 / 60)
    assert anim.state == "idle"


def test_hurt_holds_last_frame():
    clip = _clip(2, 0.1, loop=False)
    anim = Animator(clips={"idle": _clip(4), "hurt": clip})
    anim.play("hurt")
    anim.update(10.0)  # qua lau
    assert anim.state == "hurt"  # khong co fallback -> giu nguyen
    assert clip.frames.index(anim.frame) == 1  # frame cuoi


def test_hitbox_constant_across_animation():
    """Hitbox KHONG doi theo frame animation."""
    import config
    from game.player import Player
    pygame.init()
    pygame.display.set_mode((100, 100))
    player = Player(100, 100, character_id="duck")
    radius_before = player.radius
    player.flap()
    for _ in range(20):
        player.update(1 / 60)
    assert player.radius == radius_before == config.PLAYER_RADIUS
