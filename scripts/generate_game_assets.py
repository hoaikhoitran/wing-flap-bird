"""Sinh TOAN BO asset art cho Wing Flap Bird - art direction WIND FESTIVAL SKY.

Chay (deterministic):
    python scripts/generate_game_assets.py --seed 20260715

Ky thuat:
  - Render 4x roi downscale LANCZOS (anti-alias).
  - Layer: fill -> outline -> shade duoi-phai -> highlight tren-trai
    -> rim light -> texture nhe.
  - Soft shadow: pre-render Gaussian blur (CHI o build-time, khong runtime).
  - PNG trong suot, KHONG nhung chu vao anh (text render bang font runtime).
  - Chi dung Pillow + math + random(seed) - khong API, khong asset ngoai.

Asset tu sinh phat hanh theo MIT cung repository.
Generator tu ghi assets/ASSET_MANIFEST.md.
"""
from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "assets" / "art"
SS = 4  # supersample

# ---------------------------------------------------------------------
# Palette (dong bo voi game/theme.py)
# ---------------------------------------------------------------------
DEEP_NAVY = (0x17, 0x32, 0x4D)
SKY_BLUE = (0x8F, 0xD3, 0xFF)
PALE_SKY = (0xDD, 0xF3, 0xFF)
CREAM = (0xFF, 0xF5, 0xDC)
MANGO = (0xFF, 0xB5, 0x47)
VERMILION = (0xF3, 0x5B, 0x4B)
LEAF_GREEN = (0x5B, 0xAE, 0x68)
TEAL = (0x3D, 0x8C, 0x8E)
DARK_INK = (0x1A, 0x26, 0x33)
FAR_MOUNTAIN = (0xB9, 0xD9, 0xEF)
FAR_MOUNTAIN_2 = (0xA6, 0xCD, 0xE8)
MID_HILL = (0x8F, 0xC3, 0xA0)
BAMBOO = (0xC9, 0xA8, 0x5C)
BAMBOO_LIGHT = (0xE2, 0xC8, 0x84)
BAMBOO_DARK = (0x9C, 0x7E, 0x40)
BAMBOO_NODE = (0x84, 0x68, 0x34)
GROUND_PATH = (0xE8, 0xD5, 0xA6)
GROUND_PATH_DARK = (0xD4, 0xBE, 0x8C)
GROUND_GRASS = LEAF_GREEN
GROUND_GRASS_DARK = (0x4A, 0x94, 0x57)

MANIFEST: list[dict] = []


# =====================================================================
# Helpers
# =====================================================================
def canvas(w: int, h: int) -> Image.Image:
    """Canvas RGBA trong suot o kich thuoc 4x."""
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


