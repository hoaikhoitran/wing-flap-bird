"""AssetManager: load/cache anh qua resource_path.

Quy tac hieu nang (skill performance-optimization):
  - Moi file chi doc MOT lan; convert_alpha MOT lan.
  - Ket qua scale/crop deu duoc cache - KHONG smoothscale lai moi frame.
  - Thieu asset bat buoc -> AssetError ro rang (release test se fail),
    kem huong dan chay lai generator cho developer.
"""
from __future__ import annotations

import logging
from typing import Optional

import pygame

from core.paths import resource_path

logger = logging.getLogger(__name__)


class AssetError(RuntimeError):
    pass


class AssetManager:
    def __init__(self) -> None:
        self._images: dict[str, pygame.Surface] = {}
        self._scaled: dict[tuple[str, int, int], pygame.Surface] = {}
        self._cropped: dict[tuple[str, int, int, int, int], pygame.Surface] = {}
        self._strips: dict[tuple[str, int], list[pygame.Surface]] = {}

    # ------------------------------------------------------------------
    def image(self, rel: str) -> pygame.Surface:
        """Anh goc (cache). rel tinh tu goc project, vd 'assets/art/...'."""
        surf = self._images.get(rel)
        if surf is None:
            path = resource_path(rel)
            if not path.exists():
                raise AssetError(
                    f"Thieu asset bat buoc: {rel}. Developer: chay "
                    f"`python scripts/generate_game_assets.py` de tao lai.")
            surf = pygame.image.load(str(path))
            surf = self._convert(surf)
            self._images[rel] = surf
        return surf

    @staticmethod
    def _convert(surf: pygame.Surface) -> pygame.Surface:
        try:
            return surf.convert_alpha()
        except pygame.error:
            return surf  # chua co display mode (test headless som)

    # ------------------------------------------------------------------
    def scaled(self, rel: str, size: tuple[int, int]) -> pygame.Surface:
        """smoothscale co cache theo (rel, w, h)."""
        key = (rel, size[0], size[1])
        surf = self._scaled.get(key)
        if surf is None:
            surf = pygame.transform.smoothscale(self.image(rel), size)
            self._scaled[key] = surf
        return surf

    def cropped(self, rel: str, rect: tuple[int, int, int, int]
                ) -> pygame.Surface:
        """subsurface copy co cache (dung cho cot tre cao thay doi)."""
        key = (rel, *rect)
        surf = self._cropped.get(key)
        if surf is None:
            src = self.image(rel)
            r = pygame.Rect(rect).clip(src.get_rect())
            surf = src.subsurface(r).copy()
            self._cropped[key] = surf
        return surf

    def strip(self, rel: str, frame_width: int) -> list[pygame.Surface]:
        """Cat sprite strip ngang thanh list frame (cache)."""
        key = (rel, frame_width)
        frames = self._strips.get(key)
        if frames is None:
            sheet = self.image(rel)
            w, h = sheet.get_size()
            count = max(1, w // frame_width)
            frames = [
                sheet.subsurface(
                    pygame.Rect(i * frame_width, 0, frame_width, h)).copy()
                for i in range(count)
            ]
            self._strips[key] = frames
        return frames

    # ------------------------------------------------------------------
    def preload(self, rels: list[str]) -> None:
        for rel in rels:
            self.image(rel)

    def clear(self) -> None:
        self._images.clear()
        self._scaled.clear()
        self._cropped.clear()
        self._strips.clear()


# Singleton dung chung toan game
assets = AssetManager()
