"""Hieu chinh nguong nhan dien theo tung nguoi choi.

Quy trinh 3 pha:
  1. DETECT_BODY : dung giua khung hinh cho den khi thay nguoi on dinh.
  2. HOLD_LOW    : giu hai tay thap ~1 giay -> do vi tri tay thap.
  3. RAISE_HIGH  : gio hai tay cao ~1 giay -> do bien do nang tay.

Tu bien do do duoc, tinh threshold TUONG DOI (theo chieu rong vai),
khong dung toa do pixel co dinh. Neu qua timeout -> FAILED va game
dung bo threshold mac dinh trong config.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import config
from vision.flap_detector import PoseMetrics


class CalibPhase(Enum):
    DETECT_BODY = "DETECT_BODY"
    HOLD_LOW = "HOLD_LOW"
    RAISE_HIGH = "RAISE_HIGH"
    DONE = "DONE"
    FAILED = "FAILED"


# Key i18n (dich o tang UI, vision khong phu thuoc game.i18n)
_PHASE_KEYS = {
    CalibPhase.DETECT_BODY: "calib.detect",
    CalibPhase.HOLD_LOW: "calib.hold_low",
    CalibPhase.RAISE_HIGH: "calib.raise_high",
    CalibPhase.DONE: "calib.done",
    CalibPhase.FAILED: "calib.failed",
}


@dataclass(frozen=True)
class CalibrationResult:
    """Threshold da hieu chinh (don vi: ti le so voi chieu rong vai)."""
    up_margin_ratio: float
    down_margin_ratio: float
    measured_raise_range: float  # bien do nang tay do duoc (don vi sw)


class Calibrator:
    """Cap nhat moi frame bang metrics tu vision thread.

    Su dung:
        calib.update(snapshot.metrics, dt)
        if calib.phase is CalibPhase.DONE: apply calib.result
    """

    def __init__(self) -> None:
        self.phase = CalibPhase.DETECT_BODY
        self.result: Optional[CalibrationResult] = None
        self._phase_timer = 0.0
        self._total_time = 0.0
        self._last_metrics: Optional[PoseMetrics] = None
        # Mau thu thap trong tung pha: (wrist_y_avg, shoulder_y_avg, sw)
        self._low_samples: list[tuple[float, float, float]] = []
        self._high_samples: list[tuple[float, float, float]] = []

    # ------------------------------------------------------------------
    def update(self, metrics: Optional[PoseMetrics], dt: float) -> None:
        self._last_metrics = metrics
        if self.phase in (CalibPhase.DONE, CalibPhase.FAILED):
            return

        self._total_time += dt
        if self._total_time > config.CALIB_TIMEOUT:
            self.phase = CalibPhase.FAILED
            return

        if self.phase is CalibPhase.DETECT_BODY:
            if metrics is not None:
                self._phase_timer += dt
            else:
                # Mat dau -> tut lai nhung khong reset han ve 0
                self._phase_timer = max(0.0, self._phase_timer - 2.0 * dt)
            if self._phase_timer >= config.CALIB_DETECT_SECONDS:
                self._next_phase(CalibPhase.HOLD_LOW)

        elif self.phase is CalibPhase.HOLD_LOW:
            # "Tay thap": ca hai co tay ro rang duoi vai (>= 0.15 sw)
            if metrics is not None and self._wrists_below(metrics, 0.15):
                self._phase_timer += dt
                self._low_samples.append(self._sample_of(metrics))
            else:
                self._phase_timer = max(0.0, self._phase_timer - dt)
            if self._phase_timer >= config.CALIB_LOW_SECONDS:
                self._next_phase(CalibPhase.RAISE_HIGH)

        elif self.phase is CalibPhase.RAISE_HIGH:
            # "Tay cao": ca hai co tay tren vai (>= 0.05 sw)
            if metrics is not None and self._wrists_above(metrics, 0.05):
                self._phase_timer += dt
                self._high_samples.append(self._sample_of(metrics))
            else:
                self._phase_timer = max(0.0, self._phase_timer - dt)
            if self._phase_timer >= config.CALIB_HIGH_SECONDS:
                self._finish()

    # ------------------------------------------------------------------
    @property
    def message_key(self) -> str:
        """Key i18n cua huong dan pha hien tai (UI tu dich)."""
        return _PHASE_KEYS[self.phase]

    @property
    def hint_key(self) -> Optional[str]:
        """Chan doan truc tiep: qua gan / qua xa / thieu anh sang.

        Tra ve key i18n hoac None neu moi thu on.
        """
        m = self._last_metrics
        if m is None:
            # Chua/khong thay nguoi: chi goi y sau khi da qua pha detect
            if self.phase in (CalibPhase.HOLD_LOW, CalibPhase.RAISE_HIGH):
                return "calib.low_visibility"
            return None
        cfg = config.FlapDetectorConfig()
        if m.shoulder_width > cfg.too_close_shoulder_width:
            return "calib.too_close"
        if m.shoulder_width < cfg.too_far_shoulder_width:
            return "calib.too_far"
        if m.visibility < 0.6:
            return "calib.low_visibility"
        return None

    @property
    def progress(self) -> float:
        """Tien do 0..1 cua pha hien tai (cho progress bar)."""
        targets = {
            CalibPhase.DETECT_BODY: config.CALIB_DETECT_SECONDS,
            CalibPhase.HOLD_LOW: config.CALIB_LOW_SECONDS,
            CalibPhase.RAISE_HIGH: config.CALIB_HIGH_SECONDS,
        }
        target = targets.get(self.phase)
        if target is None:
            return 1.0
        return min(1.0, self._phase_timer / target)

    @property
    def finished(self) -> bool:
        return self.phase in (CalibPhase.DONE, CalibPhase.FAILED)

    # ------------------------------------------------------------------
    @staticmethod
    def _sample_of(m: PoseMetrics) -> tuple[float, float, float]:
        return (m.wrist_y_avg, m.shoulder_y_avg, m.shoulder_width)

    @staticmethod
    def _wrists_below(m: PoseMetrics, margin_ratio: float) -> bool:
        margin = margin_ratio * m.shoulder_width
        return (m.left_wrist_y > m.left_shoulder_y + margin
                and m.right_wrist_y > m.right_shoulder_y + margin)

    @staticmethod
    def _wrists_above(m: PoseMetrics, margin_ratio: float) -> bool:
        margin = margin_ratio * m.shoulder_width
        return (m.left_wrist_y < m.left_shoulder_y - margin
                and m.right_wrist_y < m.right_shoulder_y - margin)

    def _next_phase(self, phase: CalibPhase) -> None:
        self.phase = phase
        self._phase_timer = 0.0

    def _finish(self) -> None:
        """Tinh threshold tuong doi tu cac mau da thu thap."""
        if not self._low_samples or not self._high_samples:
            self.phase = CalibPhase.FAILED
            return

        def mean(values: list[float]) -> float:
            return sum(values) / len(values)

        high_wrist_y = mean([s[0] for s in self._high_samples])
        high_shoulder_y = mean([s[1] for s in self._high_samples])
        sw = mean([s[2] for s in self._low_samples + self._high_samples])
        if sw <= 1e-6:
            self.phase = CalibPhase.FAILED
            return

        # Bien do nang tay: co tay cao hon vai bao nhieu (don vi sw).
        # Y tang xuong duoi nen (shoulder_y - wrist_y) > 0 khi tay o tren vai.
        raise_range = (high_shoulder_y - high_wrist_y) / sw
        if raise_range < 0.15:
            # Nguoi choi gan nhu khong nang tay qua vai -> du lieu vo dung
            self.phase = CalibPhase.FAILED
            return

        # Nguong "tay cao" = mot phan bien do da do (de moi nguoi deu voi toi)
        up_margin = config.CALIB_UP_FRACTION * raise_range
        up_margin = max(0.15, min(0.9, up_margin))
        # Nguong "tay thap" dat gan vai hon nguong "tay cao" (hysteresis)
        down_margin = config.CALIB_DOWN_FRACTION * raise_range
        down_margin = max(0.03, min(down_margin, up_margin - 0.08, 0.30))

        self.result = CalibrationResult(
            up_margin_ratio=up_margin,
            down_margin_ratio=down_margin,
            measured_raise_range=raise_range,
        )
        self.phase = CalibPhase.DONE
