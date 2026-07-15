"""
Hang so KY THUAT cua game Wing Flap Bird.

File nay chi giu cac constant ky thuat va gia tri mac dinh.
Setting nguoi dung (camera, do kho, am thanh, ngon ngu...) nam o
core/settings.py va duoc luu vao %LOCALAPPDATA%\\WingFlapBird.

QUY UOC DON VI (quan trong - khong tron 2 he):
  Toan bo vat ly dung he DELTA-TIME: px/s va px/s^2, moi frame nhan dt.
  Quy doi tu he per-frame @60fps:  gia_tri_per_frame * 60 (van toc)
                                   gia_tri_per_frame * 3600 (gia toc)
"""
from __future__ import annotations

from dataclasses import dataclass

# ============================================================
# DEBUG (mac dinh TAT trong release; bat qua Settings hoac --debug/F1)
# ============================================================
DEBUG_MODE = False

# ============================================================
# Cua so & vong lap game
# ============================================================
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
TARGET_FPS = 60

# ============================================================
# DO KHO - config object, doi duoc trong runtime
# ============================================================


@dataclass(frozen=True)
class DifficultyConfig:
    """Toan bo thong so gameplay phu thuoc do kho (he delta-time)."""
    name: str
    gravity: float               # px/s^2
    flap_force: float            # px/s (van toc duoc DAT khi vo, am = len)
    max_fall_speed: float        # px/s
    pipe_speed: float            # px/s
    pipe_gap_min: float
    pipe_gap_max: float
    spawn_interval: float        # giay giua 2 lan sinh cot
    first_obstacle_delay: float  # cot dau tien xuat hien sau bao nhieu giay
    start_delay: float           # dem nguoc GET_READY
    grace_period: float          # sau GO: trong luc giam mot nua
    flap_cooldown_ms: int

    @property
    def pipe_spacing(self) -> float:
        """Khoang cach ngang giua 2 cap cot lien tiep (px)."""
        return self.pipe_speed * self.spawn_interval

    @property
    def flap_cooldown(self) -> float:
        return self.flap_cooldown_ms / 1000.0


EASY = DifficultyConfig(
    name="easy",
    gravity=800.0,           # ~0.22 px/frame^2 - roi cham, de phan ung
    flap_force=-400.0,       # bay len ~100 px moi lan vo
    max_fall_speed=210.0,    # roi tu giua man hinh xuong dat ~1.6s
    pipe_speed=150.0,
    pipe_gap_min=210.0,
    pipe_gap_max=250.0,
    spawn_interval=2.2,
    first_obstacle_delay=3.0,
    start_delay=2.5,
    grace_period=1.0,
    flap_cooldown_ms=220,
)

NORMAL = DifficultyConfig(
    name="normal",
    gravity=1300.0,
    flap_force=-480.0,
    max_fall_speed=520.0,
    pipe_speed=230.0,
    pipe_gap_min=195.0,
    pipe_gap_max=245.0,
    spawn_interval=1.5,
    first_obstacle_delay=2.0,
    start_delay=2.0,
    grace_period=0.5,
    flap_cooldown_ms=300,
)

_DIFFICULTIES = {"easy": EASY, "normal": NORMAL}


def get_difficulty_config(name: str) -> DifficultyConfig:
    """Lay config theo ten; ten la -> easy (an toan cho file settings hong)."""
    return _DIFFICULTIES.get(name, EASY)


# ============================================================
# Nhan vat (khong phu thuoc do kho)
# ============================================================
PLAYER_X = WINDOW_WIDTH * 0.28
PLAYER_START_Y = WINDOW_HEIGHT * 0.45
PLAYER_WIDTH = 58      # kich thuoc sprite
PLAYER_HEIGHT = 42
PLAYER_RADIUS = 17     # hitbox tron NHO hon sprite ~18%

GO_TEXT_DURATION = 0.6

# ============================================================
# Chuong ngai vat (phan khong phu thuoc do kho)
# ============================================================
PIPE_WIDTH = 92
PIPE_GAP_MARGIN = 70   # khoang trong khong duoc sat mep tren / mat dat
GROUND_HEIGHT = 84

