"""Test core.storage: high score + calibration persistence."""
from __future__ import annotations

from core import storage
from core.storage import StoredCalibration


def test_high_score_missing_file_returns_zero(isolated_user_data):
    assert storage.load_high_score() == 0


def test_high_score_corrupt_file_returns_zero(isolated_user_data):
    (isolated_user_data / "high_score.json").write_text("###hong",
                                                        encoding="utf-8")
    assert storage.load_high_score() == 0


def test_high_score_roundtrip(isolated_user_data):
    assert storage.save_high_score(42)
    assert storage.load_high_score() == 42
    storage.reset_high_score()
    assert storage.load_high_score() == 0


def test_high_score_migrates_from_legacy(isolated_user_data):
    legacy = isolated_user_data / "legacy" / "high_score.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"high_score": 7}', encoding="utf-8")
    assert storage.load_high_score() == 7
    # Sau migrate, gia tri nam o vi tri moi
    assert (isolated_user_data / "high_score.json").exists()


def test_calibration_roundtrip(isolated_user_data):
    calib = StoredCalibration(camera_index=1, up_margin_ratio=0.4,
                              down_margin_ratio=0.12,
                              measured_raise_range=0.9)
    assert storage.save_calibration(calib)
    loaded = storage.load_calibration(1)
    assert loaded is not None
    assert loaded.up_margin_ratio == 0.4


def test_calibration_wrong_camera_returns_none(isolated_user_data):
    storage.save_calibration(StoredCalibration(
        camera_index=0, up_margin_ratio=0.4, down_margin_ratio=0.12,
        measured_raise_range=0.9))
    # Doi camera -> phai de nghi calibration lai
    assert storage.load_calibration(2) is None


def test_calibration_corrupt_or_invalid_returns_none(isolated_user_data):
    path = isolated_user_data / "calibration.json"
    path.write_text("khong-json", encoding="utf-8")
    assert storage.load_calibration(0) is None
    # Gia tri ngoai range hop ly (file bi sua tay) -> tu choi
    storage.save_calibration(StoredCalibration(
        camera_index=0, up_margin_ratio=99.0, down_margin_ratio=0.1,
        measured_raise_range=1.0))
    assert storage.load_calibration(0) is None


def test_clear_calibration(isolated_user_data):
    storage.save_calibration(StoredCalibration(
        camera_index=0, up_margin_ratio=0.4, down_margin_ratio=0.1,
        measured_raise_range=0.8))
    storage.clear_calibration()
    assert storage.load_calibration(0) is None
