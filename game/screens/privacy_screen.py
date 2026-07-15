"""Man hinh thong bao quyen rieng tu webcam - hien lan dau chay game
(hoac khi PRIVACY_VERSION tang). Phai bam "TOI DA HIEU" moi vao menu.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import config
from core.version import PRIVACY_VERSION
from game.i18n import tr
from game.widgets import COL_PANEL, COL_TEXT, Button, WidgetScreen

if TYPE_CHECKING:
    from game.game import Game


class PrivacyScreen(WidgetScreen):
    def __init__(self, game: "Game") -> None:
        super().__init__()
        self.game = game
        self._build()

    def _build(self) -> None:
        self.widgets.clear()
        cx = config.WINDOW_WIDTH // 2
        button = Button(pygame.Rect(cx - 160, 520, 320, 56),
                        tr("privacy.accept"), self._accept)
        button.focused = True
        self.widgets.append(button)

    def on_enter(self) -> None:
        self._build()

    def _accept(self) -> None:
        settings = self.game.settings
        settings.privacy_accepted_version = PRIVACY_VERSION
        settings.save()
        self.game.change_state_by_name("MAIN_MENU")

    def handle_event(self, event: pygame.event.Event) -> bool:
        # Khong cho ESC bo qua - nguoi dung phai xac nhan
        return super().handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 22, 34))
        ui = self.game.ui
        cx = config.WINDOW_WIDTH // 2

        panel = pygame.Rect(cx - 400, 120, 800, 360)
        pygame.draw.rect(surface, COL_PANEL, panel, border_radius=14)
        pygame.draw.rect(surface, (255, 210, 70), panel, 2, border_radius=14)

        ui._text_outline(surface, tr("privacy.title"), ui.font_big,
                         (cx, 160), color=(255, 220, 80))
        lines = [tr("privacy.body1"), tr("privacy.body2"),
                 tr("privacy.body3"), "", tr("privacy.more")]
        y = 230
        for line in lines:
            if line:
                label = ui.font_medium.render(line, True, COL_TEXT)
                surface.blit(label, label.get_rect(center=(cx, y)))
            y += 44

        self.draw_widgets(surface, ui.font_medium)