def save(img: Image.Image, rel: str, purpose: str,
         display_size: tuple[int, int] | None = None) -> None:
    """Downscale LANCZOS ve kich thuoc hien thi va luu + ghi manifest."""
    w, h = img.size
    out_size = display_size or (w // SS, h // SS)
    final = img.resize(out_size, Image.LANCZOS)
    path = ART / rel
    path.mkdir(parents=True, exist_ok=True) if path.suffix == "" else \
        path.parent.mkdir(parents=True, exist_ok=True)
    final.save(path, "PNG")
    MANIFEST.append({
        "name": path.name, "purpose": purpose, "rel": f"assets/art/{rel}",
        "gen": f"{w}x{h}", "out": f"{out_size[0]}x{out_size[1]}",
        "alpha": "yes",
    })
    print(f"  {rel}  {out_size[0]}x{out_size[1]}")


def s(*vals: float) -> list[int]:
    """Scale toa do sang he 4x."""
    return [int(round(v * SS)) for v in vals]


def apply_lighting(img: Image.Image, top_light: float = 0.20,
                   bottom_shade: float = 0.13,
                   rim_right: float = 0.0) -> Image.Image:
    """Highlight tren-trai + shade duoi-phai + rim light, mask theo alpha.

    Anh sang tu goc tren-trai theo art direction.
    """
    w, h = img.size
    alpha = img.getchannel("A")

    # Gradient sang tren -> toi duoi, lech theo truc trai-phai nhe
    grad = Image.new("L", (w, h), 0)
    gdraw = ImageDraw.Draw(grad)
    for y in range(h):
        k = y / max(1, h - 1)
        val = int(255 * (top_light * max(0.0, 1.0 - k * 1.8)))
        gdraw.line([(0, y), (w, y)], fill=val)
    light = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    light.putalpha(Image.composite(grad, Image.new("L", (w, h), 0), alpha))
    img = Image.alpha_composite(img, light)

    grad2 = Image.new("L", (w, h), 0)
    g2 = ImageDraw.Draw(grad2)
    for y in range(h):
        k = y / max(1, h - 1)
        val = int(255 * (bottom_shade * max(0.0, (k - 0.55) / 0.45)))
        g2.line([(0, y), (w, y)], fill=val)
    shade = Image.new("RGBA", (w, h), (10, 20, 35, 0))
    shade.putalpha(Image.composite(grad2, Image.new("L", (w, h), 0), alpha))
    img = Image.alpha_composite(img, shade)

    if rim_right > 0:
        # Rim light: phan alpha lo ra khi dich silhouette sang trai
        shift = Image.new("L", (w, h), 0)
        shift.paste(alpha, (-3 * SS, 1 * SS))
        rim_mask = Image.composite(
            Image.new("L", (w, h), 0), alpha, shift)
        rim = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        rim.putalpha(rim_mask.point(lambda a: int(a * rim_right)))
        img = Image.alpha_composite(img, rim)
    return img


def soft_shadow_of(img: Image.Image, blur: int, color=(15, 35, 55),
                   opacity: float = 0.28) -> Image.Image:
    """Pre-render soft shadow tu silhouette (Gaussian o build-time)."""
    alpha = img.getchannel("A").point(lambda a: int(a * opacity))
    sh = Image.new("RGBA", img.size, (*color, 0))
    sh.putalpha(alpha)
    return sh.filter(ImageFilter.GaussianBlur(blur * SS))


def noise_texture(img: Image.Image, rng: random.Random,
                  amount: int = 60, alpha: int = 7) -> Image.Image:
    """Texture rat nhe (cham sang/toi thua) - khong lam ban hinh."""
    w, h = img.size
    mask = img.getchannel("A")
    draw = ImageDraw.Draw(img)
    for _ in range(amount):
        x, y = rng.randrange(w), rng.randrange(h)
        if mask.getpixel((x, y)) > 128:
            c = (255, 255, 255, alpha) if rng.random() < 0.5 \
                else (20, 30, 45, alpha)
            r = rng.randint(2, 4) * SS // 2
            draw.ellipse([x - r, y - r, x + r, y + r], fill=c)
    return img


# =====================================================================
# NHAN VAT - 5 loai chim, parametric
# =====================================================================
class BirdSpec:
    def __init__(self, id: str, body, belly, wing, beak, accent,
                 body_w=54.0, body_h=40.0, tail="short", neck=0.0,
                 ear_tufts=False, eye_scale=1.0, head_scale=1.0,
                 beak_len=14.0):
        self.id = id
        self.body, self.belly, self.wing = body, belly, wing
        self.beak_color, self.accent = beak, accent
        self.body_w, self.body_h = body_w, body_h
        self.tail, self.neck = tail, neck
        self.ear_tufts, self.eye_scale = ear_tufts, eye_scale
        self.head_scale, self.beak_len = head_scale, beak_len


BIRDS = [
    # Chim en: navy + bung kem, duoi che, canh nhon
    BirdSpec("swallow", body=(0x24, 0x46, 0x6E), belly=CREAM,
             wing=(0x18, 0x33, 0x52), beak=(0xFF, 0x9A, 0x3C),
             accent=VERMILION, body_w=54, body_h=38, tail="split"),
    # Vit vang: tron, mo cam, canh ngan, silhouette rong
    BirdSpec("duck", body=(0xFF, 0xD4, 0x4F), belly=(0xFF, 0xEC, 0xB0),
             wing=(0xF0, 0xB8, 0x2E), beak=(0xFF, 0x8A, 0x2E),
             accent=MANGO, body_w=60, body_h=46, tail="short",
             head_scale=1.05, beak_len=17),
    # Co trang: mo do cam, co cong gon
    BirdSpec("stork", body=(0xF6, 0xF9, 0xFC), belly=(0xE8, 0xEF, 0xF5),
             wing=(0xCF, 0xDD, 0xE8), beak=(0xE8, 0x50, 0x38),
             accent=VERMILION, body_w=56, body_h=36, tail="short",
             neck=10, beak_len=20, head_scale=0.9),
    # Cu meo: nau tron, mat lon, tai nho
    BirdSpec("owl", body=(0x9A, 0x6B, 0x44), belly=(0xD9, 0xB8, 0x8C),
             wing=(0x7C, 0x54, 0x33), beak=(0xE8, 0xA0, 0x38),
             accent=TEAL, body_w=56, body_h=48, tail="fan",
             ear_tufts=True, eye_scale=1.7, beak_len=9),
    # Chim se: nau am, bung sang, nho gon
    BirdSpec("sparrow", body=(0xB4, 0x7E, 0x4E), belly=(0xF2, 0xE2, 0xC4),
             wing=(0x8E, 0x5F, 0x38), beak=(0x6B, 0x4A, 0x2C),
             accent=MANGO, body_w=50, body_h=38, tail="short",
             head_scale=0.95, beak_len=10),
]

FRAME_W, FRAME_H = 96, 80  # kich thuoc hien thi 1 frame


def draw_bird(spec: BirdSpec, wing_pose: float, body_dy: float = 0.0,
              stretch: float = 1.0, eye: str = "open",
              tilt: float = 0.0) -> Image.Image:
    """Ve 1 frame chim. wing_pose: -1 (canh ha het) .. +1 (canh nang het)."""
    img = canvas(FRAME_W, FRAME_H)
    d = ImageDraw.Draw(img)
    cx, cy = FRAME_W / 2 - 4, FRAME_H / 2 + 4 + body_dy
    bw = spec.body_w * (2.0 - stretch)   # stretch doc -> hep ngang
    bh = spec.body_h * stretch
    out = DARK_INK
    ow = 3  # do day outline (don vi display px)

    # ---- Duoi (sau than) ----
    tail_y = cy
    if spec.tail == "split":
        d.polygon(s(cx - bw / 2 + 4, tail_y - 3, cx - bw / 2 - 16, tail_y - 10,
                    cx - bw / 2 - 8, tail_y, cx - bw / 2 - 16, tail_y + 8),
                  fill=spec.wing, outline=out, width=ow * SS)
    elif spec.tail == "fan":
        for ang in (-18, 0, 18):
            a = math.radians(180 + ang)
            tx = cx - bw / 2 + 4 + 15 * math.cos(a)
            ty = tail_y + 15 * math.sin(a)
            d.line(s(cx - bw / 2 + 5, tail_y, tx, ty),
                   fill=out, width=int(7.5 * SS))
            d.line(s(cx - bw / 2 + 5, tail_y, tx, ty),
                   fill=spec.wing, width=int(5 * SS))
    else:  # short
        d.polygon(s(cx - bw / 2 + 5, tail_y - 6, cx - bw / 2 - 11, tail_y - 2,
                    cx - bw / 2 + 3, tail_y + 6),
                  fill=spec.wing, outline=out, width=ow * SS)

    # ---- Than ----
    body_box = s(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
    d.ellipse(body_box, fill=spec.body, outline=out, width=ow * SS)
    # Bung
    d.ellipse(s(cx - bw * 0.28, cy - bh * 0.05,
                cx + bw * 0.34, cy + bh * 0.46),
              fill=spec.belly)

    # ---- Dau ----
    hs = spec.head_scale
    hx = cx + bw * 0.36
    hy = cy - bh * 0.34 - spec.neck
    hr = 15 * hs
    if spec.neck > 0:  # co cong gon (stork)
        d.line(s(cx + bw * 0.22, cy - bh * 0.12, hx - 3, hy + hr * 0.6),
               fill=out, width=int(12 * SS))
        d.line(s(cx + bw * 0.22, cy - bh * 0.12, hx - 3, hy + hr * 0.6),
               fill=spec.body, width=int(9 * SS))
    d.ellipse(s(hx - hr, hy - hr, hx + hr, hy + hr),
              fill=spec.body, outline=out, width=ow * SS)
    if spec.ear_tufts:
        for sx in (-1, 1):
            ex = hx + sx * hr * 0.62
            d.polygon(s(ex - 4, hy - hr * 0.55, ex + sx * 3, hy - hr - 7,
                        ex + 4, hy - hr * 0.55),
                      fill=spec.body, outline=out, width=ow * SS)

    # ---- Mo ----
    bl = spec.beak_len
    d.polygon(s(hx + hr - 3, hy - 4.5, hx + hr + bl, hy + 1,
                hx + hr - 3, hy + 6),
              fill=spec.beak_color, outline=out, width=ow * SS)

    # ---- Mat ----
    er = 5.5 * spec.eye_scale
    ex, ey = hx + hr * 0.28, hy - hr * 0.12
    if spec.eye_scale > 1.3:  # owl: vien mat sang
        d.ellipse(s(ex - er - 3, ey - er - 3, ex + er + 3, ey + er + 3),
                  fill=spec.belly, outline=out, width=ow * SS)
    if eye == "open":
        d.ellipse(s(ex - er, ey - er, ex + er, ey + er),
                  fill=(255, 255, 255), outline=out, width=2 * SS)
        d.ellipse(s(ex + er * 0.15 - 2.6, ey - 2.6, ex + er * 0.15 + 2.6,
                    ey + 2.6), fill=DARK_INK)
        d.ellipse(s(ex + er * 0.3, ey - er * 0.55, ex + er * 0.62,
                    ey - er * 0.2), fill=(255, 255, 255))
    elif eye == "blink":
        d.line(s(ex - er, ey, ex + er, ey), fill=out, width=int(3.5 * SS))
    else:  # hurt: mat X
        r = er * 0.8
        for a, b in ((-1, -1), (-1, 1)):
            d.line(s(ex - r, ey + a * r, ex + r, ey + b * r),
                   fill=out, width=int(3.5 * SS))

    # ---- Canh (truoc than) ----
    # wing_pose: -1 ha het (duoi canh xuong duoi), +1 nang het (len tren)
    shoulder = (cx - bw * 0.08, cy - bh * 0.10)
    span = bw * 0.52
    lift = -wing_pose * bh * 0.72
    tip = (shoulder[0] - span * 0.72, shoulder[1] + lift)
    mid = (shoulder[0] - span * 0.30,
           shoulder[1] + lift * 0.45 - bh * 0.08)
    back = (shoulder[0] - span * 0.55,
            shoulder[1] + lift * 0.75 + bh * 0.16)
    d.polygon([*s(shoulder[0] + bw * 0.16, shoulder[1] + bh * 0.06),
               *s(mid[0], mid[1]), *s(tip[0], tip[1]), *s(back[0], back[1])],
              fill=spec.wing, outline=out, width=ow * SS)

    img = apply_lighting(img, rim_right=0.30)
    return img


def gen_characters(rng: random.Random) -> None:
    print("Characters:")
    for spec in BIRDS:
        frames: dict[str, list[Image.Image]] = {
            "idle": [
                draw_bird(spec, 0.15, 0),
                draw_bird(spec, 0.45, -2),
                draw_bird(spec, 0.15, 0, eye="blink"),
                draw_bird(spec, -0.20, 2),
            ],
            "flap": [
                draw_bird(spec, 0.95, -3, stretch=1.07),
                draw_bird(spec, 0.50, -1, stretch=1.03),
                draw_bird(spec, -0.75, 2, stretch=0.94),
                draw_bird(spec, -0.35, 1, stretch=0.97),
            ],
            "hurt": [
                draw_bird(spec, -0.55, 2, eye="hurt"),
                draw_bird(spec, -0.75, 5, eye="hurt", stretch=0.95),
            ],
        }
        for state, imgs in frames.items():
            strip = canvas(FRAME_W * len(imgs), FRAME_H)
            for i, frame in enumerate(imgs):
                strip.paste(frame, (i * FRAME_W * SS, 0), frame)
            save(strip, f"characters/{spec.id}/{state}.png",
                 f"{spec.id} {state} strip ({len(imgs)} frame "
                 f"{FRAME_W}x{FRAME_H})")


# =====================================================================
# BACKGROUND - cac layer parallax wrap lien mach
# =====================================================================
def periodic_hills(d: ImageDraw.ImageDraw, w: int, base_y: float,
                   amp: float, harmonics: list[tuple[float, float]],
                   color, h: int) -> None:
    """Ve dai doi/nui bang tong sin CHU KY = w -> wrap khong seam."""
    pts = []
    for x in range(0, w + SS * 8, SS * 8):
        y = base_y
        for k, phase in harmonics:
            y += amp * math.sin(2 * math.pi * k * x / w + phase) / k
        pts.append((x, y))
    poly = [(0, h)] + pts + [(w, h)]
    d.polygon(poly, fill=color)


def blob_cloud(d: ImageDraw.ImageDraw, x: float, y: float, scale: float,
               color, w: int) -> None:
    """May 3 khoi tron; ve tai x va x±w de wrap."""
    for ox in (x - w, x, x + w):
        d.ellipse([ox - 60 * scale * SS, y - 16 * scale * SS,
                   ox + 60 * scale * SS, y + 22 * scale * SS], fill=color)
        d.ellipse([ox - 30 * scale * SS, y - 34 * scale * SS,
                   ox + 26 * scale * SS, y + 8 * scale * SS], fill=color)
        d.ellipse([ox + 6 * scale * SS, y - 24 * scale * SS,
                   ox + 58 * scale * SS, y + 10 * scale * SS], fill=color)


def gen_backgrounds(rng: random.Random) -> None:
    print("Backgrounds:")
    W = 1000

    # ---- sky.png: gradient pre-render (khong can wrap) ----
    sky = Image.new("RGBA", (W, 700))
    d = ImageDraw.Draw(sky)
    for y in range(700):
        k = y / 699
        c = tuple(int(SKY_BLUE[i] + (PALE_SKY[i] - SKY_BLUE[i]) * k)
                  for i in range(3))
        d.line([(0, y), (W, y)], fill=(*c, 255))
    path = ART / "backgrounds"
    path.mkdir(parents=True, exist_ok=True)
    sky.save(path / "sky.png", "PNG")
    MANIFEST.append({"name": "sky.png", "purpose": "gradient troi (layer 1)",
                     "rel": "assets/art/backgrounds/sky.png",
                     "gen": "1000x700", "out": "1000x700", "alpha": "no"})
    print("  backgrounds/sky.png  1000x700")

    # ---- clouds_far: nhat, it tuong phan (atmospheric) ----
    img = canvas(W, 220)
    d = ImageDraw.Draw(img)
    for i in range(6):
        x = rng.uniform(0, W) * SS
        y = rng.uniform(40, 170) * SS
        blob_cloud(d, x, y, rng.uniform(0.7, 1.1),
                   (*PALE_SKY, rng.randint(120, 160)), W * SS)
    save(img, "backgrounds/clouds_far.png",
         "may rat xa - parallax cham nhat", (W, 220))

    # ---- mountains_far: 2 dai nui nhat ----
    img = canvas(W, 260)
    d = ImageDraw.Draw(img)
    periodic_hills(d, W * SS, 120 * SS, 46 * SS,
                   [(1, 0.4), (2, 2.1), (3, 4.4)],
                   (*FAR_MOUNTAIN, 255), 260 * SS)
    periodic_hills(d, W * SS, 175 * SS, 40 * SS,
                   [(1, 2.9), (2, 0.7), (4, 1.9)],
                   (*FAR_MOUNTAIN_2, 255), 260 * SS)
    save(img, "backgrounds/mountains_far.png",
         "nui xa mau nhat (atmospheric)", (W, 260))

    # ---- clouds_mid ----
    img = canvas(W, 240)
    d = ImageDraw.Draw(img)
    for i in range(4):
        x = rng.uniform(0, W) * SS
        y = rng.uniform(50, 180) * SS
        blob_cloud(d, x, y, rng.uniform(0.9, 1.4),
                   (255, 255, 255, rng.randint(200, 235)), W * SS)
    save(img, "backgrounds/clouds_mid.png", "may giua sang hon", (W, 240))

    # ---- kites_mid: dieu gio le hoi ----
    img = canvas(W, 300)
    d = ImageDraw.Draw(img)
    kite_colors = [VERMILION, MANGO, TEAL]
    for i, kc in enumerate(kite_colors):
        kx = (120 + i * 330 + rng.uniform(-30, 30)) * SS
        ky = (60 + rng.uniform(0, 60)) * SS
        kw, kh = 26 * SS, 34 * SS
        d.polygon([(kx, ky - kh), (kx + kw, ky), (kx, ky + kh),
                   (kx - kw, ky)], fill=(*kc, 255),
                  outline=(*DARK_INK, 255), width=2 * SS)
        d.line([(kx, ky - kh), (kx, ky + kh)],
               fill=(*DARK_INK, 160), width=SS)
        d.line([(kx - kw, ky), (kx + kw, ky)],
               fill=(*DARK_INK, 160), width=SS)
        # duoi dieu cong + no
        prev = (kx, ky + kh)
        for t in range(1, 5):
            nx = kx + 18 * SS * math.sin(t * 1.3 + i)
            ny = ky + kh + t * 26 * SS
            d.line([prev, (nx, ny)], fill=(*DARK_INK, 140), width=SS)
            d.ellipse([nx - 5 * SS, ny - 3 * SS, nx + 5 * SS, ny + 3 * SS],
                      fill=(*kite_colors[(i + t) % 3], 230))
            prev = (nx, ny)
    save(img, "backgrounds/kites_mid.png",
         "dieu gio le hoi (diem nhan WIND FESTIVAL)", (W, 300))

    # ---- village_mid: doi + nha + cay ----
    img = canvas(W, 240)
    d = ImageDraw.Draw(img)
    periodic_hills(d, W * SS, 120 * SS, 34 * SS,
                   [(1, 1.2), (2, 3.8), (3, 0.5)],
                   (*MID_HILL, 255), 240 * SS)
    for i in range(4):  # nha nho mai do
        hx = rng.uniform(60, W - 60) * SS
        hy = (150 + rng.uniform(-14, 14)) * SS
        hw, hh = 26 * SS, 20 * SS
        d.rectangle([hx - hw / 2, hy - hh, hx + hw / 2, hy],
                    fill=(*CREAM, 255), outline=(*DARK_INK, 200),
                    width=SS)
        d.polygon([(hx - hw * 0.65, hy - hh), (hx, hy - hh - 15 * SS),
                   (hx + hw * 0.65, hy - hh)],
                  fill=(0xE8, 0x8A, 0x6A, 255),
                  outline=(*DARK_INK, 200), width=SS)
    for i in range(6):  # cay tan tron
        tx = rng.uniform(30, W - 30) * SS
        ty = (158 + rng.uniform(-18, 10)) * SS
        d.line([(tx, ty), (tx, ty - 22 * SS)],
               fill=(*BAMBOO_DARK, 255), width=3 * SS)
        d.ellipse([tx - 15 * SS, ty - 44 * SS, tx + 15 * SS, ty - 14 * SS],
                  fill=(*TEAL, 255), outline=(*DARK_INK, 170), width=SS)
    save(img, "backgrounds/village_mid.png", "lang + doi lop giua", (W, 240))

    # ---- foliage_near: la truoc gan (di nhanh hon) ----
    img = canvas(W, 150)
    d = ImageDraw.Draw(img)
    for i in range(9):
        x = rng.uniform(0, W) * SS
        yb = 150 * SS
        h = rng.uniform(50, 110) * SS
        w2 = rng.uniform(30, 55) * SS
        color = GROUND_GRASS_DARK if rng.random() < 0.5 else LEAF_GREEN
        for ox in (x - W * SS, x, x + W * SS):
            d.ellipse([ox - w2, yb - h, ox + w2, yb + h * 0.4],
                      fill=(*color, 255))
    save(img, "backgrounds/foliage_near.png",
         "bui la foreground (parallax nhanh)", (W, 150))

    # ---- ground_near: duong dat + co ----
    img = canvas(W, 84)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W * SS, 84 * SS], fill=(*GROUND_PATH, 255))
    d.rectangle([0, 0, W * SS, 20 * SS], fill=(*GROUND_GRASS, 255))
    d.rectangle([0, 18 * SS, W * SS, 23 * SS],
                fill=(*GROUND_GRASS_DARK, 255))
    for i in range(26):  # nhanh co nho tren mep
        x = rng.uniform(0, W) * SS
        for ox in (x - W * SS, x, x + W * SS):
            d.polygon([(ox, 20 * SS), (ox + 4 * SS, 4 * SS),
                       (ox + 8 * SS, 20 * SS)],
                      fill=(*GROUND_GRASS_DARK, 255))
    for i in range(12):  # van dat + soi
        x = rng.uniform(0, W) * SS
        y = rng.uniform(34, 74) * SS
        w2 = rng.uniform(18, 46) * SS
        for ox in (x - W * SS, x, x + W * SS):
            d.ellipse([ox - w2, y - 4 * SS, ox + w2, y + 4 * SS],
                      fill=(*GROUND_PATH_DARK, 255))
    save(img, "backgrounds/ground_near.png",
         "mat dat cuon (path + co)", (W, 84))


