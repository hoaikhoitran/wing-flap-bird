"""Menu chinh - WIND FESTIVAL SKY.

- Background 2.5D parallax chuyen dong nhe (may + dieu troi ambient).
- Nhan vat dang chon bay idle voi contact shadow.
- Panel menu co depth; nut CHOI la primary (mango), khac secondary.
- Hien che do Camera/Keyboard + ky luc + version o vi tri phu.
- Dieu huong chuot + ban phim, KHONG can webcam.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import config
from core import font_manager as fm
from core import links
from core.version import window_title
from game import theme
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
        cx = config.WINDOW_WIDTH // 2 + 170  # menu lech phai, chim ben trai
        width, height, gap = 340, 47, 10
        y = 178
        entries = [
            ("menu.play", self.game.request_play, True),
            ("menu.characters",
             lambda: self.game.open_character_select(), False),
            ("menu.settings",
             lambda: self.game.open_settings(from_pause=False), False),
            ("menu.how_to_play",
             lambda: self.game.change_state_by_name("HOW_TO_PLAY"), False),
            ("menu.support",
             lambda: self.game.change_state_by_name("DONATE"), False),
            ("menu.credits",
             lambda: self.game.change_state_by_name("CREDITS"), False),
            ("menu.quit", self.game.request_quit, False),
        ]
        for key, action, primary in entries:
            rect = pygame.Rect(cx - width // 2, y, width, height)
            button = Button(rect, tr(key), action, primary=primary)
            if key == "menu.support" and not (links.donate_available()
                                              or links.support_qr_available()):
                button.enabled = False
                button.tooltip = tr("donate.missing")
            self.widgets.append(button)
            y += height + gap

    def on_enter(self) -> None:
        self._build()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.request_quit()
            return True
        return False

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        game = self.game
        ground_top = config.WINDOW_HEIGHT - config.GROUND_HEIGHT
        game.background.draw_back(surface)
        game.background.draw_front(surface)

        # Nhan vat dang chon bay idle ben trai + contact shadow
        game.player.x = 240
        game.player.draw_shadow(surface, ground_top)
        game.player.draw(surface)

        # Title 2 tang co outline
        title = fm.render_outlined("display", "WING FLAP BIRD",
                                   theme.MANGO, theme.DARK_INK,
                                   size=64, thickness=3)
        surface.blit(title, title.get_rect(
            center=(config.WINDOW_WIDTH // 2, 80)))
        tagline = fm.render_outlined("heading", tr("menu.tagline"),
                                     theme.CREAM, theme.DARK_INK)
        surface.blit(tagline, tagline.get_rect(
            center=(config.WINDOW_WIDTH // 2, 132)))

        # Panel menu co "day" (depth)
        panel = pygame.Rect(0, 0, 384, 434)
        panel.center = (config.WINDOW_WIDTH // 2 + 170, 380)
        pygame.draw.rect(surface, (*theme.DARK_INK,), panel.move(5, 8),
                         border_radius=theme.RADIUS_L)
        panel_bg = pygame.Surface(panel.size, pygame.SRCALPHA)
        panel_bg.fill((*theme.PANEL_DARK, 216))
        surface.blit(panel_bg, panel)
        pygame.draw.rect(surface, theme.PANEL_DARK_BORDER, panel, 2,
                         border_radius=theme.RADIUS_L)

        self.draw_widgets(surface, game.ui.font_button)

        # Ky luc + ten nhan vat dang chon (chip nho ben trai)
        chip_lines = [
            tr("menu.high_score", score=game.high_score),
            tr(game.player.character.name_key),
            tr("menu.mode_camera") if game.use_camera
            else tr("menu.mode_keyboard"),
        ]
        y = 470
        for line in chip_lines:
            label = fm.render("caption", line, theme.CREAM)
            bg = pygame.Surface((label.get_width() + 16,
                                 label.get_height() + 8), pygame.SRCALPHA)
            bg.fill((*theme.DARK_INK, 150))
            surface.blit(bg, (240 - bg.get_width() // 2, y))
            surface.blit(label, (240 - label.get_width() // 2, y + 4))
            y += 32

        # Version o goc phu
        version = fm.render("caption", window_title(),
                            theme.TEXT_DIM_ON_DARK, size=13)
        surface.blit(version, (10, config.WINDOW_HEIGHT - 22))
