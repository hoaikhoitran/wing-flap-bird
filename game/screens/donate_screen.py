"""Man hinh Support Developer: hien anh QR nhan tien (neu co) + link donate.

Quy tac voi anh QR (assets/support/vietqr-support.png):
  - Anh la ban CROP nguyen ban tu poster MBBank cua developer
    (scripts/crop_support_qr.py) - KHONG duoc tao lai / ve de / decode.
  - Giu nguyen aspect ratio; scale bang pygame.transform.smoothscale
    voi CUNG mot he so cho ca 2 chieu (QR luon vuong, khong meo).
  - Nen trang phia sau; khong button/text/overlay nao de len anh.
  - Khong animate / rotate / doi transparency.
  - Thieu anh -> fallback text, KHONG crash.

Quy tac link (core/links.py): DONATE_URL rong -> nut mo bi disable;
chi mo trinh duyet khi nguoi dung CHU DONG bam.
"""
from __future__ import annotations

import logging
import webbrowser
from typing import TYPE_CHECKING, Optional

import pygame

import config
from core import links
from core.paths import resource_path
from game.i18n import tr
from game.widgets import (COL_PANEL, COL_TEXT, COL_TEXT_DIM, Button,
                          WidgetScreen)

if TYPE_CHECKING:
    from game.game import Game

logger = logging.getLogger(__name__)

# Vung danh rieng cho anh QR (ben trai man hinh) - khong widget nao cham vao
_QR_MAX_W = 360
_QR_MAX_H = 500
_QR_PANEL_PAD = 14


def _wrap_text(text: str, font: pygame.font.Font,
               max_width: int) -> list[str]:
    """Ngat dong don gian theo chieu rong pixel."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if font.size(trial)[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class DonateScreen(WidgetScreen):
    def __init__(self, game: "Game") -> None:
        super().__init__()
        self.game = game
        self._qr_raw: Optional[pygame.Surface] = None
        self._qr_scaled: Optional[pygame.Surface] = None
        self._load_qr()
        self._build()

    # ------------------------------------------------------------------
    def _load_qr(self) -> None:
        """Load anh QR mot lan; thieu file / file hong -> fallback text."""
        try:
            path = resource_path(links.SUPPORT_QR_RESOURCE)
            if not path.exists():
                self._qr_raw = None
                return
            raw = pygame.image.load(str(path))
            try:
                raw = raw.convert()
            except pygame.error:
                pass  # chua co display mode - dung surface goc
            self._qr_raw = raw
            # Scale MOT he so duy nhat cho ca 2 chieu -> khong keo meo
            w, h = raw.get_size()
            scale = min(_QR_MAX_W / w, _QR_MAX_H / h, 1.0)
            size = (max(1, int(w * scale)), max(1, int(h * scale)))
            self._qr_scaled = pygame.transform.smoothscale(raw, size)
        except Exception as exc:
            logger.warning("Khong load duoc anh QR ung ho: %s", exc)
            self._qr_raw = None
            self._qr_scaled = None

    @property
    def _has_qr(self) -> bool:
        return self._qr_scaled is not None

    # ------------------------------------------------------------------
    def _build(self) -> None:
        self.widgets.clear()
        if self._has_qr:
            # Anh QR chiem nua trai -> button nam o cot phai, khong de anh
            bx, bw = 560, 340
        else:
            bx, bw = config.WINDOW_WIDTH // 2 - 170, 340
        open_btn = Button(
            pygame.Rect(bx, 470, bw, 50), tr("donate.open"),
            self._open_donate)
        open_btn.enabled = links.donate_available()
        self.widgets.append(open_btn)
        self.widgets.append(Button(
            pygame.Rect(bx, 534, bw, 50), tr("settings.back"),
            lambda: self.game.change_state_by_name("MAIN_MENU")))

    def on_enter(self) -> None:
        if self._qr_raw is None:
            self._load_qr()  # thu lai (VD developer vua them file)
        self._build()

    @staticmethod
    def _open_donate() -> None:
        if links.donate_available():
            webbrowser.open(links.DONATE_URL)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.change_state_by_name("MAIN_MENU")
            return True
        return False

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 22, 34))
        ui = self.game.ui
        cx = config.WINDOW_WIDTH // 2

        ui._text_outline(surface, tr("donate.title"), ui.font_big,
                         (cx, 52), color=(255, 220, 80))

        if self._has_qr:
            self._draw_with_qr(surface, ui)
        else:
            self._draw_text_only(surface, ui)

        self.draw_widgets(surface, ui.font_medium)

    def _draw_with_qr(self, surface: pygame.Surface, ui) -> None:
        qr = self._qr_scaled
        qw, qh = qr.get_size()
        # Panel NEN TRANG sau anh QR (yeu cau de app ngan hang de quet)
        panel = pygame.Rect(0, 0, qw + 2 * _QR_PANEL_PAD,
                            qh + 2 * _QR_PANEL_PAD)
        panel.center = (270, 380)
        pygame.draw.rect(surface, (255, 255, 255), panel, border_radius=12)
        surface.blit(qr, qr.get_rect(center=panel.center))

        # Goi y quet ma (nam DUOI anh, khong de len)
        hint = ui.font_medium.render(tr("donate.scan_hint"), True, COL_TEXT)
        surface.blit(hint, hint.get_rect(
            midtop=(panel.centerx, panel.bottom + 10)))

        # Cot phai: noi dung donate
        text_x, text_w = 560, 380
        y = 140
        for key in ("donate.body1", "donate.body2", "donate.body3"):
            for line in _wrap_text(tr(key), ui.font_medium, text_w):
                label = ui.font_medium.render(line, True, COL_TEXT)
                surface.blit(label, (text_x, y))
                y += 30
            y += 14
        if not links.donate_available():
            for line in _wrap_text(tr("donate.missing"), ui.font_small,
                                   text_w):
                label = ui.font_small.render(line, True, COL_TEXT_DIM)
                surface.blit(label, (text_x, y))
                y += 22

    def _draw_text_only(self, surface: pygame.Surface, ui) -> None:
        cx = config.WINDOW_WIDTH // 2
        panel = pygame.Rect(cx - 400, 110, 800, 330)
        pygame.draw.rect(surface, COL_PANEL, panel, border_radius=14)
        y = 190
        for key in ("donate.body1", "donate.body2", "donate.body3"):
            for line in _wrap_text(tr(key), ui.font_medium, 720):
                label = ui.font_medium.render(line, True, COL_TEXT)
                surface.blit(label, label.get_rect(center=(cx, y)))
                y += 34
            y += 10
        if not links.donate_available():
            note = ui.font_small.render(tr("donate.missing"), True,
                                        COL_TEXT_DIM)
            surface.blit(note, note.get_rect(center=(cx, y + 6)))