# =====================================================================
# OBSTACLE - Bamboo Wind Gate
# =====================================================================
def gen_obstacles(rng: random.Random) -> None:
    print("Obstacles:")
    GW, GH = 92, 620  # than cot (display)

    def bamboo_column() -> Image.Image:
        img = canvas(GW, GH)
        d = ImageDraw.Draw(img)
        # 3 than tre bo lai
        stalks = [(4, 34), (30, 62), (56, 88)]
        for x0, x1 in stalks:
            d.rounded_rectangle(s(x0, 0, x1, GH), radius=10 * SS,
                                fill=BAMBOO, outline=DARK_INK,
                                width=3 * SS)
            # highlight trai + shade phai trong tung than
            d.rounded_rectangle(s(x0 + 3, 2, x0 + 9, GH - 2),
                                radius=6 * SS, fill=BAMBOO_LIGHT)
            d.rounded_rectangle(s(x1 - 8, 2, x1 - 3, GH - 2),
                                radius=6 * SS, fill=BAMBOO_DARK)
        # dot tre (node) so le
        for x0, x1 in stalks:
            offset = rng.uniform(0, 40)
            y = offset
            while y < GH:
                d.rounded_rectangle(s(x0 - 1, y, x1 + 1, y + 6),
                                    radius=3 * SS, fill=BAMBOO_NODE,
                                    outline=DARK_INK, width=SS)
                y += rng.uniform(64, 86)
        return apply_lighting(img, top_light=0.10, bottom_shade=0.10)

    save(bamboo_column(), "obstacles/bamboo_gate_top.png",
         "cot tre tren (crop theo chieu cao runtime)")
    save(bamboo_column(), "obstacles/bamboo_gate_bottom.png",
         "cot tre duoi (crop theo chieu cao runtime)")

    # Cap: thanh ngang buoc day o mep khoang trong
    cap = canvas(108, 34)
    d = ImageDraw.Draw(cap)
    d.rounded_rectangle(s(2, 6, 106, 30), radius=10 * SS, fill=BAMBOO_LIGHT,
                        outline=DARK_INK, width=3 * SS)
    d.rounded_rectangle(s(2, 6, 106, 14), radius=8 * SS,
                        fill=(255, 255, 255, 70))
    for x in (22, 54, 86):  # day buoc
        d.rectangle(s(x - 4, 4, x + 4, 32), fill=(*VERMILION, 255),
                    outline=(*DARK_INK, 255), width=SS)
    save(cap, "obstacles/gate_cap.png", "thanh ngang mep khoang trong")

    # Soft shadow cua cot (do sang phai)
    sh = canvas(46, GH)
    d = ImageDraw.Draw(sh)
    for x in range(46 * SS):
        a = int(80 * max(0.0, 1.0 - x / (46 * SS)))
        d.line([(x, 0), (x, GH * SS)], fill=(15, 35, 55, a))
    save(sh, "obstacles/gate_shadow.png",
         "shadow mem do ben phai cot", (46, GH))

    # Ribbon co gio o mep gap
    for name, color in (("ribbon_red", VERMILION), ("ribbon_yellow", MANGO)):
        img = canvas(46, 30)
        d = ImageDraw.Draw(img)
        d.polygon(s(2, 4, 44, 10, 30, 15, 44, 20, 2, 26),
                  fill=color, outline=DARK_INK, width=2 * SS)
        img = apply_lighting(img, top_light=0.22, bottom_shade=0.10)
        save(img, f"obstacles/{name}.png", "co lua bay o mep khoang trong")


