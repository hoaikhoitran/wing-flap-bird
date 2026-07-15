"""Vong lap game chinh + state machine day du cho public beta:

PRIVACY_NOTICE -> MAIN_MENU -> (SETTINGS / HOW_TO_PLAY / CREDITS / DONATE)
                            -> CALIBRATING -> GET_READY -> PLAYING <-> PAUSED
                                                        -> GAME_OVER

Nguyen tac:
  - Menu dieu khien bang chuot + ban phim, KHONG can webcam.
  - Camera chi mo khi can (bam CHOI, test camera, test cu chi, calibration).
  - Khi pause: physics/obstacle/score dung; flap tu webcam bi bo qua va
    duoc CLEAR khi resume de chim khong tu bay.
  - High score / settings / calibration luu o LocalAppData (core.storage).
"""
from __future__ import annotations

import logging
import math
import random
import time
from enum import Enum
from typing import Optional

import pygame

import config
from core import storage
from core.settings import GameSettings
from core.version import PRIVACY_VERSION, window_title
from game import i18n, theme, widgets
from game.background import Background
from game.i18n import tr
from game.obstacle import ObstacleManager
from game.particles import ParticleSystem
from game.player import Player
from game.sound import SoundBank
from game.ui import UI
from vision.calibration import CalibPhase, Calibrator
from vision.vision_system import VisionSystem

logger = logging.getLogger("wingflap.game")


class GameState(Enum):
    PRIVACY_NOTICE = "PRIVACY_NOTICE"
    MAIN_MENU = "MAIN_MENU"
    CHARACTER_SELECT = "CHARACTER_SELECT"
    SETTINGS = "SETTINGS"
    HOW_TO_PLAY = "HOW_TO_PLAY"
    CREDITS = "CREDITS"
    DONATE = "DONATE"
    CALIBRATING = "CALIBRATING"
    GET_READY = "GET_READY"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME_OVER"


# Man hinh menu ve TOAN BO (khong ve world duoi)
_MENU_STATES = (GameState.PRIVACY_NOTICE, GameState.MAIN_MENU,
                GameState.CHARACTER_SELECT, GameState.SETTINGS,
                GameState.HOW_TO_PLAY, GameState.CREDITS, GameState.DONATE)
# Man hinh overlay: world dong bang ve duoi, screen ve de len
_OVERLAY_STATES = (GameState.PAUSED, GameState.GAME_OVER)


