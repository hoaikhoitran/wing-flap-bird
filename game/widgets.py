"""Widget system - WIND FESTIVAL SKY.

  - Mau tu game/theme.py (khong hard-code).
  - Text qua font truyen vao (font_manager, cache san) - khong tao font moi.
  - Hover scale ~1.02, press ~0.97 roi tra ve (ease) - skill game-feel.
  - Focus ban phim (Up/Down/Tab) + chuot; disabled state; sound hook
    menu_move / menu_confirm (game gan qua set_sound_hook).
"""
from __future__ import annotations

from typing import Callable, Optional, Sequence

import pygame

from game import theme

# Alias tuong thich (screens cu) -> token trong game/theme.py
COL_PANEL = theme.PANEL_DARK
COL_BUTTON = theme.BUTTON_BG
COL_BUTTON_HOVER = theme.BUTTON_BG_HOVER
COL_BUTTON_DISABLED = theme.BUTTON_DISABLED
COL_FOCUS = theme.FOCUS_RING
COL_TEXT = theme.TEXT_ON_DARK
COL_TEXT_DIM = theme.TEXT_DIM_ON_DARK
COL_ACCENT = theme.MANGO
COL_GREEN = theme.STATE_FLAP
COL_RED = theme.VERMILION

# ---------------------------------------------------------------------
# Sound hook (menu_move / menu_confirm) - game gan sau khi SoundBank san sang
# ---------------------------------------------------------------------
_sound_hook: Optional[Callable[[str], None]] = None


def set_sound_hook(hook: Optional[Callable[[str], None]]) -> None:
    global _sound_hook
    _sound_hook = hook


def _play(name: str) -> None:
    if _sound_hook is not None:
        _sound_hook(name)


class Widget:
    focusable = True

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.focused = False
        self.enabled = True
        self.visible = True
        self._hover = False
        self._hover_anim = 0.0
        self._press_anim = 0.0

    def update(self, dt: float) -> None:
        target = 1.0 if (self._hover or self.focused) and self.enabled else 0.0
        self._hover_anim += (target - self._hover_anim) * min(1.0, 12.0 * dt)
        self._press_anim += (0.0 - self._press_anim) * min(1.0, 14.0 * dt)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled or not self.visible:
            return False
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        return False

    def press_feedback(self) -> None:
        self._press_anim = 1.0
        _play("menu_confirm")

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        raise NotImplementedError

    def activate(self) -> None:
        pass

    def adjust(self, direction: int) -> None:
        pass

    # scale hien tai theo hover/press (game-feel: 1.02 / 0.97)
    def _visual_rect(self) -> pygame.Rect:
        scale = (1.0 + 0.02 * self._hover_anim) * (1.0
                                                   - 0.03 * self._press_anim)
        rect = self.rect
        w, h = int(rect.width * scale), int(rect.height * scale)
        out = pygame.Rect(0, 0, w, h)
        out.center = rect.center
        return out


class Button(Widget):
    def __init__(self, rect: pygame.Rect, label: str,
                 on_click: Callable[[], None],
                 tooltip: str = "", primary: bool = False) -> None:
        super().__init__(rect)
        self.label = label
        self.on_click = on_click
        self.tooltip = tooltip
        self.primary = primary

    def handle_event(self, event: pygame.event.Event) -> bool:
        super().handle_event(event)
        if not self.enabled or not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                and self.rect.collidepoint(event.pos):
            self.press_feedback()
            self.on_click()
            return True
        return False

    def activate(self) -> None:
        if self.enabled:
            self.press_feedback()
            self.on_click()

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.visible:
            return
        rect = self._visual_rect()
        if not self.enabled:
            bg, text_color = theme.BUTTON_DISABLED, theme.TEXT_DIM_ON_DARK
        elif self.primary:
            k = self._hover_anim
            bg = tuple(int(theme.BUTTON_PRIMARY[i]
                           + (theme.BUTTON_PRIMARY_HOVER[i]
                              - theme.BUTTON_PRIMARY[i]) * k)
                       for i in range(3))
            text_color = theme.BUTTON_TEXT_PRIMARY
        else:
            k = self._hover_anim
            bg = tuple(int(theme.BUTTON_BG[i]
                           + (theme.BUTTON_BG_HOVER[i]
                              - theme.BUTTON_BG[i]) * k)
                       for i in range(3))
            text_color = theme.TEXT_ON_DARK
        # "day" 2.5D: khoi toi phia duoi
        base = rect.move(0, 4)
        pygame.draw.rect(surface, theme.DARK_INK, base,
                         border_radius=theme.RADIUS_M)
        pygame.draw.rect(surface, bg, rect, border_radius=theme.RADIUS_M)
        border = theme.FOCUS_RING if self.focused else theme.DARK_INK
        pygame.draw.rect(surface, border, rect, 2,
                         border_radius=theme.RADIUS_M)
        # highlight canh tren (anh sang tren-trai)
        hi = pygame.Rect(rect.x + 6, rect.y + 3, rect.width - 12, 6)
        hi_surf = pygame.Surface(hi.size, pygame.SRCALPHA)
        hi_surf.fill((255, 255, 255, 60))
        surface.blit(hi_surf, hi)

        label = font.render(self.label, True, text_color)
        surface.blit(label, label.get_rect(center=rect.center))
        # Tooltip dung font caption tu font_manager (co cache san)
        if self.tooltip and not self.enabled and self._hover:
            from core import font_manager as fm
            tip = fm.render("caption", self.tooltip,
                            theme.TEXT_DIM_ON_DARK, size=14)
            surface.blit(tip, tip.get_rect(
                midtop=(rect.centerx, rect.bottom + 6)))