# =====================================================================
# EFFECTS
# =====================================================================
def gen_effects(rng: random.Random) -> None:
    print("Effects:")
    # feather
    img = canvas(26, 20)
    d = ImageDraw.Draw(img)
    d.ellipse(s(1, 5, 23, 17), fill=CREAM, outline=DARK_INK, width=2 * SS)
    d.line(s(4, 11, 21, 10), fill=(*BAMBOO_DARK, 200), width=SS)
    save(img, "effects/feather.png", "long roi khi flap")

    # wind streak
    img = canvas(70, 16)
    d = ImageDraw.Draw(img)
    for x in range(70 * SS):
        a = int(150 * math.sin(math.pi * x / (70 * SS)))
        d.line([(x, 6 * SS), (x, 10 * SS)], fill=(255, 255, 255, a))
    save(img, "effects/wind_streak.png", "vet gio ngang")

    # sparkle 4 canh
    img = canvas(22, 22)
    d = ImageDraw.Draw(img)
    c = 11
    d.polygon(s(c, 1, c + 2.5, c - 2.5, 21, c, c + 2.5, c + 2.5,
                c, 21, c - 2.5, c + 2.5, 1, c, c - 2.5, c - 2.5),
              fill=(255, 245, 200, 255))
    d.ellipse(s(c - 2, c - 2, c + 2, c + 2), fill=(255, 255, 255, 255))
    save(img, "effects/sparkle.png", "lap lanh khi ghi diem")

    # flap ring (thay ve circle runtime)
    img = canvas(110, 110)
    d = ImageDraw.Draw(img)
    for i in range(6):
        a = 200 - i * 32
        d.ellipse(s(6 + i, 6 + i, 104 - i, 104 - i),
                  outline=(255, 255, 255, max(0, a)), width=2 * SS)
    save(img, "effects/flap_ring.png", "vong pulse khi flap")

    # contact shadow (pre-blur)
    base = canvas(140, 40)
    d = ImageDraw.Draw(base)
    d.ellipse(s(10, 8, 130, 32), fill=(15, 35, 55, 255))
    sh = soft_shadow_of(base, blur=4, opacity=0.55)
    save(sh, "effects/contact_shadow.png",
         "bong tiep dat duoi nhan vat", (140, 40))


