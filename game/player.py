"""Nhan vat chim: vat ly (he delta-time), animation vo canh, nghieng theo van toc.

Sprite ve o kich thuoc PLAYER_WIDTH x PLAYER_HEIGHT (config), co vien dam
de noi bat tren nen troi. Hitbox tron PLAYER_RADIUS NHO hon sprite ~18%.
"""
from __future__ import annotations

import math

import pygame

import config

# Mau sac nhan vat - tuong phan manh voi nen troi xanh nhat
_OUTLINE = (60, 40, 10)
_BODY = (255, 210, 40)
_BODY_DARK = (225, 160, 20)
_BELLY = (255, 245, 205)
_WING = (255, 140, 30)
_BEAK = (255, 110, 30)
_EYE_WHITE = (255, 255, 255)
_EYE_BLACK = (25, 25, 25)
_PULSE = (255, 255, 255)

# Kich thuoc "ban ve" goc; sprite se duoc scale ve PLAYER_WIDTH x HEIGHT
_ART_W, _ART_H = 76, 56


class Player:
    """Chim chiu trong luc; moi flap DAT van toc Y = flap_force (khong cong don).

    Thong so vat ly lay tu DifficultyConfig (doi duoc trong runtime),
    khong dung bien global co dinh.
    """

    def __init__(self, x: float, y: float,
                 diff: config.DifficultyConfig | None = None) -> None:
        self.x = x
        self.y = y
        self.vel_y = 0.0
        self.angle = 0.0          # Goc nghieng (do; duong = ngua len, theo pygame CCW)
        self.radius = config.PLAYER_RADIUS
        self.diff = diff or config.EASY
        self._time = 0.0
        self._flap_anim = 0.0     # >0: dang chay animation dap canh
        self.flap_effect_timer = 0.0  # >0: dang hien vong pulse quanh chim

    def set_difficulty(self, diff: config.DifficultyConfig) -> None:
        self.diff = diff

    def reset(self, y: float) -> None:
        """Reset day du khi bat dau / choi lai: vi tri, van toc, goc, hieu ung."""
        self.y = y
        self.vel_y = 0.0
        self.angle = 0.0
        self._flap_anim = 0.0
        self.flap_effect_timer = 0.0

    def flap(self) -> None:
        """Nhan luc day len - goi khi detector (hoac SPACE) phat su kien flap.

        DAT van toc = FLAP_FORCE thay vi cong don, de van toc roi hien tai
        khong lam giam hieu qua cua luc bay.
        """
        self.vel_y = self.diff.flap_force
        self.angle = 28.0            # nghieng len NGAY lap tuc cho phan hoi ro
        self._flap_anim = 0.32       # doi frame animation canh ngay
        self.flap_effect_timer = config.FLAP_PULSE_DURATION

    def update(self, dt: float, gravity_scale: float = 1.0) -> None:
        """Vat ly moi frame. gravity_scale < 1 dung cho grace period sau GO."""
        self._time += dt
        self.vel_y += self.diff.gravity * gravity_scale * dt
        # Chi gioi han van toc ROI, khong gioi han van toc bay len
        self.vel_y = min(self.vel_y, self.diff.max_fall_speed)
        self.y += self.vel_y * dt

        if self._flap_anim > 0.0:
            self._flap_anim = max(0.0, self._flap_anim - dt)
        if self.flap_effect_timer > 0.0:
            self.flap_effect_timer = max(0.0, self.flap_effect_timer - dt)

        # Khi roi: chui mui xuong dan (muot); khi vua flap goc da duoc dat ngay
        target_angle = max(-70.0, min(30.0, -self.vel_y * 0.3))
        self.angle += (target_angle - self.angle) * min(1.0, 9.0 * dt)

    def idle_bob(self, dt: float) -> None:
        """Chuyen dong nhap nho nhe o menu / man hinh GET_READY (khong trong luc)."""
        self._time += dt
        self.y += math.sin(self._time * 3.0) * 12.0 * dt
        self.angle = math.sin(self._time * 2.0) * 6.0
        self.vel_y = 0.0

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        """Ve vong pulse (neu co) roi ve chim da xoay theo goc nghieng."""
        self._draw_pulse(surface)

        art = pygame.Surface((_ART_W, _ART_H), pygame.SRCALPHA)

        # Goc vo canh: dap manh sau khi flap, ve nhe khi bay binh thuong
        if self._flap_anim > 0.0:
            phase = 1.0 - self._flap_anim / 0.32
            wing_off = -16.0 * math.sin(phase * math.pi)
        else:
            wing_off = 3.0 * math.sin(self._time * 5.0)

        # Vien ngoai dam (silhouette to hon than 3px) de chim noi tren nen
        pygame.draw.ellipse(art, _OUTLINE, (5, 7, 58, 44))
        # Duoi
        pygame.draw.polygon(art, _OUTLINE, [(0, 20), (16, 26), (2, 36)])
        pygame.draw.polygon(art, _BODY_DARK, [(3, 22), (15, 26), (5, 33)])
        # Than
        pygame.draw.ellipse(art, _BODY, (8, 10, 52, 38))
        # Bung
        pygame.draw.ellipse(art, _BELLY, (16, 28, 34, 17))
        # Canh (tam giac dap len xuong quanh diem noi voi than)
        wing_tip_y = int(28 + wing_off)
        pygame.draw.polygon(art, _WING,
                            [(18, 25), (40, 21), (30, wing_tip_y)])
        pygame.draw.polygon(art, _OUTLINE,
                            [(18, 25), (40, 21), (30, wing_tip_y)], 2)
        # Mo (ve truoc mat de mat de len tren)
        pygame.draw.polygon(art, _OUTLINE, [(56, 20), (76, 27), (56, 34)])
        pygame.draw.polygon(art, _BEAK, [(58, 22), (73, 27), (58, 32)])
        # Mat to, ro
        pygame.draw.circle(art, _OUTLINE, (46, 20), 10)
        pygame.draw.circle(art, _EYE_WHITE, (46, 20), 8)
        pygame.draw.circle(art, _EYE_BLACK, (49, 20), 3)

        # Scale ve kich thuoc sprite cau hinh roi xoay
        sprite = pygame.transform.smoothscale(
            art, (config.PLAYER_WIDTH, config.PLAYER_HEIGHT))
        rotated = pygame.transform.rotozoom(sprite, self.angle, 1.0)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)

    def _draw_pulse(self, surface: pygame.Surface) -> None:
        """Vong tron pulse lan rong quanh chim ngay sau khi flap."""
        if self.flap_effect_timer <= 0.0:
            return
        k = 1.0 - self.flap_effect_timer / config.FLAP_PULSE_DURATION  # 0 -> 1
        radius = int(24 + 30 * k)
        alpha = int(200 * (1.0 - k))
        size = radius * 2 + 6
        ring = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*_PULSE, alpha),
                           (size // 2, size // 2), radius, 3)
        surface.blit(ring, ring.get_rect(center=(int(self.x), int(self.y))))