class Toggle(Widget):
    def __init__(self, rect: pygame.Rect, label: str, value: bool,
                 on_change: Callable[[bool], None],
                 on_text: str = "ON", off_text: str = "OFF") -> None:
        super().__init__(rect)
        self.label = label
        self.value = value
        self.on_change = on_change
        self.on_text = on_text
        self.off_text = off_text

    def _flip(self) -> None:
        self.value = not self.value
        self.press_feedback()
        self.on_change(self.value)

    def handle_event(self, event: pygame.event.Event) -> bool:
        super().handle_event(event)
        if not self.enabled or not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                and self.rect.collidepoint(event.pos):
            self._flip()
            return True
        return False

    def activate(self) -> None:
        self._flip()

    def adjust(self, direction: int) -> None:
        self._flip()

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.visible:
            return
        label = font.render(self.label, True, theme.TEXT_ON_DARK)
        surface.blit(label, (self.rect.x,
                             self.rect.centery - label.get_height() // 2))
        box = pygame.Rect(self.rect.right - 96, self.rect.y + 2, 96,
                          self.rect.height - 4)
        color = theme.STATE_FLAP if self.value else theme.BUTTON_BG
        pygame.draw.rect(surface, color, box, border_radius=theme.RADIUS_S)
        border = theme.FOCUS_RING if self.focused else theme.DARK_INK
        pygame.draw.rect(surface, border, box, 2,
                         border_radius=theme.RADIUS_S)
        text = self.on_text if self.value else self.off_text
        state = font.render(
            text, True,
            theme.DARK_INK if self.value else theme.TEXT_DIM_ON_DARK)
        surface.blit(state, state.get_rect(center=box.center))


class Slider(Widget):
    def __init__(self, rect: pygame.Rect, label: str,
                 min_value: float, max_value: float, value: float,
                 step: float, on_change: Callable[[float], None],
                 fmt: Callable[[float], str] = lambda v: f"{v:.2f}") -> None:
        super().__init__(rect)
        self.label = label
        self.min_value = min_value
        self.max_value = max_value
        self.value = value
        self.step = step
        self.on_change = on_change
        self.fmt = fmt
        self._dragging = False

    def _track_rect(self) -> pygame.Rect:
        return pygame.Rect(self.rect.right - 240,
                           self.rect.centery - 5, 190, 10)

    def _set_from_pos(self, x: int) -> None:
        track = self._track_rect()
        k = max(0.0, min(1.0, (x - track.x) / track.width))
        raw = self.min_value + k * (self.max_value - self.min_value)
        self._set_value(round(raw / self.step) * self.step)

    def _set_value(self, value: float) -> None:
        value = max(self.min_value, min(self.max_value, value))
        if abs(value - self.value) > 1e-9:
            self.value = value
            self.on_change(value)

    def handle_event(self, event: pygame.event.Event) -> bool:
        super().handle_event(event)
        if not self.enabled or not self.visible:
            return False
        track = self._track_rect().inflate(12, 16)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                and track.collidepoint(event.pos):
            self._dragging = True
            self._set_from_pos(event.pos[0])
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        if event.type == pygame.MOUSEMOTION and self._dragging:
            self._set_from_pos(event.pos[0])
            return True
        return False

    def adjust(self, direction: int) -> None:
        _play("menu_move")
        self._set_value(self.value + direction * self.step)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.visible:
            return
        label = font.render(self.label, True, theme.TEXT_ON_DARK)
        surface.blit(label, (self.rect.x,
                             self.rect.centery - label.get_height() // 2))
        track = self._track_rect()
        pygame.draw.rect(surface, theme.BUTTON_BG, track, border_radius=5)
        k = ((self.value - self.min_value)
             / max(1e-9, self.max_value - self.min_value))
        fill = track.copy()
        fill.width = int(track.width * k)
        pygame.draw.rect(surface, theme.MANGO, fill, border_radius=5)
        knob_x = track.x + int(track.width * k)
        knob = theme.FOCUS_RING if self.focused else theme.CREAM
        pygame.draw.circle(surface, theme.DARK_INK,
                           (knob_x, track.centery), 10)
        pygame.draw.circle(surface, knob, (knob_x, track.centery), 8)
        value_label = font.render(self.fmt(self.value), True,
                                  theme.TEXT_DIM_ON_DARK)
        surface.blit(value_label,
                     (track.right + 10,
                      track.centery - value_label.get_height() // 2))


class Selector(Widget):
    def __init__(self, rect: pygame.Rect, label: str,
                 options: Sequence[str], index: int,
                 on_change: Callable[[int], None]) -> None:
        super().__init__(rect)
        self.label = label
        self.options = list(options)
        self.index = max(0, min(index, len(self.options) - 1)) \
            if self.options else 0
        self.on_change = on_change

    def set_options(self, options: Sequence[str], index: int = 0) -> None:
        self.options = list(options)
        self.index = max(0, min(index, len(self.options) - 1)) \
            if self.options else 0

    def _shift(self, direction: int) -> None:
        if not self.options:
            return
        _play("menu_move")
        self.index = (self.index + direction) % len(self.options)
        self.on_change(self.index)

    def _arrow_rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        h = self.rect.height - 4
        box = pygame.Rect(self.rect.right - 246, self.rect.y + 2, 246, h)
        return (pygame.Rect(box.x, box.y, 30, h),
                pygame.Rect(box.right - 30, box.y, 30, h))

    def handle_event(self, event: pygame.event.Event) -> bool:
        super().handle_event(event)
        if not self.enabled or not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            left, right = self._arrow_rects()
            if left.collidepoint(event.pos):
                self._shift(-1)
                return True
            if right.collidepoint(event.pos):
                self._shift(1)
                return True
        return False

    def adjust(self, direction: int) -> None:
        self._shift(direction)

    def activate(self) -> None:
        self._shift(1)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.visible:
            return
        label = font.render(self.label, True, theme.TEXT_ON_DARK)
        surface.blit(label, (self.rect.x,
                             self.rect.centery - label.get_height() // 2))
        left, right = self._arrow_rects()
        box = left.union(right)
        pygame.draw.rect(surface, theme.BUTTON_BG, box,
                         border_radius=theme.RADIUS_S)
        border = theme.FOCUS_RING if self.focused else theme.DARK_INK
        pygame.draw.rect(surface, border, box, 2,
                         border_radius=theme.RADIUS_S)
        for arrow_rect, char in ((left, "<"), (right, ">")):
            arrow = font.render(char, True, theme.MANGO)
            surface.blit(arrow, arrow.get_rect(center=arrow_rect.center))
        current = self.options[self.index] if self.options else "-"
        value = font.render(current, True, theme.TEXT_ON_DARK)
        surface.blit(value, value.get_rect(center=box.center))


class Label(Widget):
    focusable = False

    def __init__(self, rect: pygame.Rect, text: str,
                 color=theme.TEXT_DIM_ON_DARK, center: bool = False) -> None:
        super().__init__(rect)
        self.text = text
        self.color = color
        self.center = center

    def handle_event(self, event: pygame.event.Event) -> bool:
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.visible:
            return
        label = font.render(self.text, True, self.color)
        if self.center:
            surface.blit(label, label.get_rect(center=self.rect.center))
        else:
            surface.blit(label, (self.rect.x, self.rect.y))


class TabBar(Widget):
    """Thanh tab ngang (Settings). Left/Right hoac click de doi tab."""

    def __init__(self, rect: pygame.Rect, tabs: Sequence[str], index: int,
                 on_change: Callable[[int], None]) -> None:
        super().__init__(rect)
        self.tabs = list(tabs)
        self.index = index
        self.on_change = on_change

    def _tab_rect(self, i: int) -> pygame.Rect:
        w = self.rect.width // max(1, len(self.tabs))
        return pygame.Rect(self.rect.x + i * w, self.rect.y, w,
                           self.rect.height)

    def _select(self, i: int) -> None:
        if i != self.index:
            _play("menu_move")
            self.index = i
            self.on_change(i)

    def handle_event(self, event: pygame.event.Event) -> bool:
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(len(self.tabs)):
                if self._tab_rect(i).collidepoint(event.pos):
                    self._select(i)
                    return True
        return False

    def adjust(self, direction: int) -> None:
        self._select((self.index + direction) % len(self.tabs))

    def activate(self) -> None:
        self._select((self.index + 1) % len(self.tabs))

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        for i, name in enumerate(self.tabs):
            rect = self._tab_rect(i)
            active = i == self.index
            color = theme.MANGO if active else theme.BUTTON_BG
            pygame.draw.rect(surface, color, rect.inflate(-6, 0),
                             border_radius=theme.RADIUS_S)
            if self.focused and active:
                pygame.draw.rect(surface, theme.FOCUS_RING,
                                 rect.inflate(-6, 0), 2,
                                 border_radius=theme.RADIUS_S)
            text = font.render(
                name, True,
                theme.DARK_INK if active else theme.TEXT_DIM_ON_DARK)
            surface.blit(text, text.get_rect(center=rect.center))


class ConfirmDialog:
    def __init__(self, message: str, yes_text: str, no_text: str,
                 on_yes: Callable[[], None]) -> None:
        self.message = message
        self.on_yes = on_yes
        self.open = True
        w, h = 460, 190
        screen = pygame.display.get_surface()
        sw, sh = screen.get_size() if screen else (1000, 700)
        self.rect = pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)
        self.yes_btn = Button(
            pygame.Rect(self.rect.x + 60, self.rect.bottom - 66, 150, 44),
            yes_text, self._confirm)
        self.no_btn = Button(
            pygame.Rect(self.rect.right - 210, self.rect.bottom - 66,
                        150, 44), no_text, self._close, primary=True)
        self.no_btn.focused = True
        self._focus_yes = False

    def _confirm(self) -> None:
        self.open = False
        self.on_yes()

    def _close(self) -> None:
        self.open = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close()
                return
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
                self._focus_yes = not self._focus_yes
                self.yes_btn.focused = self._focus_yes
                self.no_btn.focused = not self._focus_yes
                return
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                (self.yes_btn if self._focus_yes else self.no_btn).activate()
                return
        self.yes_btn.handle_event(event)
        self.no_btn.handle_event(event)

    def update(self, dt: float) -> None:
        self.yes_btn.update(dt)
        self.no_btn.update(dt)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        pygame.draw.rect(surface, theme.PANEL_DARK, self.rect,
                         border_radius=theme.RADIUS_M)
        pygame.draw.rect(surface, theme.MANGO, self.rect, 2,
                         border_radius=theme.RADIUS_M)
        msg = font.render(self.message, True, theme.TEXT_ON_DARK)
        surface.blit(msg, msg.get_rect(
            center=(self.rect.centerx, self.rect.y + 55)))
        self.yes_btn.draw(surface, font)
        self.no_btn.draw(surface, font)


class WidgetScreen:
    """Man hinh menu: quan ly widget + focus ban phim + dialog."""

    def __init__(self) -> None:
        self.widgets: list[Widget] = []
        self.dialog: Optional[ConfirmDialog] = None
        self._focus_index = -1

    def _focusables(self) -> list[Widget]:
        return [w for w in self.widgets
                if w.focusable and w.enabled and w.visible]

    def _move_focus(self, direction: int) -> None:
        items = self._focusables()
        if not items:
            return
        _play("menu_move")
        current = None
        for i, w in enumerate(items):
            if w.focused:
                current = i
                break
        for w in items:
            w.focused = False
        if current is None:
            new = 0 if direction > 0 else len(items) - 1
        else:
            new = (current + direction) % len(items)
        items[new].focused = True
        self._focus_index = new

    def _focused_widget(self) -> Optional[Widget]:
        for w in self._focusables():
            if w.focused:
                return w
        return None

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.dialog is not None and self.dialog.open:
            self.dialog.handle_event(event)
            if not self.dialog.open:
                self.dialog = None
            return True

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_TAB):
                self._move_focus(1)
                return True
            if event.key == pygame.K_UP:
                self._move_focus(-1)
                return True
            focused = self._focused_widget()
            if focused is not None:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    focused.activate()
                    return True
                if event.key == pygame.K_LEFT:
                    focused.adjust(-1)
                    return True
                if event.key == pygame.K_RIGHT:
                    focused.adjust(1)
                    return True

        handled = False
        for widget in list(self.widgets):
            if widget.handle_event(event):
                handled = True
                break
        if event.type == pygame.MOUSEBUTTONDOWN:
            for w in self._focusables():
                w.focused = w.rect.collidepoint(event.pos)
        return handled

    def update(self, dt: float) -> None:
        for widget in self.widgets:
            widget.update(dt)
        if self.dialog is not None:
            self.dialog.update(dt)

    def draw_widgets(self, surface: pygame.Surface,
                     font: pygame.font.Font) -> None:
        for widget in self.widgets:
            widget.draw(surface, font)
        if self.dialog is not None and self.dialog.open:
            self.dialog.draw(surface, font)
