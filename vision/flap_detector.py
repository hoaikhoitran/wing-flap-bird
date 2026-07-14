"""WingFlapDetector - state machine nhan dien chu ky vo canh.

Chu ky hop le:  ARMS_DOWN -> ARMS_UP -> (ha tay du nhanh) -> FLAP_CONFIRMED
Moi chu ky chi phat dung MOT su kien flap. Co cooldown, lam muot EMA,
nguong van toc va kiem tra do tin cay de chong rung / chong giu tay tren cao.

Moi khoang cach & van toc deu duoc chuan hoa theo chieu rong vai (sw),
nen khong phu thuoc nguoi choi dung gan hay xa webcam.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from config import FlapDetectorConfig
from vision.pose_tracker import UpperBodySample


class DetectorState(Enum):
    NO_POSE = "NO_POSE"
    ARMS_DOWN = "ARMS_DOWN"
    ARMS_UP = "ARMS_UP"
    FLAP_CONFIRMED = "FLAP_CONFIRMED"


@dataclass(frozen=True)
class PoseMetrics:
    """Cac gia tri DA LAM MUOT, dung cho calibration va debug overlay."""
    left_wrist_y: float
    right_wrist_y: float
    left_shoulder_y: float
    right_shoulder_y: float
    shoulder_width: float
    visibility: float

    @property
    def wrist_y_avg(self) -> float:
        return (self.left_wrist_y + self.right_wrist_y) / 2.0

    @property
    def shoulder_y_avg(self) -> float:
        return (self.left_shoulder_y + self.right_shoulder_y) / 2.0


class WingFlapDetector:
    """Nhan dien chu ky vo canh tu landmark MediaPipe Pose.

    Cach dung (moi frame cua vision thread):
        flapped = detector.update(sample, timestamp)
        # flapped == True dung MOT frame khi hoan tat chu ky vo canh
    """

    def __init__(self, config: Optional[FlapDetectorConfig] = None) -> None:
        self.config = config or FlapDetectorConfig()
        self.flap_count = 0
        self._state = DetectorState.NO_POSE
        self._last_ts: Optional[float] = None
        self._last_flap_ts = -math.inf
        self._stable_frames = 0
        # Toa do Y da lam muot: lw / rw / ls / rs, va chieu rong vai "sw"
        self._smooth: dict[str, float] = {}
        # Van toc Y da lam muot cua 2 co tay (don vi: toa-do-chuan-hoa / giay)
        self._vel: dict[str, float] = {"lw": 0.0, "rw": 0.0}
        self._visibility = 0.0

    # ------------------------------------------------------------------
    # API chinh
    # ------------------------------------------------------------------
    def update(self, sample: Optional[UpperBodySample],
               timestamp: float) -> bool:
        """Cap nhat detector voi frame moi.

        Tra ve True dung MOT frame khi phat hien chu ky vo canh hoan chinh.
        """
        cfg = self.config

        # FLAP_CONFIRMED chi ton tai dung 1 frame roi tro ve ARMS_DOWN
        if self._state is DetectorState.FLAP_CONFIRMED:
            self._state = DetectorState.ARMS_DOWN

        # --- 1. Kiem tra do tin cay: mat dau -> ve NO_POSE, khong flap ---
        if sample is None or sample.min_visibility < cfg.min_visibility \
                or sample.shoulder_width < cfg.min_shoulder_width:
            self._on_pose_lost(timestamp)
            return False

        self._visibility = sample.min_visibility

        # --- 2. Tinh dt; gian doan qua lau thi reset smoothing/van toc ---
        if self._last_ts is None:
            dt = 0.0
        else:
            dt = timestamp - self._last_ts
        self._last_ts = timestamp

        raw = {
            "lw": sample.left_wrist.y,
            "rw": sample.right_wrist.y,
            "ls": sample.left_shoulder.y,
            "rs": sample.right_shoulder.y,
            "sw": sample.shoulder_width,
        }

        if not self._smooth or dt <= 0.0 or dt > cfg.max_dt:
            # Frame dau tien sau gian doan: khoi tao lai, van toc = 0
            self._smooth = dict(raw)
            self._vel = {"lw": 0.0, "rw": 0.0}
            self._stable_frames = 1
            if self._state is not DetectorState.NO_POSE:
                self._state = DetectorState.NO_POSE
            return False

        self._stable_frames += 1

        # --- 3. Lam muot toa do (EMA) va tinh van toc co tay ---
        a = cfg.smoothing_alpha
        prev_lw, prev_rw = self._smooth["lw"], self._smooth["rw"]
        for key, value in raw.items():
            self._smooth[key] = self._smooth[key] + a * (value - self._smooth[key])

        va = cfg.velocity_alpha
        inst_vlw = (self._smooth["lw"] - prev_lw) / dt
        inst_vrw = (self._smooth["rw"] - prev_rw) / dt
        self._vel["lw"] += va * (inst_vlw - self._vel["lw"])
        self._vel["rw"] += va * (inst_vrw - self._vel["rw"])

        # --- 4. Danh gia dieu kien hinh hoc (chuan hoa theo vai) ---
        sw = max(self._smooth["sw"], cfg.min_shoulder_width)
        lw_y, rw_y = self._smooth["lw"], self._smooth["rw"]
        ls_y, rs_y = self._smooth["ls"], self._smooth["rs"]

        # Y tang xuong duoi => "cao hon vai" nghia la wrist_y < shoulder_y
        l_up_strong = lw_y < ls_y - cfg.up_margin_ratio * sw
        r_up_strong = rw_y < rs_y - cfg.up_margin_ratio * sw
        l_up_weak = lw_y < ls_y - cfg.weak_up_margin_ratio * sw
        r_up_weak = rw_y < rs_y - cfg.weak_up_margin_ratio * sw
        # Van toc am = tay dang di LEN
        l_rising = self._vel["lw"] < -cfg.min_rise_speed_ratio * sw
        r_rising = self._vel["rw"] < -cfg.min_rise_speed_ratio * sw

        # Hai tay khong bat buoc doi xung: 1 tay cao ro rang + tay kia
        # dang o tren vai VA dang di len cung duoc chap nhan.
        arms_up = (
            (l_up_strong and r_up_strong)
            or (l_up_strong and r_up_weak and r_rising)
            or (r_up_strong and l_up_weak and l_rising)
        )
        # "Tay thap": ca 2 co tay thap hon duong nguong nam ngay tren vai
        arms_down = (
            lw_y > ls_y - cfg.down_margin_ratio * sw
            and rw_y > rs_y - cfg.down_margin_ratio * sw
        )

        # --- 5. State machine ---
        flapped = False
        if self._state is DetectorState.NO_POSE:
            # Can vai frame on dinh truoc khi kich hoat (chong nhiễu re-detect)
            if self._stable_frames >= cfg.stable_frames_required:
                self._state = (DetectorState.ARMS_UP if arms_up
                               else DetectorState.ARMS_DOWN)

        elif self._state is DetectorState.ARMS_DOWN:
            if arms_up:
                self._state = DetectorState.ARMS_UP

        elif self._state is DetectorState.ARMS_UP:
            if arms_down:
                # Van toc duong = tay dang di XUONG. Yeu cau CA HAI tay
                # di xuong va toc do trung binh vuot nguong -> chong viec
                # giu tay tren cao roi ha cham / chong rung 1 tay.
                avg_down_speed = (self._vel["lw"] + self._vel["rw"]) / 2.0
                fast_enough = (
                    avg_down_speed > cfg.min_down_speed_ratio * sw
                    and self._vel["lw"] > 0.0
                    and self._vel["rw"] > 0.0
                )
                cooled = (timestamp - self._last_flap_ts) >= cfg.flap_cooldown
                if fast_enough and cooled:
                    self._state = DetectorState.FLAP_CONFIRMED
                    self._last_flap_ts = timestamp
                    self.flap_count += 1
                    flapped = True
                else:
                    # Ha tay qua cham hoac dang cooldown -> khong tinh flap
                    self._state = DetectorState.ARMS_DOWN

        return flapped

    # ------------------------------------------------------------------
    # Truy van trang thai
    # ------------------------------------------------------------------
    @property
    def state(self) -> DetectorState:
        return self._state

    def cooldown_remaining(self, timestamp: float) -> float:
        remain = self.config.flap_cooldown - (timestamp - self._last_flap_ts)
        return max(0.0, remain)

    @property
    def metrics(self) -> Optional[PoseMetrics]:
        """Gia tri da lam muot cua frame gan nhat (None neu mat dau)."""
        if self._state is DetectorState.NO_POSE or not self._smooth:
            return None
        return PoseMetrics(
            left_wrist_y=self._smooth["lw"],
            right_wrist_y=self._smooth["rw"],
            left_shoulder_y=self._smooth["ls"],
            right_shoulder_y=self._smooth["rs"],
            shoulder_width=self._smooth["sw"],
            visibility=self._visibility,
        )

    def debug_info(self, timestamp: float) -> dict[str, str]:
        """Thong tin hien thi tren overlay debug."""
        sw = self._smooth.get("sw", 0.0)
        return {
            "state": self._state.value,
            "lw_y": f"{self._smooth.get('lw', 0.0):.3f}",
            "rw_y": f"{self._smooth.get('rw', 0.0):.3f}",
            "ls_y": f"{self._smooth.get('ls', 0.0):.3f}",
            "rs_y": f"{self._smooth.get('rs', 0.0):.3f}",
            "vel_lw": f"{self._vel.get('lw', 0.0):+.2f}",
            "vel_rw": f"{self._vel.get('rw', 0.0):+.2f}",
            "shoulder_w": f"{sw:.3f}",
            "visibility": f"{self._visibility:.2f}",
            "cooldown": f"{self.cooldown_remaining(timestamp):.2f}s",
            "flaps": str(self.flap_count),
            "up_margin": f"{self.config.up_margin_ratio:.2f}sw",
            "down_speed_min": f"{self.config.min_down_speed_ratio:.2f}sw/s",
        }

    def apply_thresholds(self, up_margin_ratio: float,
                         down_margin_ratio: float) -> None:
        """Nhan threshold moi tu buoc calibration."""
        self.config.up_margin_ratio = up_margin_ratio
        self.config.down_margin_ratio = down_margin_ratio

    # ------------------------------------------------------------------
    def _on_pose_lost(self, timestamp: float) -> None:
        """MediaPipe mat dau co the: reset ve NO_POSE, khong phat flap."""
        self._state = DetectorState.NO_POSE
        self._stable_frames = 0
        self._smooth = {}
        self._vel = {"lw": 0.0, "rw": 0.0}
        self._visibility = 0.0
        self._last_ts = timestamp
