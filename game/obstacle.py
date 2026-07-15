"""Chuong ngai vat: Bamboo Wind Gate di chuyen tu phai sang trai.

Visual la cot tre + thanh ngang + co lua + soft shadow, nhung
COLLISION RECT giu NGUYEN nhu truoc (rects property khong doi) ->
gameplay khong thay doi, khong va cham oan.
"""
from __future__ import annotations

import math
import random

import pygame

import config
from game.assets import assets

_A = "assets/art/obstacles"
_COL_H = 620          # chieu cao texture cot tre
_CAP_W, _CAP_H = 108, 34
_H_STEP = 8           # luong tu hoa chieu cao crop de cache hieu qua


class PipePair:
    """Mot cap cot tren-duoi voi khoang trong o giua."""

    def __init__(self, x: float, gap_center_y: float, gap_size: float) -> None:
        self.x = x
        self.gap_center_y = gap_center_y
        self.gap_size = gap_size
        self.scored = False

    def update(self, dt: float, speed: float) -> None:
        self.x -= speed * dt

    @property
    def rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        """(cot tren, cot duoi) - dung cho ca va cham va ve."""
        top_h = int(self.gap_center_y - self.gap_size / 2)
        bottom_y = int(self.gap_center_y + self.gap_size / 2)
        playfield_bottom = config.WINDOW_HEIGHT - config.GROUND_HEIGHT
        top = pygame.Rect(int(self.x), 0, config.PIPE_WIDTH, max(0, top_h))
        bottom = pygame.Rect(int(self.x), bottom_y, config.PIPE_WIDTH,
                             max(0, playfield_bottom - bottom_y))
        return top, bottom

    @property
    def off_screen(self) -> bool:
        return self.x + config.PIPE_WIDTH < -10

    def draw(self, surface: pygame.Surface) -> None:
        """Ve Bamboo Wind Gate. Visual bam sat collision rect."""
        top, bottom = self.rects
        t = pygame.time.get_ticks() / 1000.0
        # Co lua bay nhe theo thoi gian (chi offset, khong allocate)
        flutter = math.sin(t * 5.0 + self.x * 0.02) * 2.0
        ribbon = ("ribbon_red" if int(self.gap_center_y) % 2 == 0
                  else "ribbon_yellow")

        for rect, is_top in ((top, True), (bottom, False)):
            if rect.height <= 0:
                continue
            # Chieu cao crop luong tu hoa (phan thua tran ra ngoai man
            # hinh phia tren / bi mat dat che phia duoi)
            q = min(_COL_H,
                    ((rect.height + _H_STEP - 1) // _H_STEP) * _H_STEP)
            tex = f"{_A}/bamboo_gate_top.png" if is_top \
                else f"{_A}/bamboo_gate_bottom.png"
            if is_top:
                column = assets.cropped(tex, (0, _COL_H - q,
                                              config.PIPE_WIDTH, q))
                col_y = rect.bottom - q
            else:
                column = assets.cropped(tex, (0, 0, config.PIPE_WIDTH, q))
                col_y = rect.top

            # Soft shadow do sang phai (truoc cot, sau background)
            shadow = assets.cropped(f"{_A}/gate_shadow.png",
                                    (0, 0, 46, q))
            surface.blit(shadow, (rect.right - 6, col_y))
            surface.blit(column, (rect.x, col_y))

            # Thanh ngang o mep khoang trong + co lua
            cap = assets.image(f"{_A}/gate_cap.png")
            cap_x = rect.centerx - _CAP_W // 2
            if is_top:
                surface.blit(cap, (cap_x, rect.bottom - _CAP_H + 4))
                surface.blit(assets.image(f"{_A}/{ribbon}.png"),
                             (rect.right - 10,
                              rect.bottom + 2 + flutter))
            else:
                surface.blit(cap, (cap_x, rect.top - 4))
                surface.blit(assets.image(f"{_A}/{ribbon}.png"),
                             (rect.right - 10,
                              rect.top - 32 - flutter))


class ObstacleManager:
    """Sinh, di chuyen, tinh diem va kiem tra va cham cho cac cap cot.

    Thong so (toc do, gap, chu ky sinh) lay tu DifficultyConfig,
    doi duoc moi luot choi.
    """

    def __init__(self, player_x: float,
                 diff: config.DifficultyConfig | None = None) -> None:
        self._player_x = player_x
        self.diff = diff or config.EASY
        self.pipes: list[PipePair] = []
        self._distance_since_spawn = 0.0

    def set_difficulty(self, diff: config.DifficultyConfig) -> None:
        self.diff = diff

    def reset(self) -> None:
        self.pipes.clear()
        # Cot dau tien chi xuat hien sau first_obstacle_delay giay ke tu GO
        # (khoi tao am de phai tich luy du quang duong truoc lan sinh dau)
        self._distance_since_spawn = (
            self.diff.pipe_spacing
            - self.diff.pipe_speed * self.diff.first_obstacle_delay)

    def update(self, dt: float) -> int:
        """Cap nhat moi cot. Tra ve so diem moi ghi duoc trong frame nay."""
        scored = 0
        self._distance_since_spawn += self.diff.pipe_speed * dt
        if self._distance_since_spawn >= self.diff.pipe_spacing:
            self._distance_since_spawn = 0.0
            self._spawn()

        for pipe in self.pipes:
            pipe.update(dt, self.diff.pipe_speed)
            if not pipe.scored and pipe.x + config.PIPE_WIDTH < self._player_x:
                pipe.scored = True
                scored += 1

        self.pipes = [p for p in self.pipes if not p.off_screen]
        return scored

    def _spawn(self) -> None:
        """Sinh cap cot moi voi khoang trong ngau nhien nhung luon qua duoc."""
        gap = random.uniform(self.diff.pipe_gap_min, self.diff.pipe_gap_max)
        playfield_bottom = config.WINDOW_HEIGHT - config.GROUND_HEIGHT
        min_center = config.PIPE_GAP_MARGIN + gap / 2
        max_center = playfield_bottom - config.PIPE_GAP_MARGIN - gap / 2
        center = random.uniform(min_center, max_center)
        self.pipes.append(PipePair(config.WINDOW_WIDTH + 40, center, gap))

    def check_collision(self, cx: float, cy: float, radius: float) -> bool:
        """Va cham hinh tron (nhan vat) vs hinh chu nhat (cot)."""
        for pipe in self.pipes:
            for rect in pipe.rects:
                if rect.height <= 0:
                    continue
                # Diem gan nhat tren rect toi tam hinh tron
                nearest_x = max(rect.left, min(cx, rect.right))
                nearest_y = max(rect.top, min(cy, rect.bottom))
                dx, dy = cx - nearest_x, cy - nearest_y
                if dx * dx + dy * dy < radius * radius:
                    return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        for pipe in self.pipes:
            pipe.draw(surface)
