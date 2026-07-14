"""Chuong ngai vat: cac cap cot di chuyen tu phai sang trai."""
from __future__ import annotations

import random

import pygame

import config

_PIPE_BODY = (86, 180, 78)
_PIPE_LIGHT = (128, 210, 110)
_PIPE_DARK = (46, 120, 46)
_RIM_EXTRA = 7      # Vanh cot rong hon than bao nhieu px moi ben
_RIM_HEIGHT = 30


class PipePair:
    """Mot cap cot tren-duoi voi khoang trong o giua."""

    def __init__(self, x: float, gap_center_y: float, gap_size: float) -> None:
        self.x = x
        self.gap_center_y = gap_center_y
        self.gap_size = gap_size
        self.scored = False

    def update(self, dt: float) -> None:
        self.x -= config.PIPE_SPEED * dt

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
        top, bottom = self.rects
        for rect, rim_at_bottom in ((top, True), (bottom, False)):
            if rect.height <= 0:
                continue
            pygame.draw.rect(surface, _PIPE_BODY, rect)
            # Soc sang ben trai cho co chieu sau
            pygame.draw.rect(surface, _PIPE_LIGHT,
                             (rect.x + 6, rect.y, 14, rect.height))
            pygame.draw.rect(surface, _PIPE_DARK, rect, 3)
            # Vanh cot o mep khoang trong
            rim_y = (rect.bottom - _RIM_HEIGHT) if rim_at_bottom else rect.y
            rim = pygame.Rect(rect.x - _RIM_EXTRA, rim_y,
                              rect.width + 2 * _RIM_EXTRA, _RIM_HEIGHT)
            pygame.draw.rect(surface, _PIPE_BODY, rim)
            pygame.draw.rect(surface, _PIPE_LIGHT,
                             (rim.x + 4, rim.y, 12, rim.height))
            pygame.draw.rect(surface, _PIPE_DARK, rim, 3)


class ObstacleManager:
    """Sinh, di chuyen, tinh diem va kiem tra va cham cho cac cap cot."""

    def __init__(self, player_x: float) -> None:
        self._player_x = player_x
        self.pipes: list[PipePair] = []
        self._distance_since_spawn = 0.0

    def reset(self) -> None:
        self.pipes.clear()
        # Cot dau tien chi xuat hien sau FIRST_OBSTACLE_DELAY giay ke tu GO
        # (khoi tao am de phai tich luy du quang duong truoc lan sinh dau)
        self._distance_since_spawn = (
            config.PIPE_SPACING
            - config.PIPE_SPEED * config.FIRST_OBSTACLE_DELAY)

    def update(self, dt: float) -> int:
        """Cap nhat moi cot. Tra ve so diem moi ghi duoc trong frame nay."""
        scored = 0
        self._distance_since_spawn += config.PIPE_SPEED * dt
        if self._distance_since_spawn >= config.PIPE_SPACING:
            self._distance_since_spawn = 0.0
            self._spawn()

        for pipe in self.pipes:
            pipe.update(dt)
            if not pipe.scored and pipe.x + config.PIPE_WIDTH < self._player_x:
                pipe.scored = True
                scored += 1

        self.pipes = [p for p in self.pipes if not p.off_screen]
        return scored

    def _spawn(self) -> None:
        """Sinh cap cot moi voi khoang trong ngau nhien nhung luon qua duoc."""
        gap = random.uniform(config.PIPE_GAP_MIN, config.PIPE_GAP_MAX)
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
