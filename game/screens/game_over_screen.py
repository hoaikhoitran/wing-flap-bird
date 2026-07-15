"""Man hinh Game Over: card co shadow, hierarchy diem ro, button that.

Ve DE LEN the gioi game dong bang (nhan vat dang o hurt animation).
Phim tat van hoat dong: R = choi lai, M/ESC = ve menu.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import config
from core import font_manager as fm
from game import theme
from game.i18n import tr
from game.widgets import Button, WidgetScreen

if TYPE_CHECKING:
    from game.game import Game


class GameOverScreen(WidgetScreen):
    def __init__(self, game: "Game") -> None:
        super().__init__()
        self.game = game
        self._build()

    def _build(self) -> None:
        self.widgets.clear()
        cx = config.WINDOW_WIDTH // 2
        y = 400
        self.widgets.append(Button(
            pygame.Rect(cx - 170, y, 340, 52), tr("over.restart_btn"),
            self.game._start_game, primary=True))
        self.widgets.append(Button(
            pygame.Rect(cx - 170, y + 64, 340, 52), tr("over.change_char"),
            lambda: self.game.open_character_select(from_game_over=True)))
        self.widgets.append(Button(
            pygame.Rect(cx - 170, y + 128, 340, 52), tr("over.menu_btn"),
            self.game.back_to_menu))

    def on_enter(self) -> None:
        self._build()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.game._start_game()
                return True
            if event.key in (pygame.K_m, pygame.K_ESCAPE):
                self.game.back_to_menu()
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        game = self.game
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*theme.DEEP_NAVY, 130))
        surface.blit(overlay, (0, 0))

        cx = config.WINDOW_WIDTH // 2
        card = pygame.Rect(cx - 250, 96, 500, 500)
        # Card + soft shadow 2.5D
        pygame.draw.rect(surface, (*theme.DARK_INK,),
                         card.move(6, 10), border_radius=theme.RADIUS_L)
        pygame.draw.rect(surface, theme.PANEL_DARK, card,
                         border_radius=theme.RADIUS_L)
        pygame.draw.rect(surface, theme.PANEL_DARK_BORDER, card, 3,
                         border_radius=theme.RADIUS_L)

        title = fm.render_outlined("display", tr("over.title"),
                                   theme.VERMILION, theme.DARK_INK, size=46)
        surface.blit(title, title.get_rect(center=(cx, card.y + 56)))

        # Hierarchy diem: score to > best nho
        score = fm.render_outlined("score", str(game.score), theme.CREAM,
                                   theme.DARK_INK, size=64, thickness=3)
        surface.blit(score, score.get_rect(center=(cx, card.y + 150)))
        if game.is_new_record:
            badge = fm.render("heading", tr("over.new_record"),
                              theme.DARK_INK, size=20)
            box = badge.get_rect(center=(cx, card.y + 220)).inflate(24, 10)
            pygame.draw.rect(surface, theme.MANGO, box,
                             border_radius=theme.RADIUS_S)
            surface.blit(badge, badge.get_rect(center=box.center))
        else:
            best = fm.render("heading",
                             tr("hud.best", score=game.high_score),
                             theme.TEXT_ACCENT, size=20)
            surface.blit(best, best.get_rect(center=(cx, card.y + 220)))

        # Nhan vat hurt (frame that tu animator)
        frame = game.player.animator.frame
        sprite = pygame.transform.smoothscale(
            frame, (int(frame.get_width() * 0.9),
                    int(frame.get_height() * 0.9)))
        surface.blit(sprite, sprite.get_rect(center=(cx, card.y + 275)))

        self.draw_widgets(surface, game.ui.font_button)
