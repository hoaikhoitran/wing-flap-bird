"""
Cau hinh trung tam cho game Wing Flap.

Moi threshold / hang so dieu chinh duoc deu nam o day,
KHONG hard-code rai rac trong cac module khac.

QUY UOC DON VI (quan trong - khong tron 2 he):
  Toan bo vat ly dung he DELTA-TIME: px/s va px/s^2, moi frame nhan dt.
  Quy doi tu he per-frame @60fps:  gia_tri_per_frame * 60 (van toc)
                                   gia_tri_per_frame * 3600 (gia toc)
  Vi du: gravity 0.25 px/frame^2 = 900 px/s^2; flap -7.5 px/frame = -450 px/s.
"""
from __future__ import annotations

from dataclasses import dataclass

# ============================================================
# DEBUG
# ============================================================
# Bat overlay debug: van toc, gravity, flap detected, state machine...
# Trong game co the bam F1 de bat/tat nhanh.
DEBUG_MODE = True

# ============================================================
# Cua so & vong lap game
# ============================================================
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
TARGET_FPS = 60
GAME_TITLE = "Wing Flap - Vỗ cánh để bay!"

# ============================================================
# DO KHO: "easy" | "normal"
# ============================================================
DIFFICULTY = "easy"

EASY_CONFIG = {
    # --- Vat ly (don vi dt: px/s, px/s^2) ---
    "gravity": 800.0,          # ~0.22 px/frame^2 @60fps - roi cham, de phan ung
    "flap_force": -400.0,      # dat van toc = -400 px/s -> bay len ~100 px moi lan vo
    "max_fall_speed": 210.0,   # ~3.5 px/frame - roi tu giua man hinh xuong dat ~1.6s
    # --- Chuong ngai vat ---
    "pipe_speed": 150.0,           # ~2.5 px/frame
    "pipe_gap_min": 210.0,         # cua so cao 700px -> gap 210-250 la hop ly
    "pipe_gap_max": 250.0,
    "pipe_spawn_interval": 2.2,    # giay giua 2 lan sinh cot
    "first_obstacle_delay": 3.0,   # cot dau tien xuat hien sau 3s tu luc GO
    # --- Nhip do vao game ---
    "start_delay": 2.5,            # dem nguoc GET_READY truoc khi co trong luc
    "start_grace_period": 1.0,     # 1s dau sau GO: trong luc giam mot nua
    # --- Gesture ---
    "flap_cooldown_ms": 220,       # cho phep vo ~2-3 lan/giay
}

NORMAL_CONFIG = {
    "gravity": 1300.0,
    "flap_force": -480.0,
    "max_fall_speed": 520.0,
    "pipe_speed": 230.0,
    "pipe_gap_min": 195.0,
    "pipe_gap_max": 245.0,
    "pipe_spawn_interval": 1.5,
    "first_obstacle_delay": 2.0,
    "start_delay": 2.0,
    "start_grace_period": 0.5,
    "flap_cooldown_ms": 300,
}

_ACTIVE = EASY_CONFIG if DIFFICULTY == "easy" else NORMAL_CONFIG

# ============================================================
# Vat ly nhan vat (lay tu do kho da chon)
# ============================================================
GRAVITY: float = _ACTIVE["gravity"]            # px/s^2 (keo xuong)
FLAP_FORCE: float = _ACTIVE["flap_force"]      # van toc Y duoc DAT khi vo (am = len)
MAX_FALL_SPEED: float = _ACTIVE["max_fall_speed"]  # gioi han van toc roi (px/s)

PLAYER_X = WINDOW_WIDTH * 0.28        # vi tri X co dinh cua nhan vat
PLAYER_START_Y = WINDOW_HEIGHT * 0.45  # vi tri Y khi bat dau / restart
# Kich thuoc HINH ANH chim (sprite)
PLAYER_WIDTH = 58
PLAYER_HEIGHT = 42
# Hitbox tron NHO hon sprite ~18% de game de tho hon
PLAYER_RADIUS = 17

# ============================================================
# Nhip do vao game
# ============================================================
START_DELAY_SECONDS: float = _ACTIVE["start_delay"]        # dem nguoc 3-2-1-GO
START_GRACE_PERIOD: float = _ACTIVE["start_grace_period"]  # giam trong luc sau GO
GO_TEXT_DURATION = 0.6                                     # chu "GO!" hien bao lau

# ============================================================
# Chuong ngai vat (cot)
# ============================================================
PIPE_SPEED: float = _ACTIVE["pipe_speed"]      # px/s, di chuyen sang trai
PIPE_WIDTH = 92
# Khoang cach ngang giua 2 cap cot = toc do * chu ky sinh
PIPE_SPACING: float = PIPE_SPEED * _ACTIVE["pipe_spawn_interval"]
PIPE_GAP_MIN: float = _ACTIVE["pipe_gap_min"]  # khoang trong doc nho nhat
PIPE_GAP_MAX: float = _ACTIVE["pipe_gap_max"]
PIPE_GAP_MARGIN = 70        # khoang trong khong duoc sat mep tren / mat dat
FIRST_OBSTACLE_DELAY: float = _ACTIVE["first_obstacle_delay"]
GROUND_HEIGHT = 84

