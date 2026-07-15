"""HUD + cac thanh phan ve dung chung (khong con Background - xem
game/background.py). Toan bo text render qua core.font_manager
(Be Vietnam Pro, NFC) - khong dung font he thong.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pygame

import config
from core import font_manager as fm
from game import theme
from game.assets import assets
from game.i18n import tr
from vision.vision_system import VisionSnapshot

# Mau vien webcam theo trang thai detector
_STATE_COLORS = {
    "NO_POSE": theme.STATE_NO_POSE,
    "ARMS_DOWN": theme.STATE_ARMS_DOWN,
    "ARMS_UP": theme.STATE_ARMS_UP,
    "FLAP_CONFIRMED": theme.STATE_FLAP,
}
_STATE_LABEL_KEYS = {
    "NO_POSE": "hud.no_pose",
    "ARMS_DOWN": "hud.arms_down",
    "ARMS_UP": "hud.arms_up",
    "FLAP_CONFIRMED": "hud.flap",
}


class UI:
    """Cac thao tac ve HUD/overlay. Font lay tu font_manager (co cache)."""

    # ------------------------------------------------------------------
    # Font (giu ten thuoc tinh cu de screens dung chung)
    # ------------------------------------------------------------------
    @property
    def font_small(self) -> pygame.font.Font:
        return fm.get("caption")

    @property
    def font_medium(self) -> pygame.font.Font:
        return fm.get("body")

    @property
    def font_button(self) -> pygame.font.Font:
        return fm.get("button")

    @property
    def font_big(self) -> pygame.font.Font:
        return fm.get("title")

    @property
    def font_huge(self) -> pygame.font.Font:
        return fm.get("display")

    @property
    def font_score(self) -> pygame.font.Font:
        return fm.get("score")

    # ------------------------------------------------------------------
    def _text_outline(self, surface: pygame.Surface, text: str,
                      font_or_role, center: tuple[int, int],
                      color=theme.TEXT_ON_DARK,
                      outline=theme.DARK_INK, size: int | None = None,
                      ) -> None:
        role = font_or_role if isinstance(font_or_role, str) else None
        if role is None:
            # tuong thich cu: nhan pygame.font.Font -> suy ra role theo size
            h = font_or_role.get_height()
            role = ("display" if h > 48 else "title" if h > 28
                    else "body")
        label = fm.render_outlined(role, text, color, outline, size=size)
        surface.blit(label, label.get_rect(center=center))

    @staticmethod
    def frame_to_surface(frame_rgb: Optional[np.ndarray]
                         ) -> Optional[pygame.Surface]:
        if frame_rgb is None:
            return None
        try:
            h, w = frame_rgb.shape[:2]
            return pygame.image.frombuffer(frame_rgb.tobytes(), (w, h),
                                           "RGB")
        except Exception:
            return None

    # ------------------------------------------------------------------
    # HUD gameplay
    # ------------------------------------------------------------------
    def draw_score(self, surface: pygame.Surface, score: int,
                   high_score: int, pop: float = 0.0) -> None:
        """Score lon co pop animation (pop 0..1 vua ghi diem)."""
        size = int(52 * (1.0 + 0.35 * pop))
        label = fm.render_outlined("score", str(score),
                                   theme.CREAM, theme.DARK_INK,
                                   size=size, thickness=3)
        surface.blit(label, label.get_rect(
            center=(config.WINDOW_WIDTH // 2, 56)))
        best = fm.render_outlined("caption",
                                  tr("hud.best", score=high_score),
                                  theme.TEXT_ACCENT, theme.DARK_INK)
        surface.blit(best, best.get_rect(
            center=(config.WINDOW_WIDTH // 2, 100)))

    def draw_fps(self, surface: pygame.Surface, game_fps: float,
                 vision_fps: float) -> None:
        text = tr("hud.fps", game=game_fps, cam=vision_fps)
        label = fm.render("caption", text, theme.TEXT_ON_DARK)
        bg = pygame.Surface((label.get_width() + 12,
                             label.get_height() + 6), pygame.SRCALPHA)
        bg.fill((*theme.DARK_INK, 140))
        surface.blit(bg, (8, config.WINDOW_HEIGHT - 30))
        surface.blit(label, (14, config.WINDOW_HEIGHT - 27))

    def draw_flap_text(self, surface: pygame.Surface, x: float, y: float,
                       age: float) -> None:
        k = age / config.FLAP_TEXT_DURATION
        if k >= 1.0:
            return
        label = fm.render_outlined("title", tr("hud.flap"),
                                   theme.MANGO, theme.DARK_INK)
        label.set_alpha(int(255 * (1.0 - k)))
        surface.blit(label, (int(x + 34), int(y - 40 - 34.0 * k)))

    # ------------------------------------------------------------------
    # Webcam panel
    # ------------------------------------------------------------------
    def webcam_panel_rect(self) -> pygame.Rect:
        return pygame.Rect(
            config.WINDOW_WIDTH - config.WEBCAM_PANEL_WIDTH
            - config.WEBCAM_PANEL_MARGIN,
            config.WEBCAM_PANEL_MARGIN,
            config.WEBCAM_PANEL_WIDTH, config.WEBCAM_PANEL_HEIGHT,
        )

    def draw_webcam_panel(self, surface: pygame.Surface,
                          snap: VisionSnapshot,
                          flap_flash_age: float) -> None:
        rect = self.webcam_panel_rect()
        flashing = flap_flash_age < config.WEBCAM_FLASH_DURATION
        border_color = (theme.STATE_FLAP if flashing
                        else _STATE_COLORS.get(snap.detector_state,
                                               theme.STATE_NO_POSE))

        frame_surf = self.frame_to_surface(snap.frame_rgb)
        if frame_surf is not None:
            # Giu dung aspect: frame 4:3, panel 4:3 -> scale thang
            surface.blit(pygame.transform.scale(frame_surf, rect.size),
                         rect)
        else:
            pygame.draw.rect(surface, theme.PANEL_DARK, rect,
                             border_radius=theme.RADIUS_S)
            msg = fm.render("caption", tr("hud.no_signal"),
                            theme.TEXT_DIM_ON_DARK)
            surface.blit(msg, msg.get_rect(center=rect.center))

        pygame.draw.rect(surface, border_color, rect,
                         5 if flashing else 3,
                         border_radius=theme.RADIUS_S)

        # Nhan trang thai
        if not snap.camera_ok:
            label_text, label_color = tr("hud.no_webcam"), theme.VERMILION
        elif flashing:
            label_text, label_color = tr("hud.flap"), theme.STATE_FLAP
        else:
            label_text = tr(_STATE_LABEL_KEYS.get(snap.detector_state,
                                                  "hud.no_pose"))
            label_color = border_color
        label = fm.render("caption", label_text, label_color)
        label_bg = pygame.Surface((label.get_width() + 14,
                                   label.get_height() + 6), pygame.SRCALPHA)
        label_bg.fill((*theme.DARK_INK, 170))
        bg_rect = label_bg.get_rect(midtop=(rect.centerx, rect.bottom + 6))
        surface.blit(label_bg, bg_rect)
        surface.blit(label, label.get_rect(center=bg_rect.center))

        # Thanh cooldown - style thanh nang luong (khong giong debug tool)
        bar = pygame.Rect(rect.x + 4, bg_rect.bottom + 6,
                          rect.width - 8, 8)
        cooldown = max(snap.flap_cooldown, 1e-6)
        ready = 1.0 - min(1.0, snap.cooldown_remaining / cooldown)
        pygame.draw.rect(surface, theme.PANEL_DARK, bar, border_radius=4)
        fill = bar.copy()
        fill.width = max(0, int(bar.width * ready))
        pygame.draw.rect(surface,
                         theme.STATE_FLAP if ready >= 1.0 else theme.MANGO,
                         fill, border_radius=4)

    def draw_camera_warning(self, surface: pygame.Surface,
                            message: str) -> None:
        text = tr("hud.camera_warning", msg=message)
        label = fm.render("body", text, theme.TEXT_ON_DARK)
        bg = pygame.Surface((label.get_width() + 24,
                             label.get_height() + 12), pygame.SRCALPHA)
        bg.fill((*theme.VERMILION, 225))
        rect = bg.get_rect(midtop=(config.WINDOW_WIDTH // 2, 130))
        surface.blit(bg, rect)
        surface.blit(label, label.get_rect(center=rect.center))

    # ------------------------------------------------------------------
    # GET_READY / GO
    # ------------------------------------------------------------------
    def draw_get_ready(self, surface: pygame.Surface, countdown: str,
                       time_left: float, total: float) -> None:
        self._text_outline(surface, tr("ready.title"), "title",
                           (config.WINDOW_WIDTH // 2, 150),
                           color=theme.MANGO)
        self._text_outline(surface, tr("ready.instruction"), "title",
                           (config.WINDOW_WIDTH // 2, 200))
        segment = max(total / 3.0, 1e-6)
        frac = (time_left % segment) / segment
        size = int(110 * (1.0 + 0.35 * frac)) // 4 * 4
        self._text_outline(surface, countdown, "display",
                           (config.WINDOW_WIDTH // 2,
                            config.WINDOW_HEIGHT // 2 - 20),
                           color=theme.MANGO, size=size)

    def draw_go(self, surface: pygame.Surface, age: float) -> None:
        k = min(1.0, age / config.GO_TEXT_DURATION)
        size = int(90 + 50 * k) // 4 * 4
        label = fm.render_outlined("display", "GO!", theme.STATE_FLAP,
                                   theme.DARK_INK, size=size)
        label.set_alpha(int(255 * (1.0 - k)))
        surface.blit(label, label.get_rect(
            center=(config.WINDOW_WIDTH // 2,
                    config.WINDOW_HEIGHT // 2 - 20)))

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------
    def draw_calibration(self, surface: pygame.Surface,
                         snap: VisionSnapshot, message: str,
                         progress: float,
                         hint: Optional[str] = None) -> None:
        surface.fill(theme.BG_MENU)
        cx = config.WINDOW_WIDTH // 2
        self._text_outline(surface, tr("calib.title"), "title", (cx, 44),
                           color=theme.MANGO)

        cam_w, cam_h = 560, 420  # 4:3 - dung aspect webcam
        cam_rect = pygame.Rect(cx - cam_w // 2, 80, cam_w, cam_h)
        frame_surf = self.frame_to_surface(snap.frame_rgb)
        if frame_surf is not None:
            surface.blit(pygame.transform.scale(frame_surf, cam_rect.size),
                         cam_rect)
        else:
            pygame.draw.rect(surface, theme.PANEL_DARK, cam_rect,
                             border_radius=theme.RADIUS_M)
            msg = fm.render("body", snap.camera_message,
                            theme.TEXT_DIM_ON_DARK)
            surface.blit(msg, msg.get_rect(center=cam_rect.center))
        state_color = _STATE_COLORS.get(snap.detector_state,
                                        theme.STATE_NO_POSE)
        pygame.draw.rect(surface, state_color, cam_rect, 4,
                         border_radius=theme.RADIUS_M)

        self._text_outline(surface, message, "heading",
                           (cx, cam_rect.bottom + 34))
        bar = pygame.Rect(cx - 220, cam_rect.bottom + 62, 440, 18)
        pygame.draw.rect(surface, theme.PANEL_DARK, bar, border_radius=9)
        fill = bar.copy()
        fill.width = int(bar.width * progress)
        pygame.draw.rect(surface, theme.STATE_FLAP, fill, border_radius=9)

        # Canh bao dat NGAY canh preview
        if hint:
            self._text_outline(surface, hint, "body",
                               (cx, bar.bottom + 24),
                               color=theme.MANGO)
        self._text_outline(surface, tr("calib.hints"), "caption",
                           (cx, bar.bottom + 52),
                           color=theme.TEXT_DIM_ON_DARK)

    # ------------------------------------------------------------------
    # Debug overlay
    # ------------------------------------------------------------------
    def draw_debug(self, surface: pygame.Surface, snap: VisionSnapshot,
                   game_lines: Optional[list[str]] = None) -> None:
        lines: list[str] = list(game_lines or [])
        if lines:
            lines.append("-" * 30)
        lines += [
            f"state       : {snap.debug.get('state', snap.detector_state)}",
            f"wrist L/R y : {snap.debug.get('lw_y', '-')} / "
            f"{snap.debug.get('rw_y', '-')}",
            f"vel L/R     : {snap.debug.get('vel_lw', '-')} / "
            f"{snap.debug.get('vel_rw', '-')}",
            f"visibility  : {snap.debug.get('visibility', '-')}",
            f"cooldown    : {snap.debug.get('cooldown', '-')}",
            f"flaps       : {snap.debug.get('flaps', '0')}",
        ]
        pad = 8
        font = fm.get("debug")
        height = len(lines) * 18 + pad * 2
        panel = pygame.Surface((300, height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 165))
        for i, line in enumerate(lines):
            panel.blit(font.render(line, True, (170, 255, 170)),
                       (pad, pad + i * 18))
        surface.blit(panel, (8, 120))
