"""Settings chia TAB: Camera / Tro choi / Am thanh / Hien thi / Du lieu.

- Khong nhoi moi setting vao 1 man hinh; moi tab dung widget rieng.
- Camera preview giu DUNG aspect 4:3 (khong keo meo webcam frame).
- Moi thay doi tu luu; thao tac xoa du lieu co hop thoai xac nhan.
- Quet camera trong thread rieng, khong treo game.
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Optional

import pygame

import config
from core import font_manager as fm
from core import storage
from game import i18n, theme
from game.i18n import tr
from game.widgets import (Button, ConfirmDialog, Selector, Slider, TabBar,
                          Toggle, WidgetScreen)

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


_TAB_KEYS = ("settings.tab_camera", "settings.tab_gameplay",
             "settings.tab_audio", "settings.tab_display",
             "settings.tab_data")


class SettingsScreen(WidgetScreen):
    def __init__(self, game: "Game") -> None:
        super().__init__()
        self.game = game
        self.tab = 0
        self.testing = False
        self._scanning = False
        self._scan_result: Optional[list[int]] = None
        self._cam_indices: list[int] = [game.settings.camera_index]
        self._show_recalib_hint = False
        self._build()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        self.widgets.clear()
        self._tabbar = TabBar(pygame.Rect(60, 84, 880, 44),
                              [tr(k) for k in _TAB_KEYS], self.tab,
                              self._on_tab)
        self.widgets.append(self._tabbar)

        builder = (self._build_camera, self._build_gameplay,
                   self._build_audio, self._build_display,
                   self._build_data)[self.tab]
        builder()

        self.widgets.append(Button(
            pygame.Rect(810, 630, 130, 46), tr("settings.back"),
            self._back, primary=True))

    def _on_tab(self, index: int) -> None:
        if self.testing:
            self.testing = False
            self.game.stop_vision_if_idle()
        self.tab = index
        self._build()

    # ------------------------------------------------------------------
    # Tab builders
    # ------------------------------------------------------------------
    def _build_camera(self) -> None:
        s = self.game.settings
        lx, lw = 520, 420
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
        self.widgets.append(Selector(
            pygame.Rect(lx, 170, lw, 42), tr("settings.camera"),
            options, selected, self._on_camera_change))

        self._test_btn = Button(
            pygame.Rect(lx, 232, 200, 44),
            tr("settings.camera_stop_test") if self.testing
            else tr("settings.camera_test"), self._toggle_test)
        self.widgets.append(self._test_btn)
        self._refresh_btn = Button(
            pygame.Rect(lx + 220, 232, 200, 44),
            tr("settings.camera_refresh"), self._start_scan)
        self._refresh_btn.enabled = not self._scanning
        self.widgets.append(self._refresh_btn)

    def _build_gameplay(self) -> None:
        s = self.game.settings
        rx, rw, row = 300, 400, 62
        y = 180
        diff_options = [tr("settings.diff_easy"), tr("settings.diff_normal")]
        self.widgets.append(Selector(
            pygame.Rect(rx, y, rw, 42), tr("settings.difficulty"),
            diff_options, 0 if s.difficulty == "easy" else 1,
            self._on_difficulty)); y += row
        self.widgets.append(Slider(
            pygame.Rect(rx, y, rw, 42), tr("settings.sensitivity"),
            0.5, 1.5, s.sensitivity, 0.05, self._on_sensitivity,
            fmt=_sensitivity_text)); y += row
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 42), tr("settings.reduce_shake"),
            s.reduce_screen_shake, self._on_reduce_shake,
            tr("settings.on"), tr("settings.off")))

    def _build_audio(self) -> None:
        s = self.game.settings
        rx, rw, row = 300, 400, 62
        y = 180
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 42), tr("settings.sound"),
            s.sound_enabled, self._on_sound,
            tr("settings.on"), tr("settings.off"))); y += row
        self.widgets.append(Slider(
            pygame.Rect(rx, y, rw, 42), tr("settings.volume"),
            0, 100, s.volume, 5, self._on_volume,
            fmt=lambda v: f"{int(v)}")); y += row
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 42), tr("settings.music"),
            s.music_enabled, self._on_music,
            tr("settings.on"), tr("settings.off")))

    def _build_display(self) -> None:
        s = self.game.settings
        rx, rw, row = 300, 400, 62
        y = 168
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 42), tr("settings.fullscreen"),
            s.fullscreen, self._on_fullscreen,
            tr("settings.on"), tr("settings.off"))); y += row
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 42), tr("settings.webcam_preview"),
            s.webcam_preview_enabled, self._on_preview,
            tr("settings.on"), tr("settings.off"))); y += row
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 42), tr("settings.show_fps"),
            s.show_fps, self._on_fps,
            tr("settings.on"), tr("settings.off"))); y += row
        self.widgets.append(Selector(
            pygame.Rect(rx, y, rw, 42), tr("settings.language"),
            ["Tiếng Việt", "English"], 0 if s.language == "vi" else 1,
            self._on_language)); y += row
        self.widgets.append(Toggle(
            pygame.Rect(rx, y, rw, 42), tr("settings.debug"),
            s.debug_enabled, self._on_debug,
            tr("settings.on"), tr("settings.off")))

    def _build_data(self) -> None:
        cx = config.WINDOW_WIDTH // 2
        y = 200
        for key, action in (
                ("settings.reset_high_score", self._do_reset_high_score),
                ("settings.reset_calibration", self._do_reset_calibration),
                ("settings.reset_all", self._do_reset_all)):
            self.widgets.append(Button(
                pygame.Rect(cx - 190, y, 380, 50), tr(key),
                (lambda a=action: self._confirm(a))))
            y += 66

    # ------------------------------------------------------------------
    # Camera logic (thread scan, khong treo UI)
    # ------------------------------------------------------------------
    def _start_scan(self) -> None:
        if self._scanning:
            return
        self._scanning = True
        self._build()

        def worker() -> None:
            from vision.camera import scan_available_cameras
            self._scan_result = scan_available_cameras(
                config.CAMERA_SCAN_MAX_INDEX)
            self._scanning = False

        threading.Thread(target=worker, name="camera-scan",
                         daemon=True).start()

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._scan_result is not None and not self._scanning \
                and self.tab == 0 and not self._refresh_btn.enabled:
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
    # Callbacks (tu luu ngay)
    # ------------------------------------------------------------------
    def _on_difficulty(self, index: int) -> None:
        self.game.settings.difficulty = "easy" if index == 0 else "normal"
        self.game.settings.save()

    def _on_sensitivity(self, value: float) -> None:
        self.game.settings.sensitivity = round(value, 2)
        self.game.settings.save()
        if self.game.vision is not None:
            self.game.vision.apply_sensitivity(value)

    def _on_reduce_shake(self, value: bool) -> None:
        self.game.settings.reduce_screen_shake = value
        self.game.settings.save()

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

    def on_enter(self) -> None:
        self.testing = False
        self._build()
        if self._scan_result is None and not self._scanning:
            self._start_scan()

    def on_leave(self) -> None:
        if self.testing:
            self.testing = False
            self.game.stop_vision_if_idle()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return True
        return False

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.BG_MENU)
        ui = self.game.ui
        ui._text_outline(surface, tr("settings.title"), "title",
                         (config.WINDOW_WIDTH // 2, 44),
                         color=theme.MANGO)

        if self.tab == 0:
            self._draw_camera_tab(surface, ui)

        self.draw_widgets(surface, ui.font_button)

    def _draw_camera_tab(self, surface: pygame.Surface, ui) -> None:
        # Preview 4:3 DUNG aspect (frame camera 640x480)
        preview = pygame.Rect(60, 170, 400, 300)
        pygame.draw.rect(surface, theme.PANEL_DARK, preview,
                         border_radius=theme.RADIUS_M)
        if self.testing and self.game.vision is not None:
            snap = self.game.vision.snapshot()
            frame = ui.frame_to_surface(snap.frame_rgb)
            inner = preview.inflate(-8, -6)
            # 392x294 ~ 4:3 - khop ti le frame, khong meo
            if frame is not None:
                surface.blit(pygame.transform.scale(frame, inner.size),
                             inner)
            else:
                msg = fm.render("caption", tr("settings.camera_busy"),
                                theme.VERMILION)
                surface.blit(msg, msg.get_rect(center=inner.center))
        else:
            hint = fm.render("caption", tr("settings.camera_test"),
                             theme.TEXT_DIM_ON_DARK)
            surface.blit(hint, hint.get_rect(center=preview.center))
        pygame.draw.rect(surface, theme.PANEL_DARK_BORDER, preview, 2,
                         border_radius=theme.RADIUS_M)

        status_y = 500
        if self._scanning:
            status = fm.render("caption", tr("settings.camera_scanning"),
                               theme.TEXT_DIM_ON_DARK)
            surface.blit(status, (60, status_y))
        elif self._scan_result is not None and not self._scan_result:
            status = fm.render("caption", tr("settings.camera_none"),
                               theme.VERMILION)
            surface.blit(status, (60, status_y))
        if self._show_recalib_hint:
            hint = fm.render("caption", tr("settings.recalib_hint"),
                             theme.MANGO)
            surface.blit(hint, (60, status_y + 26))
