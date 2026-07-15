"""Sinh icon rieng cho Wing Flap Bird (khong dung asset ban quyen).

Ve chim bang pygame primitives o 256x256 roi xuat:
  - assets/icon/wing_flap_bird.png  (logo / preview)
  - assets/icon/wing_flap_bird.ico  (icon exe, nhieu kich thuoc)

Chay mot lan (can Pillow - co trong requirements-dev.txt):
  python scripts/generate_icon.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "icon"

# Mau dong bo voi player.py
OUTLINE = (60, 40, 10)
BODY = (255, 210, 40)
BODY_DARK = (225, 160, 20)
BELLY = (255, 245, 205)
WING = (255, 140, 30)
BEAK = (255, 110, 30)
SKY = (105, 185, 240)


def draw_icon(size: int = 256) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    s = size / 256.0

    def S(*vals: float) -> list[int]:
        return [int(v * s) for v in vals]

    # Nen tron bau troi
    pygame.draw.circle(surf, SKY, S(128, 128), int(124 * s))
    pygame.draw.circle(surf, (70, 130, 190), S(128, 128), int(124 * s),
                       max(2, int(8 * s)))

    # Than chim (phong to tu art player.py)
    pygame.draw.ellipse(surf, OUTLINE, S(30, 62, 200, 150))
    pygame.draw.polygon(surf, OUTLINE,
                        [S(10, 96), S(64, 118), S(18, 152)])
    pygame.draw.polygon(surf, BODY_DARK,
                        [S(20, 102), S(60, 118), S(26, 142)])
    pygame.draw.ellipse(surf, BODY, S(40, 72, 180, 130))
    pygame.draw.ellipse(surf, BELLY, S(66, 134, 118, 58))
    # Canh dang vo len
    pygame.draw.polygon(surf, WING,
                        [S(74, 116), S(150, 100), S(112, 44)])
    pygame.draw.polygon(surf, OUTLINE,
                        [S(74, 116), S(150, 100), S(112, 44)],
                        max(2, int(6 * s)))
    # Mo
    pygame.draw.polygon(surf, OUTLINE,
                        [S(196, 96), S(252, 118), S(196, 140)])
    pygame.draw.polygon(surf, BEAK,
                        [S(200, 102), S(242, 118), S(200, 134)])
    # Mat
    pygame.draw.circle(surf, OUTLINE, S(168, 96), int(34 * s))
    pygame.draw.circle(surf, (255, 255, 255), S(168, 96), int(27 * s))
    pygame.draw.circle(surf, (25, 25, 25), S(178, 96), int(11 * s))
    return surf


def main() -> None:
    pygame.init()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUT_DIR / "wing_flap_bird.png"
    pygame.image.save(draw_icon(256), str(png_path))
    print(f"Da tao {png_path}")

    from PIL import Image
    img = Image.open(png_path)
    ico_path = OUT_DIR / "wing_flap_bird.ico"
    img.save(ico_path, format="ICO",
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                    (64, 64), (128, 128), (256, 256)])
    print(f"Da tao {ico_path}")


if __name__ == "__main__":
    main()
