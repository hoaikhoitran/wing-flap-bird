"""Toan bo phan ve UI: nen troi, HUD, khung webcam, menu, game over,
man hinh calibration va overlay debug.
"""
from __future__ import annotations

import random
from typing import Optional

import numpy as np
import pygame

import config
from vision.vision_system import VisionSnapshot

# ------------------------------------------------------------------
# Mau sac
# ------------------------------------------------------------------
_SKY_TOP = (105, 185, 240)
_SKY_BOTTOM = (185, 228, 250)
_GROUND_GRASS = (122, 195, 90)
_GROUND_DIRT = (222, 202, 138)
_GROUND_DIRT_DARK = (196, 172, 108)
_WHITE = (255, 255, 255)
_BLACK = (25, 25, 30)
_YELLOW = (255, 220, 80)
_RED = (235, 80, 70)
_GREEN = (70, 220, 110)

# Mau vien webcam theo trang thai detector
_STATE_COLORS = {
    "NO_POSE": (130, 130, 140),
    "ARMS_DOWN": (80, 150, 255),
    "ARMS_UP": (255, 175, 45),
    "FLAP_CONFIRMED": _GREEN,
}
_STATE_LABELS = {
    "NO_POSE": "KHÔNG NHẬN DIỆN ĐƯỢC",
    "ARMS_DOWN": "TAY THẤP",
    "ARMS_UP": "TAY CAO",
    "FLAP_CONFIRMED": "VỖ CÁNH!",
}


