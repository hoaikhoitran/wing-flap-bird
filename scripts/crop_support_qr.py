"""Crop the QR nhan tien tu poster MBBank goc (developer cung cap).

RANG BUOC (xem PRIVACY/yeu cau developer):
  - CHI crop pixel nguyen ban bang PIL Image.crop() - phep copy vung anh,
    KHONG resample, KHONG filter, KHONG rotate, KHONG sharpen/denoise.
  - KHONG tao lai / decode / OCR ma QR.
  - File goc assets/support/mbbank-qr-original.png duoc GIU NGUYEN.

Input : assets/support/mbbank-qr-original.png  (1184x2560)
Output: assets/support/vietqr-support.png      (the QR phia tren)
        docs/assets/vietqr-support.png         (ban sao cho GitHub Pages)

Chay:  python scripts/crop_support_qr.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL = ROOT / "assets" / "support" / "mbbank-qr-original.png"
CROPPED = ROOT / "assets" / "support" / "vietqr-support.png"
DOCS_COPY = ROOT / "docs" / "assets" / "vietqr-support.png"

# Bien the QR (hinh chu nhat bo tron phia tren poster) do bang tay tren
# anh goc 1184x2560, da cong them le an toan ~10px moi phia de giu nguyen
# quiet zone + bong do cua the. Phan con khi / nui / nen trang tri phia
# duoi bi loai bo.
CROP_BOX = (150, 378, 1040, 1585)  # (left, top, right, bottom)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def main() -> int:
    if not ORIGINAL.exists():
        print(f"[LOI] Khong tim thay anh goc: {ORIGINAL}")
        return 1

    with Image.open(ORIGINAL) as img:
        original_size = img.size
        if CROP_BOX[2] > img.width or CROP_BOX[3] > img.height:
            print("[LOI] CROP_BOX vuot ra ngoai anh goc")
            return 1
        # crop() = copy vung pixel nguyen ban - khong resample/filter
        card = img.crop(CROP_BOX)
        CROPPED.parent.mkdir(parents=True, exist_ok=True)
        card.save(CROPPED, format="PNG")

    # Ban sao cho GitHub Pages (docs/)
    DOCS_COPY.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CROPPED, DOCS_COPY)

    # ---------------- Kiem tra tu dong sau crop ----------------
    errors: list[str] = []
    if not CROPPED.exists() or CROPPED.stat().st_size == 0:
        errors.append("File crop khong ton tai hoac rong")
    else:
        if CROPPED.read_bytes()[:8] != PNG_SIGNATURE:
            errors.append("File crop khong phai PNG hop le")
        with Image.open(CROPPED) as check:
            w, h = check.size
            if w <= 300 or h <= 300:
                errors.append(f"Kich thuoc qua nho: {w}x{h}")
            expected = (CROP_BOX[2] - CROP_BOX[0], CROP_BOX[3] - CROP_BOX[1])
            if (w, h) != expected:
                errors.append(f"Kich thuoc {w}x{h} != crop box {expected}"
                              " (anh bi keo meo?)")

    # Pygame load duoc (headless)
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    pygame.init()
    try:
        surf = pygame.image.load(str(CROPPED))
        pg_size = surf.get_size()
    except Exception as exc:
        errors.append(f"Pygame khong load duoc: {exc}")
        pg_size = None
    pygame.quit()

    print(f"Original : {ORIGINAL}  {original_size[0]}x{original_size[1]}")
    print(f"Cropped  : {CROPPED}  "
          f"{CROP_BOX[2]-CROP_BOX[0]}x{CROP_BOX[3]-CROP_BOX[1]}")
    print(f"Docs copy: {DOCS_COPY}")
    print(f"Pygame   : {'OK ' + str(pg_size) if pg_size else 'FAILED'}")
    if errors:
        for err in errors:
            print(f"[LOI] {err}")
        return 1
    print("Tat ca kiem tra tu dong: PASS")
    print("LUU Y: developer PHAI tu quet thu bang app ngan hang tren dien "
          "thoai truoc khi release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
