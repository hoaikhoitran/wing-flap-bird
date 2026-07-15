"""Diem khoi chay Wing Flap Bird.

Cach chay (developer):
    python main.py                # binh thuong
    python main.py --camera 1     # ep camera index (khong luu vao settings)
    python main.py --no-camera    # bo qua webcam, choi bang SPACE
    python main.py --debug        # bat overlay debug + log DEBUG
    python main.py --smoke        # chay ~120 frame roi tu thoat (CI/smoke test)

Nguoi dung cuoi chi can mo WingFlapBird.exe - khong can Python/terminal.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wing Flap Bird")
    parser.add_argument("--camera", type=int, default=None,
                        help="Ep camera index (mac dinh: theo Settings)")
    parser.add_argument("--no-camera", action="store_true",
                        help="Khong dung webcam, choi bang phim SPACE")
    parser.add_argument("--debug", action="store_true",
                        help="Bat overlay debug va log muc DEBUG")
    parser.add_argument("--smoke", action="store_true",
                        help="Smoke test: chay ~120 frame roi thoat")
    parser.add_argument("--capture-readme", action="store_true",
                        help="Sinh screenshot README bang renderer that")
    parser.add_argument("--output", default="docs/screenshots",
                        help="Thu muc luu screenshot (capture mode)")
    parser.add_argument("--capture-baseline", action="store_true",
                        help="Kem screenshot phu (Support...) cho audit")
    return parser.parse_args()


def _show_error_screen(logger: logging.Logger) -> None:
    """Man hinh loi than thien: khong hien stack trace dai cho nguoi dung.

    Phim: O - mo thu muc log, R - khoi dong lai, ESC - thoat.
    """
    import pygame

    from core.logging_config import get_log_file_path
    from core.paths import get_log_dir
    from game.i18n import tr

    try:
        if not pygame.display.get_init():
            pygame.init()
        screen = pygame.display.set_mode((700, 360))
        pygame.display.set_caption("Wing Flap Bird - Error")
        # Font bundle (khong SysFont); neu chinh font loi thi de excepthook
        # ghi log - man hinh loi khong the hien duoc trong truong hop do
        from core import font_manager as fm
        font_big = fm.get("title", 30)
        font = fm.get("body", 19)
        clock = pygame.time.Clock()
        lines = [
            (tr("error.title"), font_big, (235, 80, 70)),
            ("", font, (0, 0, 0)),
            (tr("error.body"), font, (230, 233, 240)),
            (str(get_log_file_path()), font, (150, 156, 170)),
            ("", font, (0, 0, 0)),
            (tr("error.open_log"), font, (230, 233, 240)),
            (tr("error.restart"), font, (230, 233, 240)),
            (tr("error.quit"), font, (230, 233, 240)),
        ]
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_o:
                        try:  # chi mo khi nguoi dung CHU DONG bam
                            os.startfile(str(get_log_dir()))  # noqa: S606
                        except OSError:
                            pass
                    if event.key == pygame.K_r:
                        pygame.quit()
                        os.execv(sys.executable,
                                 [sys.executable] + sys.argv)
            screen.fill((18, 22, 34))
            y = 50
            for text, f, color in lines:
                if text:
                    label = f.render(text, True, color)
                    screen.blit(label,
                                label.get_rect(center=(350, y)))
                y += 38
            pygame.display.flip()
            clock.tick(30)
    except Exception:
        logger.exception("Error screen that bai")


def _smoke_check_vision(logger: logging.Logger) -> None:
    """Xac thuc mediapipe import duoc, model bundle resolve dung va
    chay duoc 1 lan inference. Nem exception neu hong."""
    import numpy as np

    import config
    from vision.pose_tracker import (MEDIAPIPE_AVAILABLE, PoseTracker,
                                     ensure_pose_model,
                                     mediapipe_import_error)

    if not MEDIAPIPE_AVAILABLE:
        raise RuntimeError(
            f"Smoke: mediapipe khong import duoc: {mediapipe_import_error()}")
    model = ensure_pose_model(config.POSE_MODEL_COMPLEXITY)
    logger.info("Smoke: model = %s", model)
    tracker = PoseTracker(config.POSE_MODEL_COMPLEXITY)
    tracker.process(np.zeros((480, 640, 3), dtype=np.uint8))
    tracker.close()
    logger.info("Smoke: MediaPipe pose inference OK")


def main() -> int:
    args = parse_args()

    # --- Logging + global exception hook (truoc moi thu khac) ---
    from core.logging_config import (install_excepthook, log_system_info,
                                     setup_logging)
    from core.settings import GameSettings

    settings = GameSettings.load()
    debug = args.debug or settings.debug_enabled
    logger = setup_logging(debug=debug)
    install_excepthook(logger)
    log_system_info(logger)

    import config
    if args.debug:
        config.DEBUG_MODE = True

    # pre_init de am thanh tong hop khong bi tre
    import pygame
    try:
        pygame.mixer.pre_init(44100, -16, 2, 512)
    except Exception:
        pass

    if args.capture_readme:
        from tools.capture_readme import run_capture
        return run_capture(args.output,
                           include_baseline_extras=args.capture_baseline)

    from game.game import Game

    try:
        if args.smoke:
            # Smoke test phai xac thuc ca vision stack (mediapipe +
            # model bundle + 1 lan inference) vi day la phan de hong
            # nhat khi dong goi PyInstaller.
            _smoke_check_vision(logger)
        game = Game(settings=settings,
                    use_camera=not args.no_camera,
                    camera_override=args.camera)
        game.run(max_frames=120 if args.smoke else None)
        return 0
    except Exception:
        logger.exception("Loi nghiem trong - hien man hinh loi")
        if not args.smoke:
            _show_error_screen(logger)
        else:
            raise
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