class Game:
    """Ket noi moi thu: settings, screens, vision, vat ly, hieu ung, am thanh."""

    def __init__(self, settings: Optional[GameSettings] = None,
                 use_camera: bool = True,
                 camera_override: Optional[int] = None) -> None:
        self.settings = settings or GameSettings.load()
        if camera_override is not None:
            self.settings.camera_index = max(0, camera_override)
        i18n.set_language(self.settings.language)
        if self.settings.debug_enabled:
            config.DEBUG_MODE = True

        pygame.init()
        self.screen: pygame.Surface
        self.apply_display_mode()
        pygame.display.set_caption(window_title())
        self.clock = pygame.time.Clock()
        # The gioi game ve len surface rieng de co the "rung" khi va cham
        self.world = pygame.Surface(
            (config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

        self.ui = UI()
        self.background = Background()
        self.diff = config.get_difficulty_config(self.settings.difficulty)
        self.player = Player(config.PLAYER_X, config.PLAYER_START_Y,
                             self.diff,
                             character_id=self.settings.selected_character)
        self.obstacles = ObstacleManager(config.PLAYER_X, self.diff)
        self.particles = ParticleSystem()
        self.sound = SoundBank()
        self.sound.set_enabled(self.settings.sound_enabled)
        self.sound.set_volume(self.settings.volume)
        # Sound hook cho widget (menu_move / menu_confirm)
        widgets.set_sound_hook(self.sound.play)

        # --- Vision: lazy - KHONG mo camera khi boot ---
        self.use_camera = use_camera
        self.vision: Optional[VisionSystem] = None

        # --- Trang thai ---
        self.running = True
        self.score = 0
        self.high_score = storage.load_high_score()
        self.is_new_record = False
        self.calibrator: Optional[Calibrator] = None
        self._calib_return: Optional[GameState] = None
        self._settings_return = GameState.MAIN_MENU
        self._prepause: Optional[GameState] = None
        self._session_active = False  # dang trong mot luot choi (ke ca pause)

        # --- Timers hieu ung ---
        self._flap_text_age = math.inf
        self._flap_text_pos = (0.0, 0.0)
        self._flap_flash_age = math.inf
        self._trauma = 0.0          # screen shake trauma-based (decay)
        self._shake_t = 0.0
        self._score_pop_age = math.inf
        self._game_over_at = 0.0
        self._get_ready_timer = 0.0
        self._grace_timer = 0.0
        self._go_text_age = math.inf
        self._charselect_return = GameState.MAIN_MENU

        # --- Man hinh menu (import tre de tranh vong lap import) ---
        from game.screens.character_select import CharacterSelectScreen
        from game.screens.credits_screen import CreditsScreen
        from game.screens.donate_screen import DonateScreen
        from game.screens.game_over_screen import GameOverScreen
        from game.screens.main_menu import MainMenuScreen
        from game.screens.pause_screen import PauseScreen
        from game.screens.privacy_screen import PrivacyScreen
        from game.screens.settings_screen import SettingsScreen
        from game.screens.tutorial_screen import TutorialScreen
        self.screens = {
            GameState.PRIVACY_NOTICE: PrivacyScreen(self),
            GameState.MAIN_MENU: MainMenuScreen(self),
            GameState.CHARACTER_SELECT: CharacterSelectScreen(self),
            GameState.SETTINGS: SettingsScreen(self),
            GameState.HOW_TO_PLAY: TutorialScreen(self),
            GameState.CREDITS: CreditsScreen(self),
            GameState.DONATE: DonateScreen(self),
            GameState.PAUSED: PauseScreen(self),
            GameState.GAME_OVER: GameOverScreen(self),
        }

        first_run = (self.settings.privacy_accepted_version
                     < PRIVACY_VERSION)
        self.state = (GameState.PRIVACY_NOTICE if first_run
                      else GameState.MAIN_MENU)
        self._enter_screen(self.state)
        logger.info("Game initialized (camera=%s, index=%d, difficulty=%s)",
                    use_camera, self.settings.camera_index,
                    self.settings.difficulty)

    # ==================================================================
    # Vong lap chinh
    # ==================================================================
    def run(self, max_frames: Optional[int] = None) -> None:
        """Chay game. max_frames dung cho smoke test tu dong thoat."""
        frames = 0
        try:
            while self.running:
                dt = min(self.clock.tick(config.TARGET_FPS) / 1000.0, 0.05)
                self._handle_events()
                self._update(dt)
                self._draw()
                pygame.display.flip()
                frames += 1
                if max_frames is not None and frames >= max_frames:
                    self.running = False
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        self.stop_vision()
        widgets.set_sound_hook(None)
        # Cache Surface/Font gan voi display hien tai - PHAI xoa truoc
        # pygame.quit(), neu khong instance Game tiep theo (test) se blit
        # surface da giai phong -> access violation
        from core import font_manager
        from game.assets import assets as asset_manager
        asset_manager.clear()
        font_manager.clear_cache()
        pygame.quit()
        logger.info("Game shut down cleanly")

    # ==================================================================
    # Quan ly state & screens
    # ==================================================================
    def _enter_screen(self, state: GameState) -> None:
        screen = self.screens.get(state)
        if screen is not None and hasattr(screen, "on_enter"):
            screen.on_enter()

    def change_state(self, new_state: GameState) -> None:
        old_screen = self.screens.get(self.state)
        if old_screen is not None and hasattr(old_screen, "on_leave"):
            old_screen.on_leave()
        self.state = new_state
        self._enter_screen(new_state)

    def change_state_by_name(self, name: str) -> None:
        self.change_state(GameState[name])

    def rebuild_screens(self) -> None:
        """Sau khi doi ngon ngu / reset settings: dung lai moi man hinh."""
        for screen in self.screens.values():
            if hasattr(screen, "_build"):
                screen._build()

    # ==================================================================
    # Vision (lazy)
    # ==================================================================
    def ensure_vision(self) -> bool:
        """Mo camera + vision thread khi can. Tra ve True neu san sang."""
        if not self.use_camera:
            return False
        if self.vision is None:
            self.vision = VisionSystem(self.settings.camera_index)
        elif self.vision.camera_index != self.settings.camera_index:
            self.vision.set_camera_index(self.settings.camera_index)
        if not self.vision.running:
            if not self.vision.start():
                logger.warning("Vision khong khoi dong duoc: %s",
                               self.vision.snapshot().camera_message)
                return False
        self.vision.apply_sensitivity(self.settings.sensitivity)
        self.vision.apply_flap_cooldown(self.diff.flap_cooldown)
        stored = storage.load_calibration(self.settings.camera_index)
        if stored is not None:
            self.vision.apply_calibration(stored.up_margin_ratio,
                                          stored.down_margin_ratio)
        logger.info("Vision ready (camera index=%d)",
                    self.settings.camera_index)
        return True

    def stop_vision(self) -> None:
        if self.vision is not None:
            self.vision.stop()
            self.vision = None

    def stop_vision_if_idle(self) -> None:
        """Tat camera khi khong con can (khong trong luot choi)."""
        if not self._session_active:
            self.stop_vision()

    def on_camera_changed(self, new_index: int) -> None:
        """Settings doi camera: neu vision dang chay thi chuyen ngay."""
        if self.vision is not None and self.vision.running:
            self.vision.set_camera_index(new_index)
        elif self.vision is not None:
            self.vision = None

    def mark_uncalibrated(self) -> None:
        """Sau khi xoa calibration.json (Settings > Data)."""
        logger.info("Calibration da bi xoa")

    def reset_all_settings(self) -> None:
        self.settings = GameSettings.reset_to_defaults()
        i18n.set_language(self.settings.language)
        config.DEBUG_MODE = self.settings.debug_enabled
        self.sound.set_enabled(self.settings.sound_enabled)
        self.sound.set_volume(self.settings.volume)
        self.apply_display_mode()
        self.rebuild_screens()

    # ==================================================================
    # Hien thi
    # ==================================================================
    def apply_display_mode(self) -> None:
        flags = pygame.SCALED
        if self.settings.fullscreen:
            flags |= pygame.FULLSCREEN
        try:
            self.screen = pygame.display.set_mode(
                (config.WINDOW_WIDTH, config.WINDOW_HEIGHT), flags)
        except pygame.error:
            # Driver khong ho tro SCALED/FULLSCREEN (VD test headless)
            self.screen = pygame.display.set_mode(
                (config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

    # ==================================================================
    # Dieu huong tu menu / pause
    # ==================================================================
    def request_play(self) -> None:
        """Bam CHOI: lay difficulty hien tai, mo camera, vao calibration
        neu chua co, nguoc lai vao thang GET_READY."""
        self.diff = config.get_difficulty_config(self.settings.difficulty)
        self.player.set_difficulty(self.diff)
        self.obstacles.set_difficulty(self.diff)

        if self.use_camera and self.ensure_vision():
            if storage.load_calibration(self.settings.camera_index) is None:
                self._start_calibration(return_to=None)
                return
        self._start_game()

    def request_calibration(self, return_to: str) -> None:
        """Tu tutorial/settings: chay calibration roi quay lai man hinh cu."""
        if self.ensure_vision():
            self._start_calibration(GameState[return_to])
        else:
            logger.warning("Khong the calibration: camera khong san sang")

    def open_settings(self, from_pause: bool) -> None:
        self._settings_return = (GameState.PAUSED if from_pause
                                 else GameState.MAIN_MENU)
        self.change_state(GameState.SETTINGS)

    def close_settings(self) -> None:
        self.change_state(self._settings_return)
        if self._settings_return is GameState.MAIN_MENU:
            self.stop_vision_if_idle()

    def back_to_menu(self) -> None:
        self._session_active = False
        self.change_state(GameState.MAIN_MENU)
        self.stop_vision()

    # ------------------------------------------------------------------
    # Chon nhan vat
    # ------------------------------------------------------------------
    def open_character_select(self, from_game_over: bool = False) -> None:
        self._charselect_return = (GameState.GAME_OVER if from_game_over
                                   else GameState.MAIN_MENU)
        self.change_state(GameState.CHARACTER_SELECT)

    def close_character_select(self) -> None:
        self.change_state(self._charselect_return)

    def select_character(self, char_id: str) -> None:
        """Luu lua chon + ap dung ngay cho luot choi tiep theo."""
        self.settings.selected_character = char_id
        self.settings.validate()
        self.settings.save()
        self.player.set_character(self.settings.selected_character)
        logger.info("Character -> %s", self.settings.selected_character)

    def request_quit(self) -> None:
        self.running = False

    def pause(self) -> None:
        if self.state in (GameState.PLAYING, GameState.GET_READY):
            self._prepause = self.state
            self.change_state(GameState.PAUSED)

    def resume_from_pause(self) -> None:
        # Clear flap don trong luc pause de chim khong tu bay khi resume
        if self.vision is not None:
            self.vision.consume_flaps()
        self.change_state(self._prepause or GameState.PLAYING)
        self._prepause = None

    def restart_from_pause(self) -> None:
        self._prepause = None
        self._start_game()

    # ==================================================================
    # Calibration
    # ==================================================================
    def _start_calibration(self, return_to: Optional[GameState]) -> None:
        self.calibrator = Calibrator()
        self._calib_return = return_to
        self.change_state(GameState.CALIBRATING)

    def _finish_calibration(self, skipped: bool) -> None:
        calib = self.calibrator
        if (not skipped and calib is not None
                and calib.phase is CalibPhase.DONE
                and calib.result is not None):
            result = calib.result
            if self.vision is not None:
                self.vision.apply_calibration(result.up_margin_ratio,
                                              result.down_margin_ratio)
            storage.save_calibration(storage.StoredCalibration(
                camera_index=self.settings.camera_index,
                up_margin_ratio=result.up_margin_ratio,
                down_margin_ratio=result.down_margin_ratio,
                measured_raise_range=result.measured_raise_range,
            ))
            self.sound.play("calib_ok")
            logger.info("Calibration hoan tat va da luu")
        self.calibrator = None
        if self._calib_return is not None:
            target = self._calib_return
            self._calib_return = None
            self.change_state(target)
            self.stop_vision_if_idle()
        else:
            self._start_game()

    def _cancel_calibration(self) -> None:
        self.calibrator = None
        if self._calib_return is not None:
            target = self._calib_return
            self._calib_return = None
            self.change_state(target)
            self.stop_vision_if_idle()
        else:
            self.back_to_menu()

    # ==================================================================
    # Su kien ban phim (cac state gameplay)
    # ==================================================================
    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                config.DEBUG_MODE = not config.DEBUG_MODE
                continue
            screen = self.screens.get(self.state)
            if screen is not None:
                screen.handle_event(event)
                continue
            if event.type == pygame.KEYDOWN:
                self._on_gameplay_key(event.key)

    def _on_gameplay_key(self, key: int) -> None:
        if self.state is GameState.CALIBRATING:
            if key == pygame.K_s:
                self._finish_calibration(skipped=True)
            elif key == pygame.K_r:
                self.calibrator = Calibrator()
            elif key == pygame.K_ESCAPE:
                self._cancel_calibration()

        elif self.state is GameState.GET_READY:
            if key == pygame.K_ESCAPE:
                self.pause()

        elif self.state is GameState.PLAYING:
            if key == pygame.K_SPACE:
                # SPACE: fallback/debug - cung mot luc bay voi webcam
                self._do_flap()
            elif key == pygame.K_ESCAPE:
                self.pause()

        # GAME_OVER: xu ly boi GameOverScreen (button + phim R/M)

    # ==================================================================
    # Cap nhat
    # ==================================================================
    def _update(self, dt: float) -> None:
        self._flap_text_age += dt
        self._flap_flash_age += dt
        self._score_pop_age += dt
        # Trauma decay + thoi gian noise cho shake
        if self._trauma > 0.0:
            self._trauma = max(0.0, self._trauma - 1.6 * dt)
            self._shake_t += dt

        state = self.state
        screen = self.screens.get(state)

        # Flap tu webcam: chi tieu thu o cac state gameplay.
        # PAUSED/CALIBRATING: tieu thu roi BO QUA (khong phat vao game).
        flaps = 0
        if self.vision is not None and self.vision.running \
                and state in (GameState.GET_READY, GameState.PLAYING,
                              GameState.GAME_OVER, GameState.PAUSED,
                              GameState.CALIBRATING):
            flaps = self.vision.consume_flaps()

        if state in _MENU_STATES and screen is not None:
            screen.update(dt)
            if state in (GameState.MAIN_MENU, GameState.CHARACTER_SELECT):
                self.background.update(dt, scrolling=False)
            if state is GameState.MAIN_MENU:
                self.player.idle_bob(dt)
            return

        if state is GameState.PAUSED:
            screen.update(dt)
            return

        if state is GameState.GAME_OVER:
            screen.update(dt)
            self.background.update(dt, scrolling=False)
            self.player.animator.update(dt)  # hurt frames tiep tuc
            self.particles.update(dt)
            if flaps > 0 and time.monotonic() - self._game_over_at > 1.2:
                self._start_game()
            return

        if state is GameState.CALIBRATING:
            self._update_calibration(dt)

        elif state is GameState.GET_READY:
            self.background.update(dt, scrolling=False)
            self.player.idle_bob(dt)
            if flaps > 0:
                self._flap_flash_age = 0.0  # phan hoi vien webcam, chua bay
            self._get_ready_timer -= dt
            if self._get_ready_timer <= 0.0:
                self.player.vel_y = 0.0
                self._grace_timer = self.diff.grace_period
                self._go_text_age = 0.0
                self.state = GameState.PLAYING

        elif state is GameState.PLAYING:
            # Thu tu QUAN TRONG: flap TRUOC player.update() cung frame
            if flaps > 0:
                self._do_flap()
            self._update_playing(dt)

    def _update_playing(self, dt: float) -> None:
        self._go_text_age += dt
        self.background.update(dt, scrolling=True,
                               scroll_speed=self.diff.pipe_speed)
        if self._grace_timer > 0.0:
            self._grace_timer = max(0.0, self._grace_timer - dt)
            self.player.update(dt, gravity_scale=0.5)
        else:
            self.player.update(dt)
        self.particles.update(dt)

        scored = self.obstacles.update(dt)
        if scored:
            self.score += scored
            self.sound.play("score")
            self._score_pop_age = 0.0  # score pop (game feel)
            self.particles.emit_score(self.player.x, self.player.y - 30)

        ground_y = config.WINDOW_HEIGHT - config.GROUND_HEIGHT
        hit_pipe = self.obstacles.check_collision(
            self.player.x, self.player.y, self.player.radius)
        hit_ground = self.player.y + self.player.radius >= ground_y
        flew_too_high = self.player.y < -self.player.radius
        if hit_pipe or hit_ground or flew_too_high:
            if hit_ground:
                self.player.y = ground_y - self.player.radius
            self._on_death()

    def _update_calibration(self, dt: float) -> None:
        if self.calibrator is None:
            self._start_game()
            return
        snap = self.vision.snapshot() if self.vision else None
        metrics = snap.metrics if snap else None
        self.calibrator.update(metrics, dt)
        if self.calibrator.finished:
            self._finish_calibration(skipped=False)

    # ==================================================================
    # Gameplay
    # ==================================================================
    def _start_game(self) -> None:
        """Reset DAY DU roi vao GET_READY (dem nguoc, chua co trong luc)."""
        self.diff = config.get_difficulty_config(self.settings.difficulty)
        self.player.set_difficulty(self.diff)
        self.player.set_character(self.settings.selected_character)
        self.obstacles.set_difficulty(self.diff)
        if self.vision is not None:
            self.vision.apply_flap_cooldown(self.diff.flap_cooldown)
            self.vision.consume_flaps()  # bo flap don tu truoc
        self.player.reset(config.PLAYER_START_Y)
        self.obstacles.reset()
        self.particles.clear()
        self.score = 0
        self.is_new_record = False
        self._shake_time = 0.0
        self._flap_text_age = math.inf
        self._go_text_age = math.inf
        self._grace_timer = 0.0
        self._get_ready_timer = self.diff.start_delay
        self._session_active = True
        self.change_state(GameState.GET_READY)

    def _do_flap(self) -> None:
        if config.DEBUG_MODE:
            logger.debug("FLAP detected | old_velocity=%+.1f "
                         "| new_velocity=%+.1f",
                         self.player.vel_y, self.diff.flap_force)
        self.player.flap()
        self.sound.play("flap")
        self.particles.emit_flap(self.player.x - 18, self.player.y + 10)
        self._flap_text_age = 0.0
        self._flap_text_pos = (self.player.x, self.player.y)
        self._flap_flash_age = 0.0

    def _on_death(self) -> None:
        self.sound.play("hit")
        self.sound.play("gameover")
        self.player.hurt()  # chuyen hurt animation (khong doi physics)
        self.particles.emit_burst(self.player.x, self.player.y)
        # Trauma-based shake (skill game-feel): cong don, decay ve 0
        self._trauma = min(1.0, self._trauma + theme.SHAKE_TRAUMA_HIT)
        self._game_over_at = time.monotonic()
        if self.score > self.high_score:
            self.high_score = self.score
            self.is_new_record = True
            storage.save_high_score(self.high_score)
        self.change_state(GameState.GAME_OVER)

    # ==================================================================
    # Ve
    # ==================================================================
    def _draw(self) -> None:
        state = self.state

        # Man hinh menu ve toan bo
        if state in _MENU_STATES:
            self.screens[state].draw(self.screen)
            if self.settings.show_fps and state is not GameState.PRIVACY_NOTICE:
                snap_fps = (self.vision.snapshot().vision_fps
                            if self.vision else 0.0)
                self.ui.draw_fps(self.screen, self.clock.get_fps(), snap_fps)
            return

        snap = self.vision.snapshot() if self.vision is not None else None

        if state is GameState.CALIBRATING:
            if self.calibrator is not None and snap is not None:
                hint_key = self.calibrator.hint_key
                self.ui.draw_calibration(
                    self.screen, snap, tr(self.calibrator.message_key),
                    self.calibrator.progress,
                    tr(hint_key) if hint_key else None)
            return

        # --- The gioi 2.5D: back layers -> gates -> front layers ->
        #     contact shadow -> player -> particles (z-order chieu sau)
        ground_top = config.WINDOW_HEIGHT - config.GROUND_HEIGHT
        self.background.draw_back(self.world)
        if state in (GameState.PLAYING, GameState.GAME_OVER,
                     GameState.PAUSED):
            self.obstacles.draw(self.world)
        self.background.draw_front(self.world)
        self.player.draw_shadow(self.world, ground_top)
        self.player.draw(self.world)
        self.particles.draw(self.world)
        if self._flap_text_age < config.FLAP_TEXT_DURATION:
            self.ui.draw_flap_text(self.world, self._flap_text_pos[0],
                                   self._flap_text_pos[1],
                                   self._flap_text_age)
        self.screen.blit(self.world, self._shake_offset())

        # --- HUD ---
        if state is GameState.GET_READY:
            self.ui.draw_get_ready(self.screen, self._countdown_number(),
                                   self._get_ready_timer,
                                   self.diff.start_delay)
        elif state in (GameState.PLAYING, GameState.PAUSED):
            pop = max(0.0, 1.0 - self._score_pop_age / 0.25)
            self.ui.draw_score(self.screen, self.score, self.high_score,
                               pop=pop)
            if state is GameState.PLAYING \
                    and self._go_text_age < config.GO_TEXT_DURATION:
                self.ui.draw_go(self.screen, self._go_text_age)

        # --- Webcam panel + canh bao ---
        if snap is not None and self.settings.webcam_preview_enabled:
            self.ui.draw_webcam_panel(self.screen, snap,
                                      self._flap_flash_age)
        if self.use_camera and state in (GameState.GET_READY,
                                         GameState.PLAYING):
            if snap is None:
                self.ui.draw_camera_warning(self.screen, tr("hud.no_webcam"))
            elif not snap.camera_ok:
                self.ui.draw_camera_warning(self.screen,
                                            snap.camera_message)

        if self.settings.show_fps:
            self.ui.draw_fps(self.screen, self.clock.get_fps(),
                             snap.vision_fps if snap else 0.0)
        if config.DEBUG_MODE:
            self.ui.draw_debug(self.screen, snap or _EMPTY_SNAPSHOT,
                               self._debug_game_lines(snap))

        # Overlay (pause / game over) ve DE LEN gameplay dong bang
        if state in _OVERLAY_STATES:
            self.screens[state].draw(self.screen)

    def _countdown_number(self) -> str:
        segment = self.diff.start_delay / 3.0
        n = int(self._get_ready_timer / max(segment, 1e-6)) + 1
        return str(max(1, min(3, n)))

    def _debug_game_lines(self, snap) -> list[str]:
        flap_yes = self._flap_flash_age < config.DEBUG_FLAP_FLASH
        if snap is not None:
            cooldown = ("READY" if snap.cooldown_remaining <= 0.0
                        else f"{snap.cooldown_remaining:.2f}s")
        else:
            cooldown = "-"
        return [
            f"Velocity Y  : {self.player.vel_y:+.1f} px/s",
            f"Gravity     : {self.diff.gravity:.0f} px/s^2"
            + (" (x0.5 grace)" if self._grace_timer > 0.0 else ""),
            f"Flap force  : {self.diff.flap_force:.0f} px/s",
            f"Flap detected: {'YES' if flap_yes else 'no'}",
            f"Cooldown    : {cooldown}",
            f"Game state  : {self.state.value}",
            f"Difficulty  : {self.diff.name}",
        ]

    def _shake_offset(self) -> tuple[int, int]:
        """Screen shake trauma^2 + noise sin muot (khong random moi frame)."""
        if self._trauma <= 0.001:
            return (0, 0)
        shake = self._trauma * self._trauma
        mag = config.SHAKE_MAGNITUDE
        if self.settings.reduce_screen_shake:
            mag *= 0.35
        return (int(mag * shake * math.sin(self._shake_t * 31.7)),
                int(mag * shake * math.sin(self._shake_t * 42.3)))


# Snapshot rong cho debug overlay khi chua co vision
from vision.vision_system import VisionSnapshot as _VS  # noqa: E402
_EMPTY_SNAPSHOT = _VS()
