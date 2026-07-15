"""Menu chinh: PLAY / SETTINGS / HOW TO PLAY / SUPPORT / CREDITS / QUIT.

Dieu huong hoan toan bang chuot + ban phim, KHONG can webcam.
Camera khong duoc mo o man hinh nay.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import config
from core import links
from core.version import window_title
from game.i18n import tr
from game.widgets import Button, WidgetScreen

if TYPE_CHECKING:
    from game.game import Game


class MainMenuScreen(WidgetScreen):
    def __init__(self, game: "Game") -> None:
        super().__init__()
        self.game = game
        self._build()

    def _build(self) -> None:
        self.widgets.clear()
        cx = config.WINDOW_WIDTH // 2
        width, height, gap = 380, 52, 14
        y = 240
        entries = [
            ("menu.play", self.game.request_play),
            ("menu.settings",
             lambda: self.game.open_settings(from_pause=False)),
            ("menu.how_to_play",
             lambda: self.game.change_state_by_name("HOW_TO_PLAY")),
            ("menu.support",
             lambda: self.game.change_state_by_name("DONATE")),
            ("menu.credits",
             lambda: self.game.change_state_by_name("CREDITS")),
            ("menu.quit", self.game.request_quit),
        ]
        for key, action in entries:
            rect = pygame.Rect(cx - width // 2, y, width, height)
            button = Button(rect, tr(key), action)
            # Nut SUPPORT bat khi co link donate HOAC co anh QR ung ho
            if key == "menu.support" and not (links.donate_available()
                                              or links.support_qr_available()):
                button.enabled = False
                button.tooltip = tr("donate.missing")
            self.widgets.append(button)
            y += height + gap

    def on_enter(self) -> None:
        self._build()  # rebuild de cap nhat ngon ngu / trang thai donate

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.request_quit()
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        game = self.game
        game.background.draw_sky(surface)
        game.background.draw_ground(surface)
        game.player.draw(surface)

        ui = game.ui
        cx = config.WINDOW_WIDTH // 2
        ui._text_outline(surface, "WING FLAP BIRD", ui.font_huge,
                         (cx, 110), color=(255, 220, 80))
        ui._text_outline(surface, tr("menu.tagline"), ui.font_big, (cx, 175))
        ui._text_outline(surface,
                         tr("menu.high_score", score=game.high_score),
                         ui.font_medium, (cx, 645), color=(255, 220, 80))

        version = ui.font_small.render(window_title(), True, (240, 244, 250))
        surface.blit(version, (10, config.WINDOW_HEIGHT - 24))

        self.draw_widgets(surface, ui.font_medium)
