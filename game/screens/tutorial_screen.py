"""Man hinh HOW TO PLAY: cac buoc choi + hinh minh hoa nguoi que
dang vo canh (ve bang Pygame primitives, khong dung asset ban quyen)
+ nut chay calibration + nut test cu chi truc tiep khong can vao gameplay.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

import config
from game.i18n import tr
from game.widgets import (COL_GREEN, COL_PANEL, COL_TEXT, COL_TEXT_DIM,
                          Button, WidgetScreen)

if TYPE_CHECKING:
    from game.game import Game


class TutorialScreen(WidgetScreen):
    def __init__(self, game: "Game") -> None:
        super().__init__()
        self.game = game
        self.testing = False
        self._time = 0.0
        self._flash_age = 999.0
        self._build()

    def _build(self) -> None:
        self.widgets.clear()
        x, y, w, h, gap = 60, 520, 270, 48, 16
        self.widgets.append(Button(
            pygame.Rect(x, y, w, h), tr("howto.run_calibration"),
            self._run_calibration))
        self._test_btn = Button(
            pygame.Rect(x + w + gap, y, w, h),
            tr("howto.stop_test") if self.testing else tr("howto.test_gesture"),
            self._toggle_test)
        self.widgets.append(self._test_btn)
        self.widgets.append(Button(
            pygame.Rect(x + 2 * (w + gap), y, w, h), tr("settings.back"),
            self._back))

    def on_enter(self) -> None:
        self.testing = False
        self._build()

    def on_leave(self) -> None:
        if self.testing:
            self.testing = False
            self.game.stop_vision_if_idle()

    # ------------------------------------------------------------------
    def _run_calibration(self) -> None:
        self.testing = False
        self.game.request_calibration(return_to="HOW_TO_PLAY")

    def _toggle_test(self) -> None:
        if self.testing:
            self.testing = False
            self.game.stop_vision_if_idle()
        else:
            self.testing = self.game.ensure_vision()
        self._test_btn.label = (tr("howto.stop_test") if self.testing
                                else tr("howto.test_gesture"))

    def _back(self) -> None:
        self.game.change_state_by_name("MAIN_MENU")

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return True
        return False

    def update(self, dt: float) -> None:
        super().update(dt)
        self._time += dt
        self._flash_age += dt
        if self.testing and self.game.vision is not None:
            # Flap trong che do test: chi nhay hieu ung + dem, khong vao game
            if self.game.vision.consume_flaps() > 0:
                self._flash_age = 0.0
                self.game.sound.play("flap")

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 22, 34))
        ui = self.game.ui
        cx = config.WINDOW_WIDTH // 2
        ui._text_outline(surface, tr("howto.title"), ui.font_big, (cx, 46),
                         color=(255, 220, 80))

        # Cot trai: cac buoc
        panel = pygame.Rect(50, 90, 560, 400)
        pygame.draw.rect(surface, COL_PANEL, panel, border_radius=14)
        steps = [tr(f"howto.step{i}") for i in range(1, 7)]
        y = panel.y + 30
        for step in steps:
            label = ui.font_medium.render(step, True, COL_TEXT)
            surface.blit(label, (panel.x + 28, y))
            y += 46
        fallback = ui.font_small.render(tr("howto.fallback"), True,
                                        COL_TEXT_DIM)
        surface.blit(fallback, (panel.x + 28, y + 12))

        # Cot phai: minh hoa nguoi que vo canh HOAC webcam khi dang test
        right = pygame.Rect(640, 90, 310, 400)
        pygame.draw.rect(surface, COL_PANEL, right, border_radius=14)
        if self.testing and self.game.vision is not None:
            self._draw_test_panel(surface, right, ui)
        else:
            self._draw_stick_figure(surface, right, ui)

        self.draw_widgets(surface, ui.font_medium)

    def _draw_stick_figure(self, surface: pygame.Surface,
                           area: pygame.Rect, ui) -> None:
        """Nguoi que minh hoa chu ky vo canh: thap -> cao -> thap."""
        cx = area.centerx
        cy = area.y + 190
        # Chu ky 2 giay: 0..0.5 nang len, 0.5..1.0 ha xuong
        phase = (self._time % 2.0) / 2.0
        lift = math.sin(phase * math.pi)          # 0 -> 1 -> 0
        arm_angle = math.radians(35 + 100 * lift)  # 35deg (thap) -> 135 (cao)

        white = (240, 244, 250)
        pygame.draw.circle(surface, white, (cx, cy - 95), 26, 4)      # dau
        pygame.draw.line(surface, white, (cx, cy - 69), (cx, cy + 30), 4)
        for leg_dx in (-28, 28):                                      # chan
            pygame.draw.line(surface, white, (cx, cy + 30),
                             (cx + leg_dx, cy + 95), 4)
        arm_len = 72
        shoulder = (cx, cy - 50)
        for side in (-1, 1):                                          # tay
            dx = side * arm_len * math.cos(arm_angle)
            dy = -arm_len * math.sin(arm_angle) + 20
            wrist = (shoulder[0] + dx, shoulder[1] + dy)
            pygame.draw.line(surface, (255, 175, 45), shoulder, wrist, 5)
            pygame.draw.circle(surface, (235, 80, 70),
                               (int(wrist[0]), int(wrist[1])), 8)

        # Nhan trang thai theo pha
        if lift > 0.75:
            label_key, color = "hud.arms_up", (255, 175, 45)
        elif phase > 0.5 and lift < 0.35:
            label_key, color = "hud.flap", COL_GREEN
        else:
            label_key, color = "hud.arms_down", (80, 150, 255)
        ui._text_outline(surface, tr(label_key), ui.font_medium,
                         (cx, area.bottom - 40), color=color)

    def _draw_test_panel(self, surface: pygame.Surface,
                         area: pygame.Rect, ui) -> None:
        """Test cu chi: webcam + trang thai + dem so lan vo."""
        snap = self.game.vision.snapshot()
        cam_rect = pygame.Rect(area.x + 15, area.y + 15,
                               area.width - 30, 210)
        frame = ui.frame_to_surface(snap.frame_rgb)
        if frame is not None:
            surface.blit(pygame.transform.scale(frame, cam_rect.size),
                         cam_rect)
        else:
            pygame.draw.rect(surface, (35, 35, 45), cam_rect)
            msg = ui.font_small.render(snap.camera_message, True,
                                       COL_TEXT_DIM)
            surface.blit(msg, msg.get_rect(center=cam_rect.center))
        border = COL_GREEN if self._flash_age < 0.3 else (90, 100, 125)
        pygame.draw.rect(surface, border, cam_rect,
                         5 if self._flash_age < 0.3 else 2)

        from game.ui import _STATE_LABEL_KEYS
        state_text = tr(_STATE_LABEL_KEYS.get(snap.detector_state,
                                              "hud.no_pose"))
        if self._flash_age < 0.3:
            state_text = tr("hud.flap")
        ui._text_outline(surface, state_text, ui.font_medium,
                         (area.centerx, cam_rect.bottom + 35))
        ui._text_outline(surface,
                         tr("howto.flap_count", n=snap.flap_total),
                         ui.font_medium,
                         (area.centerx, cam_rect.bottom + 75),
                         color=(255, 220, 80))
