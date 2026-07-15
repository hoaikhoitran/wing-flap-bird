"""Test Calibrator voi metrics gia lap."""
from __future__ import annotations

from vision.calibration import CalibPhase, Calibrator
from vision.flap_detector import PoseMetrics

DT = 1.0 / 30.0


def _metrics(wrist_y: float, shoulder_y: float = 0.45,
             sw: float = 0.3) -> PoseMetrics:
    return PoseMetrics(left_wrist_y=wrist_y, right_wrist_y=wrist_y,
                       left_shoulder_y=shoulder_y,
                       right_shoulder_y=shoulder_y,
                       shoulder_width=sw, visibility=0.9)


def test_full_calibration_flow():
    cal = Calibrator()
    for _ in range(40):
        cal.update(_metrics(0.75), DT)
    assert cal.phase is CalibPhase.HOLD_LOW
    for _ in range(45):
        cal.update(_metrics(0.75), DT)
    assert cal.phase is CalibPhase.RAISE_HIGH
    for _ in range(45):
        cal.update(_metrics(0.20), DT)
    assert cal.phase is CalibPhase.DONE
    assert cal.result is not None
    # Hysteresis: nguong "cao" phai lon hon nguong "thap"
    assert cal.result.up_margin_ratio > cal.result.down_margin_ratio


def test_calibration_timeout_fails():
    cal = Calibrator()
    for _ in range(31 * 30):
        cal.update(None, DT)
    assert cal.phase is CalibPhase.FAILED


def test_hint_too_close_and_too_far():
    cal = Calibrator()
    cal.update(_metrics(0.75, sw=0.7), DT)   # vai chiem 70% khung
    assert cal.hint_key == "calib.too_close"
    cal.update(_metrics(0.75, sw=0.05), DT)  # qua xa
    assert cal.hint_key == "calib.too_far"
    cal.update(_metrics(0.75, sw=0.3), DT)
    assert cal.hint_key is None
