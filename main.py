"""Diem khoi chay game Wing Flap.

Cach chay:
    python main.py                # mac dinh: webcam index trong config.py
    python main.py --camera 1     # chon webcam khac
    python main.py --no-camera    # bo qua webcam, choi bang phim SPACE
    python main.py --no-debug     # tat overlay debug
"""
from __future__ import annotations

import argparse
import os
import sys

# Dam bao duong dan tuong doi (data/, assets/) luon dung du chay tu dau
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import config  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wing Flap - vo hai tay truoc webcam de bay!")
    parser.add_argument("--camera", type=int, default=config.CAMERA_INDEX,
                        help="Chi so webcam (0, 1, 2...). Mac dinh: "
                             f"{config.CAMERA_INDEX}")
    parser.add_argument("--no-camera", action="store_true",
                        help="Khong dung webcam, choi bang phim SPACE")
    parser.add_argument("--debug", dest="debug", action="store_true",
                        default=None, help="Bat overlay debug")
    parser.add_argument("--no-debug", dest="debug", action="store_false",
                        help="Tat overlay debug")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.debug is not None:
        config.DEBUG_MODE = args.debug

    # pre_init truoc pygame.init() de am thanh tong hop khong bi tre
    try:
        pygame.mixer.pre_init(44100, -16, 2, 512)
    except Exception:
        pass

    # Import Game sau khi da chinh config (Game doc config luc khoi tao)
    from game.game import Game

    try:
        game = Game(camera_index=args.camera,
                    use_camera=not args.no_camera)
    except Exception as exc:
        print(f"[LOI] Khong khoi tao duoc game: {exc}", file=sys.stderr)
        return 1

    game.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
