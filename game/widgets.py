"""He thong widget tai su dung cho menu: Button, Toggle, Slider, Selector,
ConfirmDialog. Dieu khien duoc bang CA chuot lan ban phim:

  - Chuot: hover + click.
  - Ban phim: Up/Down (hoac Tab) di chuyen focus, Enter/Space kich hoat,
    Left/Right chinh gia tri (slider/selector).

Khong hard-code tung nut; moi man hinh chi khai bao danh sach widget.
"""
from __future__ import annotations

from typing import Callable, Optional, Sequence

import pygame

# Bang mau thong nhat cho toan bo UI
COL_PANEL = (28, 34, 48)
COL_BUTTON = (52, 62, 86)
COL_BUTTON_HOVER = (76, 92, 128)
COL_BUTTON_DISABLED = (40, 44, 54)
COL_FOCUS = (255, 210, 70)
COL_TEXT = (235, 238, 245)
COL_TEXT_DIM = (150, 156, 170)
COL_ACCENT = (255, 175, 45)
COL_GREEN = (70, 220, 110)
COL_RED = (235, 80, 70)


class Widget:
    """Lop co so: moi widget co rect, focus duoc (hoac khong), ve + xu ly event."""

    focusable = True

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.focused = False
        self.enabled = True
        self.visible = True
        self._hover = False
        self._hover_anim = 0.0  # 0..1, animation muot khi hover/focus

    # -- vong doi ------------------------------------------------------
    def update(self, dt: float) -> None:
        target = 1.0 if (self._hover or self.focused) and self.enabled else 0.0
        self._hover_anim += (target - self._hover_anim) * min(1.0, 12.0 * dt)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Tra ve True neu event da duoc widget xu ly."""
        if not self.enabled or not self.visible:
            return False
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        raise NotImplementedError

    def activate(self) -> None:
        """Kich hoat bang Enter/Space (ban phim)."""

    def adjust(self, direction: int) -> None:
        """Left/Right tren widget dang focus (slider/selector)."""


class Button(Widget):
    def __init__(self, rect: pygame.Rect, label: str,
                 on_click: Callable[[], None],
                 tooltip: str = "") -> None:
        super().__init__(rect)
        self.label = label
        self.on_click = on_click
        self.tooltip = tooltip

    def handle_event(self, event: pygame.event.Event) -> bool:
        super().handle_event(event)
        if not self.enabled or not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                and self.rect.collidepoint(event.pos):
            self.on_click()
            return True
        return False

    def activate(self) -> None:
        if self.enabled:
            self.on_click()

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.visible:
            return
        # Animation nhe: phong to 2px khi hover/focus
        grow = int(2 * self._hover_anim)
        rect = self.rect.inflate(grow * 2, grow)
        if not self.enabled:
            color = COL_BUTTON_DISABLED
        else:
            k = self._hover_anim
            color = tuple(int(COL_BUTTON[i]
                              + (COL_BUTTON_HOVER[i] - COL_BUTTON[i]) * k)
                          for i in range(3))
        pygame.draw.rect(surface, color, rect, border_radius=10)
        border = COL_FOCUS if self.focused else (90, 100, 125)
        pygame.draw.rect(surface, border, rect, 2, border_radius=10)
        text_color = COL_TEXT if self.enabled else COL_TEXT_DIM
        label = font.render(self.label, True, text_color)
        surface.blit(label, label.get_rect(center=rect.center))
        if self.tooltip and not self.enabled:
            tip_font = pygame.font.SysFont("arial", 13)
            tip = tip_font.render(self.tooltip, True, COL_TEXT_DIM)
            surface.blit(tip, tip.get_rect(
                midtop=(rect.centerx, rect.bottom + 4)))


class Toggle(Widget):
    """Cong tac BAT/TAT voi nhan mo ta ben trai."""

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
        label = font.render(self.label, True, COL_TEXT)
        surface.blit(label, (self.rect.x,
                             self.rect.centery - label.get_height() // 2))
        # Hop trang thai ben phai
        box = pygame.Rect(self.rect.right - 96, self.rect.y + 2, 96,
                          self.rect.height - 4)
        color = COL_GREEN if self.value else COL_BUTTON
        pygame.draw.rect(surface, color, box, border_radius=8)
        border = COL_FOCUS if self.focused else (90, 100, 125)
        pygame.draw.rect(surface, border, box, 2, border_radius=8)
        text = self.on_text if self.value else self.off_text
        state = font.render(text, True,
                            (20, 40, 25) if self.value else COL_TEXT_DIM)
        surface.blit(state, state.get_rect(center=box.center))


class Slider(Widget):
    """Thanh keo gia tri lien tuc (chuot keo / Left-Right chinh buoc)."""

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
                           self.rect.centery - 5, 200, 10)

    def _set_from_pos(self, x: int) -> None:
        track = self._track_rect()
        k = max(0.0, min(1.0, (x - track.x) / track.width))
        raw = self.min_value + k * (self.max_value - self.min_value)
        # Bam theo step de gia tri gon gang
        stepped = round(raw / self.step) * self.step
        self._set_value(stepped)

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
        self._set_value(self.value + direction * self.step)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.visible:
            return
        label = font.render(self.label, True, COL_TEXT)
        surface.blit(label, (self.rect.x,
                             self.rect.centery - label.get_height() // 2))
        track = self._track_rect()
        pygame.draw.rect(surface, COL_BUTTON, track, border_radius=5)
        k = ((self.value - self.min_value)
             / max(1e-9, self.max_value - self.min_value))
        fill = track.copy()
        fill.width = int(track.width * k)
        pygame.draw.rect(surface, COL_ACCENT, fill, border_radius=5)
        knob_x = track.x + int(track.width * k)
        knob_color = COL_FOCUS if self.focused else COL_TEXT
        pygame.draw.circle(surface, knob_color, (knob_x, track.centery), 9)
        value_label = font.render(self.fmt(self.value), True, COL_TEXT_DIM)
        surface.blit(value_label,
                     (track.right + 10,
                      track.centery - value_label.get_height() // 2))


class Selector(Widget):
    """Chon 1 trong N gia tri bang mui ten < > (chuot hoac Left/Right)."""

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
        self.index = (self.index + direction) % len(self.options)
        self.on_change(self.index)

    def _arrow_rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        h = self.rect.height - 4
        right_box = pygame.Rect(self.rect.right - 246, self.rect.y + 2,
                                246, h)
        left = pygame.Rect(right_box.x, right_box.y, 30, h)
        right = pygame.Rect(right_box.right - 30, right_box.y, 30, h)
        return left, right

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
        label = font.render(self.label, True, COL_TEXT)
        surface.blit(label, (self.rect.x,
                             self.rect.centery - label.get_height() // 2))
        left, right = self._arrow_rects()
        box = left.union(right)
        pygame.draw.rect(surface, COL_BUTTON, box, border_radius=8)
        border = COL_FOCUS if self.focused else (90, 100, 125)
        pygame.draw.rect(surface, border, box, 2, border_radius=8)
        for arrow_rect, char in ((left, "<"), (right, ">")):
            arrow = font.render(char, True, COL_ACCENT)
            surface.blit(arrow, arrow.get_rect(center=arrow_rect.center))
        current = self.options[self.index] if self.options else "-"
        value = font.render(current, True, COL_TEXT)
        surface.blit(value, value.get_rect(center=box.center))


class Label(Widget):
    """Dong chu tinh (khong focus duoc)."""

    focusable = False

    def __init__(self, rect: pygame.Rect, text: str,
                 color: tuple[int, int, int] = COL_TEXT_DIM,
                 center: bool = False) -> None:
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


class ConfirmDialog:
    """Hop thoai xac nhan modal (Yes/No). Ve de len tren man hinh."""

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
                        150, 44),
            no_text, self._close)
        self.no_btn.focused = True  # mac dinh focus NO cho an toan
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
        pygame.draw.rect(surface, COL_PANEL, self.rect, border_radius=12)
        pygame.draw.rect(surface, COL_ACCENT, self.rect, 2, border_radius=12)
        msg = font.render(self.message, True, COL_TEXT)
        surface.blit(msg, msg.get_rect(
            center=(self.rect.centerx, self.rect.y + 55)))
        self.yes_btn.draw(surface, font)
        self.no_btn.draw(surface, font)


class WidgetScreen:
    """Nen tang man hinh menu: quan ly danh sach widget + focus ban phim."""

    def __init__(self) -> None:
        self.widgets: list[Widget] = []
        self.dialog: Optional[ConfirmDialog] = None
        self._focus_index = -1

    # -- focus ---------------------------------------------------------
    def _focusables(self) -> list[Widget]:
        return [w for w in self.widgets
                if w.focusable and w.enabled and w.visible]

    def _move_focus(self, direction: int) -> None:
        items = self._focusables()
        if not items:
            return
        current = None
        if 0 <= self._focus_index:
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

    # -- vong doi ------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Tra ve True neu event da duoc man hinh xu ly."""
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
        # Iterate tren ban sao: callback co the rebuild danh sach widget
        # (VD doi ngon ngu) ngay trong luc xu ly event
        for widget in list(self.widgets):
            if widget.handle_event(event):
                handled = True
                break
        # Click chuot -> chuyen focus theo hover
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
