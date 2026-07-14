"""Vong lap game chinh va state machine: MENU / CALIBRATING / PLAYING / GAME_OVER."""
from __future__ import annotations

import json
import math
import os
import random
import time
from enum import Enum
from typing import Optional

import pygame

import config
from game.obstacle import ObstacleManager
from game.particles import ParticleSystem
from game.player import Player
from game.sound import SoundBank
from game.ui import UI, Background
from vision.calibration import CalibPhase, Calibrator
from vision.vision_system import VisionSystem


class GameState(Enum):
    MENU = "MENU"
    CALIBRATING = "CALIBRATING"
    GET_READY = "GET_READY"   # dem nguoc 3-2-1-GO, chua co trong luc
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"


class Game:
    """Ket noi moi thu: vision thread, vat ly, hieu ung, UI, am thanh."""

    def __init__(self, camera_index: int = config.CAMERA_INDEX,
                 use_camera: bool = True) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(
            (config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        pygame.display.set_caption(config.GAME_TITLE)
        self.clock = pygame.time.Clock()
        # The gioi game ve len surface rieng de co the "rung" khi va cham
        self.world = pygame.Surface(
            (config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

        self.ui = UI()
        self.background = Background()
        self.player = Player(config.PLAYER_X, config.WINDOW_HEIGHT / 2)
        self.obstacles = ObstacleManager(config.PLAYER_X)
        self.particles = ParticleSystem()
        self.sound = SoundBank()

        # --- Vision ---
        self.vision = VisionSystem(camera_index)
        self.vision_started = self.vision.start() if use_camera else False
        self.calibrator: Optional[Calibrator] = None
        self.calibrated = False

        # --- Trang thai game ---
        self.state = GameState.MENU
        self.running = True
        self.score = 0
        self.high_score = self._load_high_score()
        self.is_new_record = False

        # --- Timers hieu ung ---
        self._flap_text_age = math.inf
        self._flap_text_pos = (0.0, 0.0)
        self._flap_flash_age = math.inf
        self._shake_time = 0.0
        self._game_over_at = 0.0
        # --- Nhip do vao game ---
        self._get_ready_timer = 0.0   # dem nguoc GET_READY
        self._grace_timer = 0.0       # sau GO: trong luc giam mot nua
        self._go_text_age = math.inf  # chu "GO!" ngay sau countdown

    # ==================================================================
    # Vong lap chinh
    # ==================================================================
    def run(self) -> None:
        try:
            while self.running:
                # Clamp dt de vat ly khong "nhay" khi cua so bi keo/lag
                dt = min(self.clock.tick(config.TARGET_FPS) / 1000.0, 0.05)
                self._handle_events()
                self._update(dt)
                self._draw()
                pygame.display.flip()
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        self.vision.stop()
        pygame.quit()

    # ==================================================================
    # Su kien ban phim
    # ==================================================================
    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    def _on_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_F1:
            config.DEBUG_MODE = not config.DEBUG_MODE

        elif self.state is GameState.MENU:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._on_start_requested()
            elif key == pygame.K_c:
                self._start_calibration()

        elif self.state is GameState.PLAYING:
            # SPACE: fallback/debug, khong phai dieu khien chinh
            if key == pygame.K_SPACE:
                self._do_flap()

        elif self.state is GameState.GET_READY:
            pass  # trong countdown khong nhan input bay

        elif self.state is GameState.GAME_OVER:
            if key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                self._start_game()
            elif key == pygame.K_c:
                self._start_calibration()

        elif self.state is GameState.CALIBRATING:
            if key == pygame.K_s:
                self._finish_calibration(skipped=True)

    # ==================================================================
    # Cap nhat theo trang thai
    # ==================================================================
    def _update(self, dt: float) -> None:
        self._flap_text_age += dt
        self._flap_flash_age += dt
        if self._shake_time > 0.0:
            self._shake_time = max(0.0, self._shake_time - dt)

        # Luon tieu thu su kien flap moi frame de khong bi don ung
        flaps = self.vision.consume_flaps()

        if self.state is GameState.MENU:
            self.background.update(dt, scrolling=False)
            self.player.idle_bob(dt)
            if flaps > 0:
                self._flap_flash_age = 0.0
                self._on_start_requested()

        elif self.state is GameState.CALIBRATING:
            self._update_calibration(dt)

        elif self.state is GameState.GET_READY:
            # Chim nhap nho nhe, chua co trong luc, cot chua chay.
            # Van nhan dien webcam: flap chi nhay vien webcam, KHONG tao luc.
            self.background.update(dt, scrolling=False)
            self.player.idle_bob(dt)
            if flaps > 0:
                self._flap_flash_age = 0.0
            self._get_ready_timer -= dt
            if self._get_ready_timer <= 0.0:
                # GO! Trong luc bat dau tu day, kem 1s grace giam trong luc
                self.player.vel_y = 0.0
                self._grace_timer = config.START_GRACE_PERIOD
                self._go_text_age = 0.0
                self.state = GameState.PLAYING

        elif self.state is GameState.PLAYING:
            # Thu tu QUAN TRONG: xu ly flap TRUOC player.update()
            # de luc bay khong bi buoc vat ly cung frame ghi de
            if flaps > 0:
                self._do_flap()
            self._update_playing(dt)

        elif self.state is GameState.GAME_OVER:
            self.background.update(dt, scrolling=False)
            self.particles.update(dt)
            # Vo canh de choi lai (sau 1.2s de tranh restart ngoai y muon)
            if flaps > 0 and time.monotonic() - self._game_over_at > 1.2:
                self._start_game()

    def _update_playing(self, dt: float) -> None:
        self._go_text_age += dt
        self.background.update(dt, scrolling=True)
        # Grace period sau GO: trong luc giam mot nua de khong chet ngay
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
            self.particles.emit_score(self.player.x, self.player.y - 30)

        # --- Kiem tra thua ---
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
        snap = self.vision.snapshot()
        self.calibrator.update(snap.metrics, dt)
        if self.calibrator.finished:
            self._finish_calibration(skipped=False)

    # ==================================================================
    # Chuyen trang thai
    # ==================================================================
    def _on_start_requested(self) -> None:
        """ENTER/flap o menu: hieu chinh truoc neu chua, roi vao game."""
        if self.vision_started and not self.calibrated:
            self._start_calibration()
        else:
            self._start_game()

    def _start_calibration(self) -> None:
        if not self.vision_started:
            self._start_game()
            return
        self.calibrator = Calibrator()
        self.state = GameState.CALIBRATING

    def _finish_calibration(self, skipped: bool) -> None:
        calib = self.calibrator
        if (not skipped and calib is not None
                and calib.phase is CalibPhase.DONE
                and calib.result is not None):
            self.vision.apply_calibration(calib.result.up_margin_ratio,
                                          calib.result.down_margin_ratio)
            self.sound.play("calib_ok")
        # That bai / bo qua -> giu threshold mac dinh trong config
        self.calibrated = True
        self.calibrator = None
        self._start_game()

    def _start_game(self) -> None:
        """Reset day du roi vao GET_READY (dem nguoc, chua co trong luc)."""
        self.player.reset(config.PLAYER_START_Y)
        self.obstacles.reset()
        self.particles.clear()
        self.score = 0
        self.is_new_record = False
        self._shake_time = 0.0
        self._flap_text_age = math.inf
        self._go_text_age = math.inf
        self._grace_timer = 0.0
        self._get_ready_timer = config.START_DELAY_SECONDS
        self.state = GameState.GET_READY

    def _do_flap(self) -> None:
        if config.DEBUG_MODE:
            print(f"FLAP detected | old_velocity={self.player.vel_y:+.1f} "
                  f"| new_velocity={config.FLAP_FORCE:+.1f}")
        self.player.flap()
        self.sound.play("flap")
        self.particles.emit_flap(self.player.x - 18, self.player.y + 10)
        self._flap_text_age = 0.0
        self._flap_text_pos = (self.player.x, self.player.y)
        self._flap_flash_age = 0.0

    def _on_death(self) -> None:
        self.sound.play("hit")
        self.sound.play("gameover")
        self.particles.emit_burst(self.player.x, self.player.y)
        self._shake_time = config.SHAKE_DURATION
        self._game_over_at = time.monotonic()
        if self.score > self.high_score:
            self.high_score = self.score
            self.is_new_record = True
            self._save_high_score()
        self.state = GameState.GAME_OVER

    # ==================================================================
    # Ve
    # ==================================================================
    def _draw(self) -> None:
        snap = self.vision.snapshot()

        if self.state is GameState.CALIBRATING:
            if self.calibrator is not None:
                self.ui.draw_calibration(self.screen, snap,
                                         self.calibrator.message,
                                         self.calibrator.progress,
                                         self.calibrator.phase.value)
            return

        # --- The gioi game (co the rung khi va cham) ---
        # Thu tu render: background -> obstacles -> player -> particles
        # -> UI -> webcam preview (player luon duoc ve moi frame)
        self.background.draw_sky(self.world)
        if self.state in (GameState.PLAYING, GameState.GAME_OVER):
            self.obstacles.draw(self.world)
        self.background.draw_ground(self.world)
        self.player.draw(self.world)
        self.particles.draw(self.world)
        if self._flap_text_age < config.FLAP_TEXT_DURATION:
            self.ui.draw_flap_text(self.world, self._flap_text_pos[0],
                                   self._flap_text_pos[1],
                                   self._flap_text_age)

        shake = self._shake_offset()
        self.screen.blit(self.world, shake)

        # --- HUD (khong rung) ---
        if self.state is GameState.MENU:
            self.ui.draw_menu(self.screen, self.high_score,
                              vision_ok=self.vision_started
                              and snap.camera_ok,
                              calibrated=self.calibrated)
        elif self.state is GameState.GET_READY:
            self.ui.draw_get_ready(self.screen,
                                   self._countdown_number(),
                                   self._get_ready_timer,
                                   config.START_DELAY_SECONDS)
        elif self.state is GameState.PLAYING:
            self.ui.draw_score(self.screen, self.score, self.high_score)
            if self._go_text_age < config.GO_TEXT_DURATION:
                self.ui.draw_go(self.screen, self._go_text_age)
        elif self.state is GameState.GAME_OVER:
            self.ui.draw_score(self.screen, self.score, self.high_score)
            self.ui.draw_game_over(self.screen, self.score, self.high_score,
                                   self.is_new_record)

        # Khung webcam + canh bao camera
        self.ui.draw_webcam_panel(self.screen, snap, self._flap_flash_age)
        if not self.vision_started:
            self.ui.draw_camera_warning(self.screen, snap.camera_message
                                        or "Webcam chưa khởi động")
        elif not snap.camera_ok:
            self.ui.draw_camera_warning(self.screen, snap.camera_message)

        self.ui.draw_fps(self.screen, self.clock.get_fps(), snap.vision_fps)
        if config.DEBUG_MODE:
            self.ui.draw_debug(self.screen, snap, self._debug_game_lines(snap))

    def _countdown_number(self) -> str:
        """3 / 2 / 1 theo thoi gian con lai cua GET_READY."""
        segment = config.START_DELAY_SECONDS / 3.0
        n = int(self._get_ready_timer / segment) + 1
        return str(max(1, min(3, n)))

    def _debug_game_lines(self, snap) -> list[str]:
        """Thong so gameplay hien tren overlay debug (muc 14)."""
        # "Flap detected: YES" giu it nhat 300ms, khong chi 1 frame
        flap_yes = self._flap_flash_age < config.DEBUG_FLAP_FLASH
        cooldown = ("READY" if snap.cooldown_remaining <= 0.0
                    else f"{snap.cooldown_remaining:.2f}s")
        return [
            f"Velocity Y  : {self.player.vel_y:+.1f} px/s",
            f"Gravity     : {config.GRAVITY:.0f} px/s^2"
            + (" (x0.5 grace)" if self._grace_timer > 0.0 else ""),
            f"Flap force  : {config.FLAP_FORCE:.0f} px/s",
            f"Flap detected: {'YES' if flap_yes else 'no'}",
            f"Cooldown    : {cooldown}",
            f"Game state  : {self.state.value}",
        ]

    def _shake_offset(self) -> tuple[int, int]:
        if self._shake_time <= 0.0:
            return (0, 0)
        k = self._shake_time / config.SHAKE_DURATION
        mag = config.SHAKE_MAGNITUDE * k
        return (int(random.uniform(-mag, mag)),
                int(random.uniform(-mag, mag)))

    # ==================================================================
    # High score
    # ==================================================================
    def _load_high_score(self) -> int:
        """Doc high score; file thieu / hong -> tra ve 0."""
        try:
            with open(config.HIGH_SCORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return max(0, int(data.get("high_score", 0)))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return 0

    def _save_high_score(self) -> None:
        try:
            os.makedirs(os.path.dirname(config.HIGH_SCORE_FILE),
                        exist_ok=True)
            with open(config.HIGH_SCORE_FILE, "w", encoding="utf-8") as f:
                json.dump({"high_score": self.high_score}, f)
        except OSError:
            pass  # Khong luu duoc cung khong duoc lam crash game
