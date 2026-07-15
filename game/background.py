"""Background 2.5D nhieu lop parallax - WIND FESTIVAL SKY.

7 lop (xa -> gan): sky gradient, may xa, nui xa, may giua, dieu gio,
lang/doi, la foreground + mat dat. Moi lop co toc do rieng, wrap lien
mach (tile 1000px = be rong cua so, blit 2 ban sao), KHONG allocate
surface moi trong game loop (moi anh load/cache 1 lan qua AssetManager).

Chia 2 tang ve:
  draw_back(surface)  : sau nhan vat/obstacle (troi -> lang)
  draw_front(surface) : truoc obstacle (la gan + mat dat) -> chieu sau
"""
from __future__ import annotations

import math

import pygame

import config
from game.assets import assets

_ART = "assets/art/backgrounds"
_W = config.WINDOW_WIDTH
_GROUND_TOP = config.WINDOW_HEIGHT - config.GROUND_HEIGHT


class _Layer:
    def __init__(self, rel: str, y: int, speed: float,
                 ambient: float = 0.0) -> None:
        self.rel = f"{_ART}/{rel}"
        self.y = y
        self.speed = speed      # he so nhan voi toc do cuon gameplay
        self.ambient = ambient  # px/s troi nhe ke ca khi dung (may)
        self.offset = 0.0

    def update(self, dt: float, scroll_speed: float) -> None:
        self.offset = (self.offset
                       + (scroll_speed * self.speed + self.ambient) * dt) % _W

    def draw(self, surface: pygame.Surface, dy: float = 0.0) -> None:
        img = assets.image(self.rel)
        x = -int(self.offset)
        y = int(self.y + dy)
        surface.blit(img, (x, y))
        surface.blit(img, (x + _W, y))


class Background:
    """Quan ly toan bo layer parallax + hieu ung dieu bay nhap nho."""

    def __init__(self) -> None:
        self._time = 0.0
        # Atmospheric perspective: cang xa toc do & tuong phan cang thap
        self.clouds_far = _Layer("clouds_far.png", 30, 0.05, ambient=4.0)
        self.mountains = _Layer("mountains_far.png", _GROUND_TOP - 250, 0.10)
        self.clouds_mid = _Layer("clouds_mid.png", 90, 0.18, ambient=7.0)
        self.kites = _Layer("kites_mid.png", 40, 0.24, ambient=2.0)
        self.village = _Layer("village_mid.png", _GROUND_TOP - 228, 0.32)
        self.foliage = _Layer("foliage_near.png", _GROUND_TOP - 118, 0.72)
        self.ground = _Layer("ground_near.png", _GROUND_TOP, 1.0)
        self._back = [self.clouds_far, self.mountains, self.clouds_mid,
                      self.kites, self.village]
        self._front = [self.foliage, self.ground]

    def update(self, dt: float, scrolling: bool,
               scroll_speed: float = 150.0) -> None:
        self._time += dt
        speed = scroll_speed if scrolling else 0.0
        for layer in self._back + self._front:
            layer.update(dt, speed)

    # ------------------------------------------------------------------
    def draw_back(self, surface: pygame.Surface) -> None:
        surface.blit(assets.image(f"{_ART}/sky.png"), (0, 0))
        self.clouds_far.draw(surface)
        self.mountains.draw(surface)
        self.clouds_mid.draw(surface)
        # Dieu gio nhap nho nhe theo thoi gian (khong allocate)
        self.kites.draw(surface, dy=math.sin(self._time * 0.9) * 6.0)
        self.village.draw(surface)

    def draw_front(self, surface: pygame.Surface) -> None:
        self.foliage.draw(surface)
        self.ground.draw(surface)