# =====================================================================
# UI
# =====================================================================
def gen_ui(rng: random.Random) -> None:
    print("UI:")
    # panel cream + shadow
    pw, ph = 560, 400
    panel = canvas(pw, ph)
    d = ImageDraw.Draw(panel)
    d.rounded_rectangle(s(4, 4, pw - 4, ph - 4), radius=18 * SS,
                        fill=CREAM, outline=DARK_INK, width=3 * SS)
    d.rounded_rectangle(s(10, 10, pw - 10, 64), radius=12 * SS,
                        fill=(255, 255, 255, 90))
    save(panel, "ui/panel.png", "panel cream 2.5D (scale theo nhu cau)")
    save(soft_shadow_of(panel, blur=6, opacity=0.35), "ui/panel_shadow.png",
         "shadow panel pre-render", (pw, ph))

    # buttons
    bw, bh = 400, 76
    def button(pressed: bool) -> Image.Image:
        img = canvas(bw, bh)
        d = ImageDraw.Draw(img)
        base = MANGO if not pressed else (0xE0, 0x96, 0x2E)
        dy = 3 if pressed else 0
        d.rounded_rectangle(s(4, 8 + dy, bw - 4, bh - 4), radius=16 * SS,
                            fill=(0xB8, 0x76, 0x1E), )
        d.rounded_rectangle(s(4, 4 + dy, bw - 4, bh - 9 + dy),
                            radius=16 * SS, fill=base,
                            outline=DARK_INK, width=3 * SS)
        if not pressed:
            d.rounded_rectangle(s(12, 9, bw - 12, 28), radius=10 * SS,
                                fill=(255, 255, 255, 80))
        return img
    save(button(False), "ui/button.png", "nut chinh (mango)")
    save(button(True), "ui/button_pressed.png", "nut nhan xuong")

    # logo mark: chim en bay
    logo = draw_bird(BIRDS[0], 0.85, -2, stretch=1.05)
    save(logo, "ui/logo_mark.png", "logo mark (swallow flap)",
         (FRAME_W * 2, FRAME_H * 2))

    # icons strip: play / gear / question / heart / camera / back
    isz = 40
    icons = canvas(isz * 6, isz)
    d = ImageDraw.Draw(icons)
    white = (255, 255, 255, 255)

    def at(i, *pts):
        return [v + (i * isz if j % 2 == 0 else 0) * SS
                for j, v in enumerate(s(*pts))]
    # play
    d.polygon(at(0, 12, 8, 32, 20, 12, 32), fill=white)
    # gear
    cx = isz * 1.5
    d.ellipse(s(cx - 11, 9, cx + 11, 31), outline=white, width=4 * SS)
    for k in range(8):
        a = k * math.pi / 4
        x1, y1 = cx + 11 * math.cos(a), 20 + 11 * math.sin(a)
        x2, y2 = cx + 16 * math.cos(a), 20 + 16 * math.sin(a)
        d.line(s(x1, y1, x2, y2), fill=white, width=4 * SS)
    # question
    cx = isz * 2.5
    d.arc(s(cx - 9, 6, cx + 9, 24), start=180, end=90, fill=white,
          width=4 * SS)
    d.line(s(cx, 22, cx, 27), fill=white, width=4 * SS)
    d.ellipse(s(cx - 2, 31, cx + 2, 35), fill=white)
    # heart
    cx = isz * 3.5
    d.polygon(s(cx, 33, cx - 13, 18, cx - 6, 9, cx, 15, cx + 6, 9,
                cx + 13, 18), fill=white)
    # camera
    cx = isz * 4.5
    d.rounded_rectangle(s(cx - 14, 12, cx + 8, 30), radius=4 * SS,
                        outline=white, width=4 * SS)
    d.polygon(s(cx + 8, 17, cx + 15, 12, cx + 15, 30, cx + 8, 25),
              fill=white)
    # back arrow
    cx = isz * 5.5
    d.line(s(cx + 8, 20, cx - 8, 20), fill=white, width=4 * SS)
    d.polygon(s(cx - 12, 20, cx - 3, 13, cx - 3, 27), fill=white)
    save(icons, "ui/icons.png", "icon strip 6x40px (play/gear/?/heart/cam/back)")


