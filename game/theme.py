"""WIND FESTIVAL SKY - design token tap trung cho toan bo game.

Moi mau sac / spacing / radius / shadow deu lay tu day.
KHONG hard-code mau rai rac trong tung screen nua.

Art direction:
  - 2D illustration cam giac 2.5D, hinh khoi bo tron, doc duoc khi bay nhanh.
  - Anh sang tu goc TREN-TRAI; shadow mem do xuong duoi lech PHAI.
  - Highlight canh tren, rim light nhe tach nhan vat khoi background.
  - Layer xa nhat mau & tuong phan thap (atmospheric perspective).
"""
from __future__ import annotations

# ============================================================
# PALETTE CHINH (khong dung neon)
# ============================================================
DEEP_NAVY = (0x17, 0x32, 0x4D)      # #17324D
SKY_BLUE = (0x8F, 0xD3, 0xFF)       # #8FD3FF
PALE_SKY = (0xDD, 0xF3, 0xFF)       # #DDF3FF
CREAM = (0xFF, 0xF5, 0xDC)          # #FFF5DC
MANGO = (0xFF, 0xB5, 0x47)          # #FFB547
VERMILION = (0xF3, 0x5B, 0x4B)      # #F35B4B
LEAF_GREEN = (0x5B, 0xAE, 0x68)     # #5BAE68
TEAL = (0x3D, 0x8C, 0x8E)           # #3D8C8E
DARK_INK = (0x1A, 0x26, 0x33)       # #1A2633
SOFT_SHADOW = (15, 35, 55, 71)      # rgba(15,35,55,0.28)

# ============================================================
# SEMANTIC TOKEN - UI
# ============================================================
# Nen man hinh menu (toi, de panel cream noi len)
BG_MENU = (0x14, 0x24, 0x36)
BG_MENU_TOP = (0x1B, 0x30, 0x47)

PANEL_BG = CREAM
PANEL_BORDER = DARK_INK
PANEL_DARK = (0x20, 0x38, 0x50)          # panel toi (settings, overlays)
PANEL_DARK_BORDER = (0x3A, 0x55, 0x70)

TEXT_ON_DARK = (0xF2, 0xF6, 0xFB)
TEXT_DIM_ON_DARK = (0xA8, 0xB4, 0xC4)
TEXT_ON_LIGHT = DARK_INK
TEXT_ACCENT = MANGO
TEXT_TITLE = MANGO
TEXT_DANGER = VERMILION
TEXT_SUCCESS = (0x7F, 0xD8, 0x8F)

BUTTON_BG = (0x2A, 0x44, 0x60)
BUTTON_BG_HOVER = (0x38, 0x58, 0x7C)
BUTTON_PRIMARY = MANGO
BUTTON_PRIMARY_HOVER = (0xFF, 0xC7, 0x6E)
BUTTON_TEXT_PRIMARY = DARK_INK
BUTTON_DISABLED = (0x24, 0x32, 0x42)
FOCUS_RING = MANGO

# Trang thai nhan dien (webcam border / label)
STATE_NO_POSE = (0x8A, 0x96, 0xA4)
STATE_ARMS_DOWN = (0x6F, 0xB6, 0xE8)
STATE_ARMS_UP = MANGO
STATE_FLAP = (0x6F, 0xD8, 0x84)

# ============================================================
# GAMEPLAY / WORLD
# ============================================================
SKY_TOP = SKY_BLUE
SKY_BOTTOM = PALE_SKY
GROUND_PATH = (0xE8, 0xD5, 0xA6)
GROUND_PATH_DARK = (0xD4, 0xBE, 0x8C)
GROUND_GRASS = LEAF_GREEN
GROUND_GRASS_DARK = (0x4A, 0x94, 0x57)

BAMBOO = (0xC9, 0xA8, 0x5C)          # than tre am
BAMBOO_LIGHT = (0xE2, 0xC8, 0x84)
BAMBOO_DARK = (0x9C, 0x7E, 0x40)
BAMBOO_NODE = (0x84, 0x68, 0x34)

# Atmospheric perspective: cang xa cang pha ve PALE_SKY
FAR_MOUNTAIN = (0xB9, 0xD9, 0xEF)
FAR_MOUNTAIN_2 = (0xA6, 0xCD, 0xE8)
MID_HILL = (0x8F, 0xC3, 0xA0)
VILLAGE_ROOF = (0xE8, 0x8A, 0x6A)

# ============================================================
# SPACING / RADIUS / MOTION
# ============================================================
SPACE_XS = 4
SPACE_S = 8
SPACE_M = 16
SPACE_L = 24
SPACE_XL = 40
SAFE_PAD = 24            # le an toan quanh man hinh

RADIUS_S = 8
RADIUS_M = 12
RADIUS_L = 18

# Game feel (skill game-feel: transient, ease-out, khong lam dung)
HOVER_SCALE = 1.02
PRESS_SCALE = 0.97
TRANSITION_S = 0.20      # chuyen man hinh 150-250ms
EASE_POP = 0.12          # score pop
SHAKE_TRAUMA_HIT = 0.55  # trauma khi va cham (decay ve 0)
