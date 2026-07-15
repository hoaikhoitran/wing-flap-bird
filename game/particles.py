"""He thong particle dung sprite asset (feather / wind streak / sparkle).

Gioi han MAX_PARTICLES (pooling don gian bang cat bot) - khong tao
Surface moi trong game loop (sprite lay tu AssetManager cache; chi
rotozoom cac particle dang song, so luong nho).
"""
from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

import config
from game.assets import assets

_FEATHER = "assets/art/effects/feather.png"
_STREAK = "assets/art/effects/wind_streak.png"
_SPARKLE = "assets/art/effects/sparkle.png"


@dataclass
class _Particle:
    kind: str            # feather | streak | sparkle | dot
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    gravity: float
    rot: float = 0.0
    spin: float = 0.0
    scale: float = 1.0
    color: tuple[int, int, int] = (255, 255, 255)
    size: float = 4.0


class ParticleSystem:
    def __init__(self) -> None:
        self._particles: list[_Particle] = []

    def clear(self) -> None:
        self._particles.clear()

    # ------------------------------------------------------------------
    def emit_flap(self, x: float, y: float) -> None:
        """2-5 feather roi + wind streak tao vet gio cong phia sau."""
        for _ in range(random.randint(2, 4)):
            self._add(_Particle(
                kind="feather", x=x + random.uniform(-8, 6),
                y=y + random.uniform(-4, 10),
                vx=random.uniform(-140, -60), vy=random.uniform(30, 110),
                life=0.55, max_life=0.55, gravity=240.0,
                rot=random.uniform(0, 360), spin=random.uniform(-240, 240),
                scale=random.uniform(0.8, 1.15)))
        for i in range(3):
            self._add(_Particle(
                kind="streak", x=x - 12 - i * 10,
                y=y + random.uniform(-6, 10) + i * 4,
                vx=-220 - i * 40, vy=random.uniform(-16, 6),
                life=0.32, max_life=0.32, gravity=-60.0,
                scale=random.uniform(0.7, 1.1)))

    def emit_score(self, x: float, y: float) -> None:
        for _ in range(6):
            self._add(_Particle(
                kind="sparkle", x=x + random.uniform(-14, 14),
                y=y + random.uniform(-10, 10),
                vx=random.uniform(-70, 70), vy=random.uniform(-150, -50),
                life=0.5, max_life=0.5, gravity=140.0,
                rot=random.uniform(0, 90), spin=random.uniform(-180, 180),
                scale=random.uniform(0.7, 1.2)))

    def emit_burst(self, x: float, y: float) -> None:
        """Va cham: feather bung ra + vai dot mau."""
        for _ in range(10):
            self._add(_Particle(
                kind="feather", x=x, y=y,
                vx=random.uniform(-300, 300), vy=random.uniform(-340, 90),
                life=0.75, max_life=0.75, gravity=720.0,
                rot=random.uniform(0, 360), spin=random.uniform(-420, 420),
                scale=random.uniform(0.7, 1.2)))
        for _ in range(10):
            self._add(_Particle(
                kind="dot", x=x, y=y,
                vx=random.uniform(-260, 260), vy=random.uniform(-300, 80),
                life=0.55, max_life=0.55, gravity=760.0,
                color=random.choice([(255, 181, 71), (243, 91, 75),
                                     (255, 245, 220)]),
                size=random.uniform(3, 6)))

    # ------------------------------------------------------------------
    def _add(self, particle: _Particle) -> None:
        if len(self._particles) < config.MAX_PARTICLES:
            self._particles.append(particle)

    def update(self, dt: float) -> None:
        alive: list[_Particle] = []
        for p in self._particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.rot += p.spin * dt
            alive.append(p)
        self._particles = alive

    def draw(self, surface: pygame.Surface) -> None:
        for p in self._particles:
            k = p.life / p.max_life
            if p.kind == "dot":
                pygame.draw.circle(surface, p.color,
                                   (int(p.x), int(p.y)),
                                   max(1, int(p.size * k)))
                continue
            rel = {"feather": _FEATHER, "streak": _STREAK,
                   "sparkle": _SPARKLE}[p.kind]
            img = assets.image(rel)
            if p.kind == "streak":
                sprite = img  # streak khong xoay
            else:
                sprite = pygame.transform.rotozoom(img, p.rot, p.scale)
            sprite.set_alpha(int(255 * k))
            surface.blit(sprite,
                         sprite.get_rect(center=(int(p.x), int(p.y))))