# ============================================================
# Webcam / Vision
# ============================================================
CAMERA_INDEX = 0            # Doi neu may co nhieu webcam (0, 1, 2, ...)
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
VISION_MAX_FPS = 30         # Pose detection khong can chay bang FPS game
CAMERA_RETRY_INTERVAL = 2.0  # Giay giua 2 lan thu mo lai webcam khi loi
# 0 = lite (nhanh, khuyen nghi cho CPU), 1 = full, 2 = heavy.
# Voi mediapipe moi (Tasks API), file model .task tuong ung se duoc
# tu dong tai ve assets/models/ trong lan chay dau tien.
POSE_MODEL_COMPLEXITY = 0

# Khung webcam thu nho hien thi trong game (goc phai tren)
WEBCAM_PANEL_WIDTH = 264
WEBCAM_PANEL_HEIGHT = 198
WEBCAM_PANEL_MARGIN = 12

# ============================================================
# File du lieu
# ============================================================
HIGH_SCORE_FILE = "data/high_score.json"

# ============================================================
# Nhan dien vo canh (WingFlapDetector)
# ============================================================
FLAP_COOLDOWN_MS: int = _ACTIVE["flap_cooldown_ms"]


@dataclass
class FlapDetectorConfig:
    """Toan bo threshold cua thuat toan nhan dien vo canh.

    Moi khoang cach deu duoc CHUAN HOA theo chieu rong vai hien tai
    (don vi "sw" = shoulder width). Nho do thuat toan khong phu thuoc
    viec nguoi choi dung gan hay xa webcam.
    """

    # --- Lam muot (exponential smoothing) ---
    smoothing_alpha: float = 0.45   # EMA cho toa do (cang nho cang muot nhung tre)
    velocity_alpha: float = 0.5     # EMA cho van toc co tay

    # --- Nguong hinh hoc (nhan voi shoulder width) ---
    # Co tay cao hon vai it nhat chung nay -> "tay cao ro rang"
    up_margin_ratio: float = 0.35
    # Nguong "cao hon vai mot chut" cho tay con lai (khong bat buoc doi xung)
    weak_up_margin_ratio: float = 0.02
    # Duong nguong "tay thap" nam TREN vai chung nay (cho phep gan ngang vai)
    down_margin_ratio: float = 0.10

    # --- Nguong van toc (don vi: shoulder-width / giay) ---
    # Toc do HA tay toi thieu de xac nhan flap -> chong viec giu tay tren cao
    min_down_speed_ratio: float = 1.1
    # Toc do NANG tay de chap nhan tay con lai "dang di len"
    min_rise_speed_ratio: float = 0.6

    # --- Thoi gian ---
    # Cooldown lay theo do kho (easy: 220ms). Van dam bao moi chu ky tay
    # chi phat dung MOT flap nho state machine, khong phu thuoc cooldown.
    flap_cooldown: float = FLAP_COOLDOWN_MS / 1000.0
    max_dt: float = 0.2           # dt lon hon -> coi nhu gian doan, reset van toc

    # --- Do tin cay ---
    min_visibility: float = 0.5       # Visibility toi thieu cua 6 landmark
    stable_frames_required: int = 3   # So frame lien tiep thay nguoi truoc khi kich hoat
    min_shoulder_width: float = 0.04  # Vai qua nho (dung qua xa) -> khong tin cay


# ============================================================
# Calibration (hieu chinh truoc khi choi)
# ============================================================
CALIB_DETECT_SECONDS = 1.0   # Can thay nguoi on dinh chung nay giay
CALIB_LOW_SECONDS = 1.2      # Thoi gian giu tay thap
CALIB_HIGH_SECONDS = 1.2     # Thoi gian gio tay cao
CALIB_TIMEOUT = 30.0         # Qua lau -> that bai, dung threshold mac dinh

# Quy doi ket qua do dac thanh threshold:
# nguong "tay cao" = CALIB_UP_FRACTION * bien do nang tay da do duoc
CALIB_UP_FRACTION = 0.45
# nguong "tay thap" = CALIB_DOWN_FRACTION * bien do (tinh tu vai len)
CALIB_DOWN_FRACTION = 0.20

# ============================================================
# Hieu ung
# ============================================================
FLAP_TEXT_DURATION = 0.3      # Chu "FLAP!" hien 300ms
FLAP_PULSE_DURATION = 0.3     # Vong tron pulse quanh chim khi vo
WEBCAM_FLASH_DURATION = 0.35  # Vien webcam doi mau bao lau sau khi flap
DEBUG_FLAP_FLASH = 0.3        # "Flap detected: YES" giu it nhat 300ms
SHAKE_DURATION = 0.45         # Camera shake khi va cham
SHAKE_MAGNITUDE = 9           # Bien do rung (px)
MAX_PARTICLES = 300
SOUND_ENABLED = True
