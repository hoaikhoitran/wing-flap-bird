"""Nhan vat: vat ly delta-time + sprite animation (idle/flap/hurt).

CONG BANG: moi nhan vat dung CUNG hitbox PLAYER_RADIUS va cung
DifficultyConfig - chi khac hinh anh/animation (xem game/characters.py).

Game feel (skill game-feel):
  - Flap: doi animation NGAY, squash ngang + stretch doc nhe, tra ve
    scale 1 bang easing (transient, khong thanh trang thai moi).
  - Hurt: chuyen hurt animation, KHONG doi physics body.
  - Contact shadow rieng (draw_shadow) thay doi theo do cao.
"""
from __future__ import annotations

import math

import pygame

import config
from game.assets import assets
from game.characters import get_character, load_animator

_FLAP_RING = "assets/art/effects/flap_ring.png"
_CONTACT_SHADOW = "assets/art/effects/contact_shadow.png"


class Player:
    """Chim chiu trong luc; moi flap DAT van toc Y = flap_force."""

    def __init__(self, x: float, y: float,
                 diff: config.DifficultyConfig | None = None,
                 character_id: str = "swallow") -> None:
        self.x = x
        self.y = y
        self.vel_y = 0.0
        self.angle = 0.0
        self.radius = config.PLAYER_RADIUS  # hitbox CO DINH cho moi nhan vat
        self.diff = diff or config.EASY
        self.character = get_character(character_id)
        self.animator = load_animator(self.character.id)
        self._time = 0.0
        self.flap_effect_timer = 0.0
        # Squash & stretch (CHI visual, khong dung hitbox)
        self._scale_x = 1.0
        self._scale_y = 1.0

    # ------------------------------------------------------------------
    def set_difficulty(self, diff: config.DifficultyConfig) -> None:
        self.diff = diff

    def set_character(self, character_id: str) -> None:
        """Doi nhan vat (hitbox/physics giu nguyen)."""
        if character_id != self.character.id:
            self.character = get_character(character_id)
            self.animator = load_animator(self.character.id)

    def reset(self, y: float) -> None:
        self.y = y
        self.vel_y = 0.0
        self.angle = 0.0
        self.flap_effect_timer = 0.0
        self._scale_x = self._scale_y = 1.0
        self.animator.play("idle", restart=True)

    # ------------------------------------------------------------------
    def flap(self) -> None:
        self.vel_y = self.diff.flap_force
        self.angle = 28.0
        self.animator.play("flap", restart=True)  # dap canh NGAY lap tuc
        self.flap_effect_timer = config.FLAP_PULSE_DURATION
        self._scale_x = 0.92   # squash ngang nhe
        self._scale_y = 1.10   # stretch theo chieu bay

    def hurt(self) -> None:
        self.animator.play("hurt")

    # ------------------------------------------------------------------
    def update(self, dt: float, gravity_scale: float = 1.0) -> None:
        self._time += dt
        self.vel_y += self.diff.gravity * gravity_scale * dt
        self.vel_y = min(self.vel_y, self.diff.max_fall_speed)
        self.y += self.vel_y * dt

        self.animator.update(dt)
        if self.flap_effect_timer > 0.0:
            self.flap_effect_timer = max(0.0, self.flap_effect_timer - dt)
        # Tra scale ve 1 bang ease-out
        ease = min(1.0, 9.0 * dt)
        self._scale_x += (1.0 - self._scale_x) * ease
        self._scale_y += (1.0 - self._scale_y) * ease

        target_angle = max(-70.0, min(30.0, -self.vel_y * 0.3))
        self.angle += (target_angle - self.angle) * min(1.0, 9.0 * dt)

    def idle_bob(self, dt: float) -> None:
        """Bay idle nhe o menu / GET_READY (khong trong luc)."""
        self._time += dt
        self.animator.play("idle")
        self.animator.update(dt)
        self.y += math.sin(self._time * 3.0) * 12.0 * dt
        self.angle = math.sin(self._time * 2.0) * 6.0
        self.vel_y = 0.0
        ease = min(1.0, 9.0 * dt)
        self._scale_x += (1.0 - self._scale_x) * ease
        self._scale_y += (1.0 - self._scale_y) * ease

    # ------------------------------------------------------------------
    def draw_shadow(self, surface: pygame.Surface, ground_y: float) -> None:
        """Contact shadow duoi nhan vat - nho/mo dan khi bay cao."""
        height = max(0.0, ground_y - self.y)
        k = max(0.25, 1.0 - height / 520.0)
        w = max(24, int(96 * k) // 4 * 4)   # luong tu hoa de cache scale
        h = max(8, int(26 * k) // 2 * 2)
        shadow = assets.scaled(_CONTACT_SHADOW, (w, h))
        shadow.set_alpha(int(150 * k))
        surface.blit(shadow, shadow.get_rect(
            center=(int(self.x), int(ground_y - h // 2 - 2))))

    def draw(self, surface: pygame.Surface) -> None:
        """Ve pulse ring (neu co) + sprite frame hien tai da xoay/scale."""
        self._draw_pulse(surface)

        frame = self.animator.frame
        fw, fh = frame.get_size()
        # Squash & stretch quanh scale hien thi chuan
        base_scale = config.PLAYER_HEIGHT / 42.0  # giu ti le thiet ke
        w = int(fw * 0.72 * base_scale * self._scale_x)
        h = int(fh * 0.72 * base_scale * self._scale_y)
        sprite = pygame.transform.smoothscale(frame, (max(2, w), max(2, h)))
        rotated = pygame.transform.rotozoom(sprite, self.angle, 1.0)
        surface.blit(rotated,
                     rotated.get_rect(center=(int(self.x), int(self.y))))

    def _draw_pulse(self, surface: pygame.Surface) -> None:
        if self.flap_effect_timer <= 0.0:
            return
        k = 1.0 - self.flap_effect_timer / config.FLAP_PULSE_DURATION
        d = (int(46 + 66 * k) // 4) * 4   # luong tu hoa de cache
        ring = assets.scaled(_FLAP_RING, (d, d))
        ring.set_alpha(int(210 * (1.0 - k)))
        surface.blit(ring, ring.get_rect(center=(int(self.x), int(self.y))))