def _load_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Chon font he thong co ho tro tieng Viet (Arial co san tren Windows)."""
    for name in ("arial", "segoeui", "tahoma", "calibri"):
        try:
            font = pygame.font.SysFont(name, size, bold=bold)
            if font is not None:
                return font
        except Exception:
            continue
    return pygame.font.Font(None, size)


class Background:
    """Nen troi gradient (ve san 1 lan) + may troi + mat dat cuon."""

    def __init__(self) -> None:
        w, h = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        self._sky = pygame.Surface((w, h))
        for y in range(h):
            k = y / h
            color = tuple(int(_SKY_TOP[i] + (_SKY_BOTTOM[i] - _SKY_TOP[i]) * k)
                          for i in range(3))
            pygame.draw.line(self._sky, color, (0, y), (w, y))
        # May: (x, y, ti le, toc do)
        self._clouds = [
            [random.uniform(0, w), random.uniform(40, 260),
             random.uniform(0.6, 1.4), random.uniform(12, 30)]
            for _ in range(6)
        ]
        self._ground_scroll = 0.0

    def update(self, dt: float, scrolling: bool) -> None:
        w = config.WINDOW_WIDTH
        for cloud in self._clouds:
            cloud[0] -= cloud[3] * dt
            if cloud[0] < -160:
                cloud[0] = w + random.uniform(20, 120)
                cloud[1] = random.uniform(40, 260)
        if scrolling:
            self._ground_scroll = (self._ground_scroll
                                   + config.PIPE_SPEED * dt) % 48

    def draw_sky(self, surface: pygame.Surface) -> None:
        surface.blit(self._sky, (0, 0))
        for x, y, scale, _ in self._clouds:
            cw, ch = int(120 * scale), int(44 * scale)
            cloud = pygame.Surface((cw, ch), pygame.SRCALPHA)
            pygame.draw.ellipse(cloud, (255, 255, 255, 190), (0, ch // 3,
                                                              cw, ch // 2))
            pygame.draw.ellipse(cloud, (255, 255, 255, 190),
                                (cw // 5, 0, cw // 2, int(ch * 0.8)))
            pygame.draw.ellipse(cloud, (255, 255, 255, 190),
                                (cw // 2, ch // 6, cw // 3, int(ch * 0.7)))
            surface.blit(cloud, (int(x), int(y)))

    def draw_ground(self, surface: pygame.Surface) -> None:
        w, h = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        gh = config.GROUND_HEIGHT
        top = h - gh
        pygame.draw.rect(surface, _GROUND_DIRT, (0, top, w, gh))
        pygame.draw.rect(surface, _GROUND_GRASS, (0, top, w, 22))
        pygame.draw.line(surface, (86, 150, 62), (0, top + 22), (w, top + 22), 3)
        # Soc cheo cuon theo toc do game
        offset = int(self._ground_scroll)
        for x in range(-48, w + 48, 48):
            pygame.draw.polygon(surface, _GROUND_DIRT_DARK, [
                (x - offset, top + 34), (x - offset + 24, top + 34),
                (x - offset + 12, top + gh - 8),
                (x - offset - 12, top + gh - 8),
            ])


class UI:
    """Gom moi thao tac ve chu / panel / overlay len man hinh."""

    def __init__(self) -> None:
        self.font_small = _load_font(15)
        self.font_medium = _load_font(20)
        self.font_big = _load_font(30, bold=True)
        self.font_huge = _load_font(58, bold=True)
        self.font_score = _load_font(46, bold=True)
        # Cache cho font co kich thuoc thay doi theo animation (countdown, GO!)
        self._font_cache: dict[tuple[int, bool], pygame.font.Font] = {}

    def _sized_font(self, size: int, bold: bool = True) -> pygame.font.Font:
        """Font theo size dong, luong tu hoa buoc 4px de cache hieu qua."""
        size = max(8, (size // 4) * 4)
        key = (size, bold)
        if key not in self._font_cache:
            self._font_cache[key] = _load_font(size, bold)
        return self._font_cache[key]

    # ------------------------------------------------------------------
    # Tien ich
    # ------------------------------------------------------------------
    def _text_outline(self, surface: pygame.Surface, text: str,
                      font: pygame.font.Font, center: tuple[int, int],
                      color: tuple[int, int, int] = _WHITE,
                      outline: tuple[int, int, int] = _BLACK) -> None:
        base = font.render(text, True, color)
        shadow = font.render(text, True, outline)
        rect = base.get_rect(center=center)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            surface.blit(shadow, rect.move(dx, dy))
        surface.blit(base, rect)

    @staticmethod
    def frame_to_surface(frame_rgb: Optional[np.ndarray]
                         ) -> Optional[pygame.Surface]:
        """Chuyen frame numpy RGB tu vision thread thanh pygame Surface."""
        if frame_rgb is None:
            return None
        try:
            h, w = frame_rgb.shape[:2]
            return pygame.image.frombuffer(frame_rgb.tobytes(), (w, h), "RGB")
        except Exception:
            return None

    # ------------------------------------------------------------------
    # HUD trong luc choi
    # ------------------------------------------------------------------
    def draw_score(self, surface: pygame.Surface, score: int,
                   high_score: int) -> None:
        self._text_outline(surface, str(score), self.font_score,
                           (config.WINDOW_WIDTH // 2, 56))
        self._text_outline(surface, f"Kỷ lục: {high_score}", self.font_medium,
                           (config.WINDOW_WIDTH // 2, 100),
                           color=_YELLOW)

    def draw_fps(self, surface: pygame.Surface, game_fps: float,
                 vision_fps: float) -> None:
        text = f"FPS game: {game_fps:4.0f}   FPS camera: {vision_fps:4.0f}"
        label = self.font_small.render(text, True, _WHITE)
        bg = pygame.Surface((label.get_width() + 12, label.get_height() + 6),
                            pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        surface.blit(bg, (8, config.WINDOW_HEIGHT - 30))
        surface.blit(label, (14, config.WINDOW_HEIGHT - 27))

    def draw_flap_text(self, surface: pygame.Surface, x: float, y: float,
                       age: float) -> None:
        """Chu "FLAP!" bay len va mo dan sau moi lan vo canh."""
        k = age / config.FLAP_TEXT_DURATION
        if k >= 1.0:
            return
        offset_y = -34.0 * k
        label = self.font_big.render("FLAP!", True, _YELLOW)
        shadow = self.font_big.render("FLAP!", True, _BLACK)
        alpha = int(255 * (1.0 - k))
        label.set_alpha(alpha)
        shadow.set_alpha(alpha)
        pos = (int(x + 34), int(y - 40 + offset_y))
        surface.blit(shadow, (pos[0] + 2, pos[1] + 2))
        surface.blit(label, pos)

    # ------------------------------------------------------------------
    # Khung webcam
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

        # Mau vien: xanh la khi vua flap, con lai theo trang thai detector
        flashing = flap_flash_age < config.WEBCAM_FLASH_DURATION
        if flashing:
            border_color = _GREEN
        else:
            border_color = _STATE_COLORS.get(snap.detector_state,
                                             _STATE_COLORS["NO_POSE"])

        frame_surf = self.frame_to_surface(snap.frame_rgb)
        if frame_surf is not None:
            scaled = pygame.transform.scale(frame_surf, rect.size)
            surface.blit(scaled, rect)
        else:
            pygame.draw.rect(surface, (35, 35, 45), rect)
            msg = self.font_small.render("KHÔNG CÓ TÍN HIỆU", True,
                                         (200, 200, 210))
            surface.blit(msg, msg.get_rect(center=rect.center))

        pygame.draw.rect(surface, border_color, rect,
                         5 if flashing else 3)

        # Nhan trang thai nhan dien
        if not snap.camera_ok:
            label_text, label_color = "KHÔNG CÓ WEBCAM", _RED
        elif flashing:
            label_text, label_color = "VỖ CÁNH!", _GREEN
        else:
            label_text = _STATE_LABELS.get(snap.detector_state, "?")
            label_color = border_color
        label = self.font_medium.render(label_text, True, label_color)
        label_bg = pygame.Surface((label.get_width() + 14,
                                   label.get_height() + 6), pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 150))
        bg_rect = label_bg.get_rect(midtop=(rect.centerx, rect.bottom + 6))
        surface.blit(label_bg, bg_rect)
        surface.blit(label, label.get_rect(center=bg_rect.center))

        # Thanh cooldown: day = san sang flap tiep
        bar_rect = pygame.Rect(rect.x, bg_rect.bottom + 6, rect.width, 10)
        cooldown = max(snap.flap_cooldown, 1e-6)
        ready_frac = 1.0 - min(1.0, snap.cooldown_remaining / cooldown)
        pygame.draw.rect(surface, (40, 40, 50), bar_rect)
        fill = bar_rect.copy()
        fill.width = int(bar_rect.width * ready_frac)
        pygame.draw.rect(surface, _GREEN if ready_frac >= 1.0 else _YELLOW,
                         fill)
        pygame.draw.rect(surface, _BLACK, bar_rect, 2)
        tip = "SẴN SÀNG" if ready_frac >= 1.0 else "HỒI..."
        tip_label = self.font_small.render(tip, True, _WHITE)
        surface.blit(tip_label,
                     tip_label.get_rect(midtop=(rect.centerx,
                                                bar_rect.bottom + 4)))

    def draw_camera_warning(self, surface: pygame.Surface,
                            message: str) -> None:
        """Banner canh bao khi webcam khong hoat dong."""
        text = f"! {message} - Dùng phím SPACE để vỗ cánh"
        label = self.font_medium.render(text, True, _WHITE)
        bg = pygame.Surface((label.get_width() + 24,
                             label.get_height() + 12), pygame.SRCALPHA)
        bg.fill((200, 60, 50, 220))
        rect = bg.get_rect(midtop=(config.WINDOW_WIDTH // 2, 130))
        surface.blit(bg, rect)
        surface.blit(label, label.get_rect(center=rect.center))

    # ------------------------------------------------------------------
    # Cac man hinh
    # ------------------------------------------------------------------
    def draw_menu(self, surface: pygame.Surface, high_score: int,
                  vision_ok: bool, calibrated: bool) -> None:
        cx = config.WINDOW_WIDTH // 2
        self._text_outline(surface, "WING FLAP", self.font_huge, (cx, 150),
                           color=_YELLOW)
        self._text_outline(surface, "Vỗ hai tay như chim để bay lên!",
                           self.font_big, (cx, 215))

        lines = [
            ("ENTER  -  Bắt đầu chơi", _WHITE),
            ("C  -  Hiệu chỉnh lại camera", _WHITE),
            ("ESC  -  Thoát", _WHITE),
        ]
        if vision_ok:
            lines.insert(0, ("(Hoặc vỗ cánh trước webcam để bắt đầu)",
                             _GREEN))
            if not calibrated:
                lines.append(("Lần đầu chơi sẽ hiệu chỉnh nhanh ~5 giây",
                              _YELLOW))
        else:
            lines.insert(0, ("Webcam chưa sẵn sàng - chơi bằng phím SPACE",
                             _RED))
        for i, (text, color) in enumerate(lines):
            self._text_outline(surface, text, self.font_medium,
                               (cx, 330 + i * 40), color=color)
        self._text_outline(surface, f"Kỷ lục: {high_score}",
                           self.font_big, (cx, 540), color=_YELLOW)

    def draw_game_over(self, surface: pygame.Surface, score: int,
                       high_score: int, is_new_record: bool) -> None:
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT),
                                 pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        cx = config.WINDOW_WIDTH // 2
        self._text_outline(surface, "GAME OVER", self.font_huge, (cx, 200),
                           color=_RED)
        self._text_outline(surface, f"Điểm: {score}", self.font_big,
                           (cx, 285))
        if is_new_record:
            self._text_outline(surface, "★ KỶ LỤC MỚI! ★", self.font_big,
                               (cx, 335), color=_YELLOW)
        else:
            self._text_outline(surface, f"Kỷ lục: {high_score}",
                               self.font_medium, (cx, 335), color=_YELLOW)
        for i, text in enumerate((
                "R  -  Chơi lại  (hoặc vỗ cánh)",
                "C  -  Hiệu chỉnh lại camera",
                "ESC  -  Thoát")):
            self._text_outline(surface, text, self.font_medium,
                               (cx, 420 + i * 40))

    def draw_get_ready(self, surface: pygame.Surface, countdown: str,
                       time_left: float, total: float) -> None:
        """Man hinh chuan bi: huong dan + dem nguoc 3-2-1 truoc khi co trong luc."""
        cx = config.WINDOW_WIDTH // 2
        self._text_outline(surface, "CHUẨN BỊ...", self.font_big, (cx, 150),
                           color=_YELLOW)
        self._text_outline(surface, "Vỗ hai tay để bay", self.font_big,
                           (cx, 200))
        # So dem nguoc phong to nhe theo nhip (pulse trong tung giay)
        segment = max(total / 3.0, 1e-6)
        frac_in_segment = (time_left % segment) / segment  # 1 -> 0
        scale = 1.0 + 0.35 * frac_in_segment
        font = self._sized_font(int(110 * scale))
        self._text_outline(surface, countdown, font,
                           (cx, config.WINDOW_HEIGHT // 2 - 20),
                           color=_YELLOW)

    def draw_go(self, surface: pygame.Surface, age: float) -> None:
        """Chu "GO!" phong to va mo dan ngay khi bat dau roi."""
        k = min(1.0, age / config.GO_TEXT_DURATION)  # 0 -> 1
        font = self._sized_font(int(90 + 50 * k))
        label = font.render("GO!", True, _GREEN)
        shadow = font.render("GO!", True, _BLACK)
        alpha = int(255 * (1.0 - k))
        label.set_alpha(alpha)
        shadow.set_alpha(alpha)
        center = (config.WINDOW_WIDTH // 2, config.WINDOW_HEIGHT // 2 - 20)
        rect = label.get_rect(center=center)
        surface.blit(shadow, rect.move(3, 3))
        surface.blit(label, rect)

    def draw_calibration(self, surface: pygame.Surface,
                         snap: VisionSnapshot, message: str,
                         progress: float, phase_name: str) -> None:
        surface.fill((22, 26, 38))
        cx = config.WINDOW_WIDTH // 2

        self._text_outline(surface, "HIỆU CHỈNH CAMERA", self.font_big,
                           (cx, 44), color=_YELLOW)

        # Webcam lon o giua man hinh
        cam_w, cam_h = 560, 420
        cam_rect = pygame.Rect(cx - cam_w // 2, 80, cam_w, cam_h)
        frame_surf = self.frame_to_surface(snap.frame_rgb)
        if frame_surf is not None:
            surface.blit(pygame.transform.scale(frame_surf, cam_rect.size),
                         cam_rect)
        else:
            pygame.draw.rect(surface, (35, 35, 45), cam_rect)
            msg = self.font_medium.render(snap.camera_message, True,
                                          (220, 220, 230))
            surface.blit(msg, msg.get_rect(center=cam_rect.center))
        state_color = _STATE_COLORS.get(snap.detector_state,
                                        _STATE_COLORS["NO_POSE"])
        pygame.draw.rect(surface, state_color, cam_rect, 4)

        # Huong dan pha hien tai + progress bar
        self._text_outline(surface, message, self.font_big,
                           (cx, cam_rect.bottom + 40))
        bar = pygame.Rect(cx - 220, cam_rect.bottom + 70, 440, 22)
        pygame.draw.rect(surface, (50, 55, 70), bar)
        fill = bar.copy()
        fill.width = int(bar.width * progress)
        pygame.draw.rect(surface, _GREEN, fill)
        pygame.draw.rect(surface, _WHITE, bar, 2)

        self._text_outline(surface,
                           "S - bỏ qua (dùng mặc định)     ESC - thoát",
                           self.font_medium, (cx, bar.bottom + 34),
                           color=(190, 195, 210))

    # ------------------------------------------------------------------
    # Debug overlay
    # ------------------------------------------------------------------
    def draw_debug(self, surface: pygame.Surface, snap: VisionSnapshot,
                   game_lines: Optional[list[str]] = None) -> None:
        """Overlay debug: thong so gameplay (neu co) + thong so vision."""
        lines: list[str] = list(game_lines or [])
        if lines:
            lines.append("-" * 30)
        lines += [
            f"state       : {snap.debug.get('state', snap.detector_state)}",
            f"wrist L/R y : {snap.debug.get('lw_y', '-')} / "
            f"{snap.debug.get('rw_y', '-')}",
            f"shoulder y  : {snap.debug.get('ls_y', '-')} / "
            f"{snap.debug.get('rs_y', '-')}",
            f"vel L/R     : {snap.debug.get('vel_lw', '-')} / "
            f"{snap.debug.get('vel_rw', '-')}  (norm/s)",
            f"shoulder w  : {snap.debug.get('shoulder_w', '-')}",
            f"visibility  : {snap.debug.get('visibility', '-')}",
            f"cooldown    : {snap.debug.get('cooldown', '-')}",
            f"flaps       : {snap.debug.get('flaps', '0')}",
            f"up margin   : {snap.debug.get('up_margin', '-')}",
            f"min speed   : {snap.debug.get('down_speed_min', '-')}",
        ]
        pad = 8
        width = 300
        height = len(lines) * 19 + pad * 2
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 165))
        for i, line in enumerate(lines):
            label = self.font_small.render(line, True, (170, 255, 170))
            panel.blit(label, (pad, pad + i * 19))
        surface.blit(panel, (8, 120))
