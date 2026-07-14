"""He thong particle don gian: bui khi vo canh, manh vo khi va cham."""
from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

import config


@dataclass
class _Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: tuple[int, int, int]
    gravity: float


class ParticleSystem:
    """Quan ly toan bo particle; gioi han so luong de giu FPS."""

    def __init__(self) -> None:
        self._particles: list[_Particle] = []

    def clear(self) -> None:
        self._particles.clear()

    def emit_flap(self, x: float, y: float) -> None:
        """Bui nho toa ra phia sau-duoi khi vo canh."""
        for _ in range(10):
            angle_vx = random.uniform(-160, -40)
            angle_vy = random.uniform(40, 160)
            color = random.choice([(255, 235, 160), (255, 210, 110),
                                   (255, 255, 255)])
            self._add(_Particle(
                x=x + random.uniform(-6, 6), y=y + random.uniform(-4, 10),
                vx=angle_vx, vy=angle_vy,
                life=0.45, max_life=0.45,
                size=random.uniform(3, 6), color=color, gravity=300.0,
            ))

    def emit_burst(self, x: float, y: float) -> None:
        """No manh khi va cham."""
        for _ in range(26):
            self._add(_Particle(
                x=x, y=y,
                vx=random.uniform(-320, 320), vy=random.uniform(-380, 120),
                life=0.7, max_life=0.7,
                size=random.uniform(3, 8),
                color=random.choice([(255, 205, 60), (255, 120, 40),
                                     (255, 255, 255), (230, 80, 60)]),
                gravity=800.0,
            ))

    def emit_score(self, x: float, y: float) -> None:
        """Lap lanh nho khi ghi diem."""
        for _ in range(8):
            self._add(_Particle(
                x=x, y=y,
                vx=random.uniform(-90, 90), vy=random.uniform(-160, -40),
                life=0.5, max_life=0.5,
                size=random.uniform(2, 4),
                color=(255, 250, 170), gravity=150.0,
            ))

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
            alive.append(p)
        self._particles = alive

    def draw(self, surface: pygame.Surface) -> None:
        for p in self._particles:
            # Nho dan + mo dan theo thoi gian song con lai
            k = p.life / p.max_life
            size = max(1, int(p.size * k))
            pygame.draw.circle(surface, p.color,
                               (int(p.x), int(p.y)), size)
