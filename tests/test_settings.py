"""Unit test cho core.settings.GameSettings."""
from __future__ import annotations

import json

from core.settings import GameSettings


def test_defaults_when_file_missing(tmp_path):
    settings = GameSettings.load(tmp_path / "khong_ton_tai.json")
    assert settings.camera_index == 0
    assert settings.difficulty == "easy"
    assert settings.debug_enabled is False  # PHAI tat mac dinh trong release
    assert settings.language == "vi"
    assert settings.sensitivity == 1.0


def test_corrupted_json_falls_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{khong phai json%%%", encoding="utf-8")
    settings = GameSettings.load(path)
    assert settings.difficulty == "easy"


def test_non_dict_json_falls_back(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("[1,2,3]", encoding="utf-8")
    settings = GameSettings.load(path)
    assert settings.camera_index == 0


def test_invalid_values_are_clamped(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({
        "camera_index": -5,          # khong nhan index am
        "difficulty": "nightmare",   # chi nhan easy/normal
        "sensitivity": 99.0,         # clamp 0.5..1.5
        "volume": 250,
        "language": "fr",            # chi vi/en
        "fullscreen": "yes",         # sai kieu -> mac dinh
    }), encoding="utf-8")
    settings = GameSettings.load(path)
    assert settings.camera_index == 0
    assert settings.difficulty == "easy"
    assert settings.sensitivity == 1.5
    assert settings.volume == 100
    assert settings.language == "vi"
    assert settings.fullscreen is False


def test_missing_fields_get_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"camera_index": 2}), encoding="utf-8")
    settings = GameSettings.load(path)
    assert settings.camera_index == 2
    assert settings.sound_enabled is True
    assert settings.webcam_preview_enabled is True


def test_save_and_reload_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    settings = GameSettings(camera_index=1, difficulty="normal",
                            sensitivity=1.25, language="en", volume=40)
    assert settings.save(path)
    loaded = GameSettings.load(path)
    assert loaded.camera_index == 1
    assert loaded.difficulty == "normal"
    assert loaded.sensitivity == 1.25
    assert loaded.language == "en"
    assert loaded.volume == 40


def test_reset_to_defaults_writes_file(tmp_path):
    path = tmp_path / "settings.json"
    GameSettings(camera_index=3).save(path)
    settings = GameSettings.reset_to_defaults(path)
    assert settings.camera_index == 0
    assert GameSettings.load(path).camera_index == 0