# ============================================================
# Webcam / Vision
# ============================================================
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
VISION_MAX_FPS = 30          # pose detection khong can chay bang FPS game
CAMERA_RETRY_INTERVAL = 2.0  # giay giua 2 lan thu mo lai webcam khi loi
CAMERA_SCAN_MAX_INDEX = 5    # quet camera index 0..5 trong Settings
# 0 = lite (nhanh, bundle san trong release), 1 = full, 2 = heavy
POSE_MODEL_COMPLEXITY = 0

# Khung webcam thu nho hien thi trong game (goc phai tren)
WEBCAM_PANEL_WIDTH = 264
WEBCAM_PANEL_HEIGHT = 198
WEBCAM_PANEL_MARGIN = 12

# ============================================================
# Nhan dien vo canh (WingFlapDetector)
# ============================================================


@dataclass
class FlapDetectorConfig:
    """Threshold cua thuat toan nhan dien vo canh.

    Moi khoang cach duoc CHUAN HOA theo chieu rong vai hien tai
    (don vi "sw" = shoulder width) -> khong phu thuoc dung gan hay xa.
    Cac gia tri nay la MAC DINH; calibration va sensitivity (Settings)
    se dieu chinh chung trong runtime mot cach co kiem soat.
    """

    # --- Lam muot (exponential smoothing) ---
    smoothing_alpha: float = 0.45
    velocity_alpha: float = 0.5

    # --- Nguong hinh hoc (nhan voi shoulder width) ---
    up_margin_ratio: float = 0.35
    weak_up_margin_ratio: float = 0.02
    down_margin_ratio: float = 0.10

    # --- Nguong van toc (shoulder-width / giay) ---
    min_down_speed_ratio: float = 1.1
    min_rise_speed_ratio: float = 0.6

    # --- Thoi gian ---
    flap_cooldown: float = 0.25   # se bi ghi de theo do kho khi vao game
    max_dt: float = 0.2

    # --- Do tin cay ---
    min_visibility: float = 0.5
    stable_frames_required: int = 3
    min_shoulder_width: float = 0.04
    # Chan doan khoang cach cho man calibration
    too_close_shoulder_width: float = 0.55  # vai chiem >55% khung -> qua gan
    too_far_shoulder_width: float = 0.07    # vai <7% khung -> qua xa

    def apply_sensitivity(self, sensitivity: float) -> None:
        """Anh xa co kiem soat tu slider sensitivity (0.5..1.5).

        sensitivity cao -> de kich hoat hon (nguong thap hon) nhung
        cac gia tri deu bi clamp de detector khong mat on dinh.
        Calibration van la co che chinh; day chi la tinh chinh bo sung.
        """
        s = max(0.5, min(1.5, float(sensitivity)))
        base = FlapDetectorConfig()
        self.up_margin_ratio = max(
            0.15, min(0.7, base.up_margin_ratio / s))
        self.down_margin_ratio = max(
            0.05, min(0.25, base.down_margin_ratio * (2.0 - s)))
        self.min_down_speed_ratio = max(
            0.6, min(1.8, base.min_down_speed_ratio / s))
        self.stable_frames_required = 2 if s >= 1.25 else (
            4 if s <= 0.75 else 3)


# ============================================================
# Calibration
# ============================================================
CALIB_DETECT_SECONDS = 1.0
CALIB_LOW_SECONDS = 1.2
CALIB_HIGH_SECONDS = 1.2
CALIB_TIMEOUT = 30.0
CALIB_UP_FRACTION = 0.45
CALIB_DOWN_FRACTION = 0.20

# ============================================================
# Hieu ung
# ============================================================
FLAP_TEXT_DURATION = 0.3
FLAP_PULSE_DURATION = 0.3
WEBCAM_FLASH_DURATION = 0.35
DEBUG_FLAP_FLASH = 0.3
SHAKE_DURATION = 0.45
SHAKE_MAGNITUDE = 9
MAX_PARTICLES = 300
SOUND_ENABLED = True
