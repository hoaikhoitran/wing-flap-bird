"""Capture screenshot THAT tu chinh renderer cua game (khong mockup).

Chay:
    python main.py --capture-readme --output docs/screenshots --no-camera

Nguyen tac:
  - Dung chinh class Game + render path that (khong dung giao dien gia).
  - Seed RNG co dinh -> ket qua tai lap duoc.
  - Khong can webcam, khong mo browser, khong debug overlay.
  - Gameplay screenshot: nhan vat that, >= 2 obstacle, score > 0, HUD that.
  - PNG lossless qua pygame.image.save.
"""
from __future__ import annotations

import logging
import random
from pathlib import Path

logger = logging.getLogger("wingflap.capture")

DT = 1.0 / 60.0
DEFAULT_SEED = 20260715


def run_capture(output_dir: str, seed: int = DEFAULT_SEED,
                include_baseline_extras: bool = False) -> int:
    """Sinh bo screenshot README. Tra ve 0 neu thanh cong."""
    random.seed(seed)

    import pygame

    import config
    from core.settings import GameSettings
    from core.version import PRIVACY_VERSION
    from game.game import Game, GameState

    config.DEBUG_MODE = False  # screenshot khong co debug overlay

    # Settings sach, doc lap voi settings that cua nguoi dung
    settings = GameSettings()
    settings.privacy_accepted_version = PRIVACY_VERSION
    settings.show_fps = False

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    game = Game(settings=settings, use_camera=False)
    saved: list[str] = []
    gameplay_ok = False

    def step(frames: int) -> None:
        for _ in range(frames):
            game._update(DT)
            game._draw()

    def snap(name: str) -> None:
        pygame.image.save(game.screen, str(out / name))
        saved.append(name)
        logger.info("Saved %s", out / name)

    try:
        # ---------------- Main menu ----------------
        game.change_state(GameState.MAIN_MENU)
        step(45)
        snap("main-menu.png")

        # ---------------- Character select (neu da co) ----------------
        if hasattr(GameState, "CHARACTER_SELECT"):
            game.change_state(GameState.CHARACTER_SELECT)
            step(45)
            snap("character-select.png")

        # ---------------- Settings ----------------
        game.change_state(GameState.SETTINGS)
        step(30)
        snap("settings.png")

        # ---------------- How to play ----------------
        game.change_state(GameState.HOW_TO_PLAY)
        step(50)
        snap("how-to-play.png")

        if include_baseline_extras:
            game.change_state(GameState.DONATE)
            step(20)
            snap("support.png")

        # ---------------- Gameplay ----------------
        game.change_state(GameState.MAIN_MENU)
        step(5)
        game.request_play()
        guard = 0
        while game.state is GameState.GET_READY and guard < 400:
            step(1)
            guard += 1

        # Autopilot: bam giua khoang trong cua cong ke tiep (an toan,
        # dao dong ~[-60, +45] px quanh tam < nua gap 105px)
        frames = 0
        while game.state is GameState.PLAYING and frames < 60 * 25:
            target_y = config.WINDOW_HEIGHT * 0.45
            for pipe in game.obstacles.pipes:
                if pipe.x + config.PIPE_WIDTH > game.player.x - 20:
                    target_y = pipe.gap_center_y
                    break
            if game.player.y > target_y + 40 and game.player.vel_y > 0:
                game._do_flap()
            step(1)
            frames += 1
            # Du dieu kien -> flap 1 nhip cho co hieu ung roi CHUP NGAY
            if game.score >= 2 and len(game.obstacles.pipes) >= 2 \
                    and game.state is GameState.PLAYING:
                game._do_flap()
                step(3)
                if game.state is GameState.PLAYING:
                    snap("gameplay.png")
                    gameplay_ok = True
                    break

        if not gameplay_ok:
            snap("gameplay.png")  # van luu de debug
            logger.error("Gameplay screenshot thieu dieu kien "
                         "(score=%d, obstacles=%d, state=%s)",
                         game.score, len(game.obstacles.pipes),
                         game.state)

        # ---------------- Game over ----------------
        guard = 0
        while game.state is GameState.PLAYING and guard < 60 * 10:
            step(1)
            guard += 1
        step(35)
        snap("game-over.png")

    finally:
        game.shutdown()

    print("Da luu screenshot:")
    for name in saved:
        print(f"  {out / name}")
    if not gameplay_ok:
        print("[LOI] gameplay.png chua dat yeu cau (score/obstacle)")
        return 1
    return 0