# =====================================================================
# MANIFEST
# =====================================================================
def write_manifest(seed: int) -> None:
    lines = [
        "# ASSET MANIFEST — Wing Flap Bird",
        "",
        f"Sinh boi `scripts/generate_game_assets.py --seed {seed}` "
        "(deterministic).",
        "Ky thuat: Pillow, render 4x + LANCZOS, layer fill/outline/shade/",
        "highlight/rim, soft shadow pre-render. KHONG nhung text vao anh.",
        "",
        "**License: MIT** (asset tu sinh, phat hanh cung repository).",
        "Khong su dung asset ben thu ba, khong AI image API, chi phi: 0.",
        "",
        "| File | Cong dung | Goc (4x) | In-game | Alpha | Nguon |",
        "|---|---|---|---|---|---|",
    ]
    for m in MANIFEST:
        lines.append(
            f"| `{m['rel']}` | {m['purpose']} | {m['gen']} | {m['out']} "
            f"| {m['alpha']} | generate_game_assets.py |")
    lines += [
        "",
        "Cac asset khac:",
        "- `assets/fonts/BeVietnamPro-*.ttf` — SIL OFL 1.1, tai tu kho "
        "phan phoi chinh thuc google/fonts (`ofl/bevietnampro`).",
        "- `assets/support/*.png` — anh QR do developer cung cap "
        "(khong sua, khong decode).",
        "- `assets/models/pose_landmarker_lite.task` — Apache-2.0 "
        "(MediaPipe).",
        "- `assets/audio/*.wav` — sinh boi "
        "`scripts/generate_audio_assets.py`, MIT.",
        "- `assets/icon/*` — sinh boi `scripts/generate_icon.py`, MIT.",
    ]
    out = ROOT / "assets" / "ASSET_MANIFEST.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Manifest: {out} ({len(MANIFEST)} asset)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260715)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    ART.mkdir(parents=True, exist_ok=True)
    gen_characters(rng)
    gen_backgrounds(rng)
    gen_obstacles(rng)
    gen_effects(rng)
    gen_ui(rng)
    write_manifest(args.seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
