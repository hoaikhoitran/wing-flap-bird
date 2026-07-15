"""Man hinh Credits: thong tin game, developer, cong nghe su dung.

Nut mo repository chi mo trinh duyet khi nguoi dung CHU DONG bam.
Khong hien thi email hay du lieu ca nhan.
"""
from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING

import pygame

import config
from core import links
from core.version import APP_AUTHOR, APP_NAME, APP_VERSION
from game.i18n import tr
from game.widgets import (COL_PANEL, COL_TEXT, COL_TEXT_DIM, Button,
                          WidgetScreen)

if TYPE_CHECKING:
    from game.game import Game

_TECH = ["Python 3.11", "Pygame", "OpenCV", "MediaPipe", "NumPy",
         "platformdirs", "PyInstaller"]


class CreditsScreen(WidgetScreen):
    def __init__(self, game: "Game") -> None:
        super().__init__()
        self.game = game
        self._build()

    def _build(self) -> None:
        self.widgets.clear()
        cx = config.WINDOW_WIDTH // 2
        self.widgets.append(Button(
            pygame.Rect(cx - 170, 530, 340, 48),
            tr("credits.open_repo"),
            lambda: webbrowser.open(links.REPOSITORY_URL)))
        self.widgets.append(Button(
            pygame.Rect(cx - 170, 592, 340, 48), tr("settings.back"),
            lambda: self.game.change_state_by_name("MAIN_MENU")))

    def on_enter(self) -> None:
        self._build()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.change_state_by_name("MAIN_MENU")
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 22, 34))
        ui = self.game.ui
        cx = config.WINDOW_WIDTH // 2

        panel = pygame.Rect(cx - 380, 60, 760, 440)
        pygame.draw.rect(surface, COL_PANEL, panel, border_radius=14)

        ui._text_outline(surface, tr("credits.title"), ui.font_big,
                         (cx, 100), color=(255, 220, 80))
        lines = [
            (f"{APP_NAME}  v{APP_VERSION}", COL_TEXT),
            (f"{tr('credits.developer')}: {APP_AUTHOR}", COL_TEXT),
            (links.REPOSITORY_URL, COL_TEXT_DIM),
            ("", COL_TEXT),
            (tr("credits.tech") + ":", COL_TEXT),
            ("  •  ".join(_TECH), COL_TEXT_DIM),
            ("Powered by MediaPipe (Apache License 2.0)", COL_TEXT_DIM),
            ("", COL_TEXT),
            (tr("credits.licenses"), COL_TEXT_DIM),
        ]
        y = 150
        for text, color in lines:
            if text:
                label = ui.font_medium.render(text, True, color)
                surface.blit(label, label.get_rect(center=(cx, y)))
            y += 38

        self.draw_widgets(surface, ui.font_medium)
