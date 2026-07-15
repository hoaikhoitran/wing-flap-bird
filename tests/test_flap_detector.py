"""Test WingFlapDetector voi landmark tong hop (khong can webcam)."""
from __future__ import annotations

import math

from config import FlapDetectorConfig
from vision.flap_detector import DetectorState, WingFlapDetector
from vision.pose_tracker import LandmarkPoint, UpperBodySample

DT = 1.0 / 30.0


def _sample(wrist_y: float, shoulder_y: float = 0.45,
            vis: float = 0.95) -> UpperBodySample:
    def p(x, y):
        return LandmarkPoint(x=x, y=y, visibility=vis)
    return UpperBodySample(
        left_shoulder=p(0.65, shoulder_y), right_shoulder=p(0.35, shoulder_y),
        left_elbow=p(0.72, (shoulder_y + wrist_y) / 2),
        right_elbow=p(0.28, (shoulder_y + wrist_y) / 2),
        left_wrist=p(0.75, wrist_y), right_wrist=p(0.25, wrist_y),
    )


def _run_cycle(det: WingFlapDetector, t0: float,
               up_time: float = 0.25, down_time: float = 0.15):
    """Gia lap 1 chu ky vo canh day du. Tra ve (so flap, thoi diem cuoi)."""
    flaps, t = 0, t0
    low, high = 0.75, 0.25
    for _ in range(9):
        flaps += det.update(_sample(low), t); t += DT
    steps = max(1, int(up_time / DT))
    for i in range(steps):
        y = low + (high - low) * (i + 1) / steps
        flaps += det.update(_sample(y), t); t += DT
    for _ in range(2):
        flaps += det.update(_sample(high), t); t += DT
    steps = max(1, int(down_time / DT))
    for i in range(steps):
        y = high + (low - high) * (i + 1) / steps
        flaps += det.update(_sample(y), t); t += DT
    for _ in range(6):
        flaps += det.update(_sample(low), t); t += DT
    return flaps, t


def test_full_cycle_gives_exactly_one_flap():
    det = WingFlapDetector(FlapDetectorConfig())
    flaps, t = _run_cycle(det, 0.0)
    assert flaps == 1
    assert det.state is DetectorState.ARMS_DOWN
    flaps2, _ = _run_cycle(det, t + 0.5)
    assert flaps2 == 1
    assert det.flap_count == 2


def test_slow_lowering_does_not_flap():
    det = WingFlapDetector(FlapDetectorConfig())
    flaps, _ = _run_cycle(det, 0.0, down_time=2.5)
    assert flaps == 0


def test_holding_arms_up_does_not_flap():
    det = WingFlapDetector(FlapDetectorConfig())
    t = 0.0
    for _ in range(10):
        det.update(_sample(0.75), t); t += DT
    for i in range(8):
        det.update(_sample(0.75 - 0.5 * (i + 1) / 8), t); t += DT
    held = sum(det.update(_sample(0.25), t + i * DT) for i in range(90))
    assert held == 0
    assert det.state is DetectorState.ARMS_UP


def test_single_hand_waving_does_not_flap():
    det = WingFlapDetector(FlapDetectorConfig())

    def p(x, y):
        return LandmarkPoint(x=x, y=y, visibility=0.95)

    flaps = 0
    for i in range(120):
        wob = 0.75 - 0.55 * abs(math.sin(i * 0.35))
        sample = UpperBodySample(
            left_shoulder=p(0.65, 0.45), right_shoulder=p(0.35, 0.45),
            left_elbow=p(0.72, 0.6), right_elbow=p(0.28, 0.6),
            left_wrist=p(0.75, wob), right_wrist=p(0.25, 0.75),
        )
        flaps += det.update(sample, i * DT)
    assert flaps == 0


def test_lost_pose_resets_to_no_pose():
    det = WingFlapDetector(FlapDetectorConfig())
    _run_cycle(det, 0.0)
    assert det.update(None, 100.0) is False
    assert det.state is DetectorState.NO_POSE


def test_low_visibility_treated_as_no_pose():
    det = WingFlapDetector(FlapDetectorConfig())
    det.update(_sample(0.75, vis=0.2), 0.0)
    assert det.state is DetectorState.NO_POSE


def test_sensitivity_mapping_is_clamped():
    cfg = FlapDetectorConfig()
    cfg.apply_sensitivity(99.0)   # ngoai range -> clamp ve 1.5
    assert 0.15 <= cfg.up_margin_ratio <= 0.7
    assert 0.6 <= cfg.min_down_speed_ratio <= 1.8
    cfg.apply_sensitivity(0.01)
    assert cfg.up_margin_ratio <= 0.7
    assert cfg.stable_frames_required in (2, 3, 4)
