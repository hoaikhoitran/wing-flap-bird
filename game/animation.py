"""Sprite animation theo ELAPSED TIME (khong theo frame count).

  - AnimationClip: danh sach frame + thoi luong moi frame + loop.
  - Animator: chuyen state; CHI reset khi state thay doi (khong reset
    loop moi frame); 30 FPS va 60 FPS cho ket qua tuong duong.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pygame


@dataclass
class AnimationClip:
    frames: list[pygame.Surface]
    frame_time: float = 0.12   # giay / frame
    loop: bool = True

    def frame_at(self, elapsed: float) -> pygame.Surface:
        if not self.frames:
            raise ValueError("AnimationClip rong")
        index = int(elapsed / self.frame_time)
        if self.loop:
            index %= len(self.frames)
        else:
            index = min(index, len(self.frames) - 1)
        return self.frames[index]

    def finished(self, elapsed: float) -> bool:
        if self.loop:
            return False
        return elapsed >= self.frame_time * len(self.frames)

    @property
    def duration(self) -> float:
        return self.frame_time * len(self.frames)


@dataclass
class Animator:
    clips: dict[str, AnimationClip]
    state: str = "idle"
    elapsed: float = 0.0
    # state tu dong quay ve sau khi clip non-loop ket thuc (vd flap -> idle)
    fallback: dict[str, str] = field(default_factory=dict)

    def play(self, state: str, restart: bool = False) -> None:
        """Doi state. Chi reset elapsed khi state THAY DOI hoac restart=True
        (flap lien tiep can restart de dap canh ngay)."""
        if state not in self.clips:
            return
        if state != self.state or restart:
            self.state = state
            self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt
        clip = self.clips[self.state]
        if clip.finished(self.elapsed):
            nxt = self.fallback.get(self.state)
            if nxt is not None and nxt in self.clips:
                self.state = nxt
                self.elapsed = 0.0

    @property
    def frame(self) -> pygame.Surface:
        return self.clips[self.state].frame_at(self.elapsed)
