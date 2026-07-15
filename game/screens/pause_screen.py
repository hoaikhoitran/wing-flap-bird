"""Pause menu (ESC trong gameplay).

Khi pause: player physics / obstacle / score dung han.
Vision thread van chay nhung flap KHONG duoc dua vao game;
khi resume, game se clear pending flap de chim khong tu bay.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import config
from game.i18n import tr
from game.widgets import COL_PANEL, Button, WidgetScreen

if TYPE_CHECKING:
    from game.game import Game


class PauseScreen(WidgetScreen):
    def __init__(self, game: "Game") -> None:
        super().__init__()
        self.game = game
        self._build()

    def _build(self) -> None:
        self.widgets.clear()
        cx = config.WINDOW_WIDTH // 2
        width, height, gap = 320, 48, 12
        y = 240
        entries = [
            ("pause.resume", self.game.resume_from_pause),
            ("pause.restart", self.game.restart_from_pause),
            ("pause.settings",
             lambda: self.game.open_settings(from_pause=True)),
            ("pause.main_menu", self.game.back_to_menu),
            ("pause.quit", self.game.request_quit),
        ]
        for key, action in entries:
            rect = pygame.Rect(cx - width // 2, y, width, height)
            self.widgets.append(Button(rect, tr(key), action))
            y += height + gap

    def on_enter(self) -> None:
        self._build()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.resume_from_pause()
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        # The gioi game dong bang phia sau (game da ve san vao surface)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((10, 12, 20, 170))
        surface.blit(overlay, (0, 0))

        ui = self.game.ui
        cx = config.WINDOW_WIDTH // 2
        panel = pygame.Rect(cx - 210, 150, 420, 420)
        pygame.draw.rect(surface, COL_PANEL, panel, border_radius=14)
        pygame.draw.rect(surface, (255, 210, 70), panel, 2, border_radius=14)
        ui._text_outline(surface, tr("pause.title"), ui.font_big,
                         (cx, 195), color=(255, 220, 80))

        self.draw_widgets(surface, ui.font_medium)
