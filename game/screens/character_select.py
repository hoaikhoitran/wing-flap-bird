"""Man hinh chon nhan vat: 5 card voi preview animation THAT.

- Khong khoa nhan vat, khong donate, khong loi the gameplay.
- Preview dung chinh AnimationClip cua nhan vat (idle loop).
- Dieu huong: chuot + Left/Right/Tab + Enter; nut CHON va QUAY LAI.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable

import pygame

import config
from core import font_manager as fm
from game import theme
from game.animation import Animator
from game.assets import assets
from game.characters import CHARACTER_IDS, get_character, load_animator
from game.i18n import tr
from game.widgets import Button, Widget, WidgetScreen

if TYPE_CHECKING:
    from game.game import Game

_CONTACT_SHADOW = "assets/art/effects/contact_shadow.png"


class CharacterCard(Widget):
    """Card 1 nhan vat: preview animation + ten + badge selected."""

    def __init__(self, rect: pygame.Rect, char_id: str,
                 animator: Animator,
                 on_pick: Callable[[str], None]) -> None:
        super().__init__(rect)
        self.char_id = char_id
        self.animator = animator
        self.on_pick = on_pick
        self.highlighted = False
        self.selected = False
        self._time = 0.0

    def handle_event(self, event: pygame.event.Event) -> bool:
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                and self.rect.collidepoint(event.pos):
            self.press_feedback()
            self.on_pick(self.char_id)
            return True
        return False

    def activate(self) -> None:
        self.press_feedback()
        self.on_pick(self.char_id)

    def update(self, dt: float) -> None:
        super().update(dt)
        self._time += dt
        self.animator.update(dt)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        rect = self._visual_rect()
        # Panel card + "day" 2.5D
        pygame.draw.rect(surface, theme.DARK_INK, rect.move(0, 5),
                         border_radius=theme.RADIUS_M)
        bg = theme.BUTTON_BG_HOVER if self.highlighted else theme.PANEL_DARK
        pygame.draw.rect(surface, bg, rect, border_radius=theme.RADIUS_M)
        border = (theme.FOCUS_RING if self.focused or self.highlighted
                  else theme.PANEL_DARK_BORDER)
        pygame.draw.rect(surface, border, rect, 3,
                         border_radius=theme.RADIUS_M)

        # Platform + contact shadow + preview bay idle
        cx = rect.centerx
        platform_y = rect.y + 150
        pygame.draw.ellipse(surface, theme.PANEL_DARK_BORDER,
                            (cx - 52, platform_y - 8, 104, 20))
        shadow = assets.scaled(_CONTACT_SHADOW, (72, 18))
        shadow.set_alpha(130)
        surface.blit(shadow, shadow.get_rect(center=(cx, platform_y)))

        frame = self.animator.frame
        bob = math.sin(self._time * 2.6) * 5.0
        sprite = pygame.transform.smoothscale(
            frame, (int(frame.get_width() * 1.15),
                    int(frame.get_height() * 1.15)))
        surface.blit(sprite, sprite.get_rect(
            center=(cx, rect.y + 88 + int(bob))))

        # Ten nhan vat
        name = fm.render("heading", tr(get_character(self.char_id).name_key),
                         theme.TEXT_ON_DARK, size=21)
        surface.blit(name, name.get_rect(center=(cx, rect.bottom - 62)))

        # Badge dang chon
        if self.selected:
            badge = fm.render("caption", "★ " + tr("select.selected"),
                              theme.DARK_INK, size=14)
            box = badge.get_rect(center=(cx, rect.bottom - 28)).inflate(14, 8)
            pygame.draw.rect(surface, theme.MANGO, box,
                             border_radius=theme.RADIUS_S)
            surface.blit(badge, badge.get_rect(center=box.center))


class CharacterSelectScreen(WidgetScreen):
    def __init__(self, game: "Game") -> None:
        super().__init__()
        self.game = game
        self.highlight_id = game.settings.selected_character
        self._cards: list[CharacterCard] = []
        self._build()

    def _build(self) -> None:
        self.widgets.clear()
        self._cards.clear()
        card_w, card_h, gap = 180, 280, 12
        total = len(CHARACTER_IDS) * card_w + (len(CHARACTER_IDS) - 1) * gap
        x = (config.WINDOW_WIDTH - total) // 2
        y = 120
        for char_id in CHARACTER_IDS:
            rect = pygame.Rect(x, y, card_w, card_h)
            card = CharacterCard(rect, char_id, load_animator(char_id),
                                 self._pick)
            card.selected = (char_id
                             == self.game.settings.selected_character)
            card.highlighted = (char_id == self.highlight_id)
            self._cards.append(card)
            self.widgets.append(card)
            x += card_w + gap

        cx = config.WINDOW_WIDTH // 2
        self.widgets.append(Button(
            pygame.Rect(cx - 250, 560, 235, 52), tr("select.choose"),
            self._confirm, primary=True))
        self.widgets.append(Button(
            pygame.Rect(cx + 15, 560, 235, 52), tr("settings.back"),
            self._back))

    def on_enter(self) -> None:
        self.highlight_id = self.game.settings.selected_character
        self._build()

    # ------------------------------------------------------------------
    def _pick(self, char_id: str) -> None:
        self.highlight_id = char_id
        for card in self._cards:
            card.highlighted = (card.char_id == char_id)

    def _confirm(self) -> None:
        self.game.select_character(self.highlight_id)
        for card in self._cards:
            card.selected = (card.char_id == self.highlight_id)

    def _back(self) -> None:
        self.game.close_character_select()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return True
        return False

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        game = self.game
        game.background.draw_back(surface)
        game.background.draw_front(surface)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*theme.DEEP_NAVY, 140))
        surface.blit(overlay, (0, 0))

        ui = game.ui
        cx = config.WINDOW_WIDTH // 2
        ui._text_outline(surface, tr("select.title"), "title", (cx, 56),
                         color=theme.MANGO)

        # Mo ta nhan vat dang highlight
        spec = get_character(self.highlight_id)
        desc = fm.render("body", tr(spec.description_key),
                         theme.TEXT_ON_DARK)
        surface.blit(desc, desc.get_rect(center=(cx, 440)))
        note = fm.render("caption", tr("select.equal_note"),
                         theme.TEXT_DIM_ON_DARK)
        surface.blit(note, note.get_rect(center=(cx, 470)))

        self.draw_widgets(surface, ui.font_button)
