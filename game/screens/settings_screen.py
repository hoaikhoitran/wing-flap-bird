"""Man hinh Settings: camera, do kho, do nhay, am thanh, hien thi, du lieu.

Nguyen tac:
  - Moi thay doi tu luu ngay vao settings.json (LocalAppData).
  - Quet camera chay trong THREAD RIENG, khong treo game.
  - Chi mo 1 VideoCapture tai mot thoi diem (scan mo/release tuan tu).
  - Thao tac xoa du lieu co hop thoai xac nhan.
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Optional

import pygame

import config
from core import storage
from game import i18n
from game.i18n import tr
from game.widgets import (COL_PANEL, COL_RED, COL_TEXT_DIM, Button,
                          ConfirmDialog, Selector, Slider, Toggle,
                          WidgetScreen)

if TYPE_CHECKING:
    from game.game import Game


def _sensitivity_text(value: float) -> str:
    if value < 0.85:
        name = tr("sens.low")
    elif value > 1.15:
        name = tr("sens.high")
    else:
        name = tr("sens.normal")
    return f"{name} ({value:.2f})"


class SettingsScreen(WidgetScreen):
    def __init__(self, game: "Game") -> None:
        super().__init__()
        self.game = game
        self.testing = False
        self._scanning = False
        self._scan_result: Optional[list[int]] = None
        self._cam_indices: list[int] = [game.settings.camera_index]
        self._show_recalib_hint = False
        self._build()

    # ------------------------------------------------------------------
    # Dung giao dien
    # ------------------------------------------------------------------
    def _build(self) -> None:
        self.widgets.clear()
        s = self.game.settings

        # ----- Cot trai: camera -----
        lx, lw = 60, 420
        options = [tr("settings.camera_item", index=i)
                   for i in self._cam_indices]
        if self._scanning:
            options = [tr("settings.camera_scanning")]
        elif not options:
            options = [tr("settings.camera_none")]
        try:
            selected = self._cam_indices.index(s.camera_index)
        except ValueError:
            selected = 0
        self._cam_selector = Selector(
            pygame.Rect(lx, 100, lw, 40), tr("settings.camera"),
            options, selected, self._on_camera_change)
        self.widgets.append(self._cam_selector)

        self._test_btn = Button(
            pygame.Rect(lx, 152, 200, 40),
            tr("settings.camera_stop_test") if self.testing
            else tr("settings.camera_test"),
            self._toggle_test)
        self.widgets.append(self._test_btn)
        self._refresh_btn = Button(
            pygame.Rect(lx + 220, 152, 200, 40),
            tr("settings.camera_refresh"), self._start_scan)
        self._refresh_btn.enabled = not self._scanning
        self.widgets.append(self._refresh_btn)

        # ----- Cot phai: gameplay / am thanh / hien thi -----
        rx, rw, row = 540, 400, 52
        y = 100
        diff_options = [tr("settings.diff_easy"), tr("settings.diff_normal")]
        diff_index = 0 if s.difficulty == "easy" else 1
        self.widgets.append(Selector(
            pygame.Rect(rx, y, rw, 40), tr("settings.difficulty"),
            diff_options, diff_index, self._on_difficulty)); y += row
        self.widgets.append(Slider(
            pygame.Rect(rx, y, rw, 40), tr("settings.sensitivity"),
            0.5, 1.5, s.sensitivity, 0.05, self._on_sensitivity,
            fmt=_sensitivity_text)); y += row
        lang_index = 0 if s.language == "vi" else 1
        self.widgets.append(Selector(
            pygame.Rect(rx, y, rw, 40), tr("settings.language"),
            ["Tiếng Việt", "English"], lang_index,
            self._on_language)); y += row
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 40), tr("settings.sound"),
            s.sound_enabled, self._on_sound,
            tr("settings.on"), tr("settings.off"))); y += row
        self.widgets.append(Slider(
            pygame.Rect(rx, y, rw, 40), tr("settings.volume"),
            0, 100, s.volume, 5, self._on_volume,
            fmt=lambda v: f"{int(v)}")); y += row
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 40), tr("settings.music"),
            s.music_enabled, self._on_music,
            tr("settings.on"), tr("settings.off"))); y += row
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 40), tr("settings.fullscreen"),
            s.fullscreen, self._on_fullscreen,
            tr("settings.on"), tr("settings.off"))); y += row
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 40), tr("settings.webcam_preview"),
            s.webcam_preview_enabled, self._on_preview,
            tr("settings.on"), tr("settings.off"))); y += row
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 40), tr("settings.show_fps"),
            s.show_fps, self._on_fps,
            tr("settings.on"), tr("settings.off"))); y += row
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 40), tr("settings.debug"),
            s.debug_enabled, self._on_debug,
            tr("settings.on"), tr("settings.off"))); y += row

        # ----- Hang duoi: du lieu + quay lai -----
        by = 632
        self.widgets.append(Button(
            pygame.Rect(60, by, 235, 44), tr("settings.reset_high_score"),
            lambda: self._confirm(self._do_reset_high_score)))
        self.widgets.append(Button(
            pygame.Rect(310, by, 235, 44), tr("settings.reset_calibration"),
            lambda: self._confirm(self._do_reset_calibration)))
        self.widgets.append(Button(
            pygame.Rect(560, by, 235, 44), tr("settings.reset_all"),
            lambda: self._confirm(self._do_reset_all)))
        self.widgets.append(Button(
            pygame.Rect(830, by, 130, 44), tr("settings.back"), self._back))

    def on_enter(self) -> None:
        self.testing = False
        self._build()
        if self._scan_result is None and not self._scanning:
            self._start_scan()

    def on_leave(self) -> None:
        if self.testing:
            self.testing = False
            self.game.stop_vision_if_idle()

    # ------------------------------------------------------------------
    # Camera
    # ------------------------------------------------------------------
    def _start_scan(self) -> None:
        if self._scanning:
            return
        self._scanning = True
        self._build()

        def worker() -> None:
            from vision.camera import scan_available_cameras
            result = scan_available_cameras(config.CAMERA_SCAN_MAX_INDEX)
            self._scan_result = result
            self._scanning = False

        threading.Thread(target=worker, name="camera-scan",
                         daemon=True).start()

    def update(self, dt: float) -> None:
        super().update(dt)
        # Scan xong -> cap nhat danh sach camera (chay tren main thread)
        if self._scan_result is not None and not self._scanning \
                and self._refresh_btn.enabled is False:
            found = self._scan_result or []
            current = self.game.settings.camera_index
            self._cam_indices = found if found else [current]
            if current not in self._cam_indices:
                self._cam_indices.append(current)
                self._cam_indices.sort()
            self._build()

    def _on_camera_change(self, option_index: int) -> None:
        if not self._cam_indices:
            return
        option_index = min(option_index, len(self._cam_indices) - 1)
        new_index = self._cam_indices[option_index]
        settings = self.game.settings
        if new_index == settings.camera_index:
            return
        settings.camera_index = new_index
        settings.save()
        self._show_recalib_hint = (
            storage.load_calibration(new_index) is None)
        self.game.on_camera_changed(new_index)

    def _toggle_test(self) -> None:
        if self.testing:
            self.testing = False
            self.game.stop_vision_if_idle()
        else:
            self.testing = self.game.ensure_vision()
        self._test_btn.label = (tr("settings.camera_stop_test")
                                if self.testing
                                else tr("settings.camera_test"))

    # ------------------------------------------------------------------
    # Cac setting khac (tu luu ngay)
    # ------------------------------------------------------------------
    def _on_difficulty(self, index: int) -> None:
        self.game.settings.difficulty = "easy" if index == 0 else "normal"
        self.game.settings.save()

    def _on_sensitivity(self, value: float) -> None:
        self.game.settings.sensitivity = round(value, 2)
        self.game.settings.save()
        if self.game.vision is not None:
            self.game.vision.apply_sensitivity(value)

    def _on_language(self, index: int) -> None:
        self.game.settings.language = "vi" if index == 0 else "en"
        self.game.settings.save()
        i18n.set_language(self.game.settings.language)
        self.game.rebuild_screens()
        self._build()

    def _on_sound(self, value: bool) -> None:
        self.game.settings.sound_enabled = value
        self.game.settings.save()
        self.game.sound.set_enabled(value)

    def _on_volume(self, value: float) -> None:
        self.game.settings.volume = int(value)
        self.game.settings.save()
        self.game.sound.set_volume(int(value))

    def _on_music(self, value: bool) -> None:
        self.game.settings.music_enabled = value
        self.game.settings.save()

    def _on_fullscreen(self, value: bool) -> None:
        self.game.settings.fullscreen = value
        self.game.settings.save()
        self.game.apply_display_mode()

    def _on_preview(self, value: bool) -> None:
        self.game.settings.webcam_preview_enabled = value
        self.game.settings.save()

    def _on_fps(self, value: bool) -> None:
        self.game.settings.show_fps = value
        self.game.settings.save()

    def _on_debug(self, value: bool) -> None:
        self.game.settings.debug_enabled = value
        self.game.settings.save()
        config.DEBUG_MODE = value

    # ------------------------------------------------------------------
    # Du lieu (co xac nhan)
    # ------------------------------------------------------------------
    def _confirm(self, action) -> None:
        self.dialog = ConfirmDialog(tr("settings.confirm"),
                                    tr("settings.yes"), tr("settings.no"),
                                    action)

    def _do_reset_high_score(self) -> None:
        storage.reset_high_score()
        self.game.high_score = 0

    def _do_reset_calibration(self) -> None:
        storage.clear_calibration()
        self.game.mark_uncalibrated()

    def _do_reset_all(self) -> None:
        self.game.reset_all_settings()
        self._build()

    def _back(self) -> None:
        self.game.close_settings()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return True
        return False

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 22, 34))
        ui = self.game.ui
        ui._text_outline(surface, tr("settings.title"), ui.font_big,
                         (config.WINDOW_WIDTH // 2, 44),
                         color=(255, 220, 80))

        # Khung preview camera (cot trai duoi)
        preview = pygame.Rect(60, 216, 420, 300)
        pygame.draw.rect(surface, COL_PANEL, preview, border_radius=10)
        if self.testing and self.game.vision is not None:
            snap = self.game.vision.snapshot()
            frame = ui.frame_to_surface(snap.frame_rgb)
            inner = preview.inflate(-12, -12)
            if frame is not None:
                surface.blit(pygame.transform.scale(frame, inner.size),
                             inner)
            else:
                msg = ui.font_small.render(tr("settings.camera_busy"),
                                           True, COL_RED)
                surface.blit(msg, msg.get_rect(center=inner.center))
        else:
            hint = ui.font_small.render(tr("settings.camera_test"), True,
                                        COL_TEXT_DIM)
            surface.blit(hint, hint.get_rect(center=preview.center))

        # Trang thai quet / goi y calibration lai
        status_y = 542
        if self._scanning:
            status = ui.font_small.render(tr("settings.camera_scanning"),
                                          True, COL_TEXT_DIM)
            surface.blit(status, (60, status_y))
        elif self._scan_result is not None and not self._scan_result:
            status = ui.font_small.render(tr("settings.camera_none"),
                                          True, COL_RED)
            surface.blit(status, (60, status_y))
        if self._show_recalib_hint:
            hint = ui.font_small.render(tr("settings.recalib_hint"), True,
                                        (255, 190, 120))
            surface.blit(hint, (60, status_y + 24))

        self.draw_widgets(surface, ui.font_medium)
