"""Am thanh: uu tien file WAV trong assets/, khong co thi tu tong hop
bang NumPy (khong can asset ban quyen).
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pygame

import config
from core.paths import resource_path

_SAMPLE_RATE = 44100
# Am thanh sinh boi scripts/generate_audio_assets.py (MIT, khong asset
# thuong mai). Ten logic -> file; "flap" chon ngau nhien 1/3 pitch.
_ASSET_FILES = {
    "flap_1": "assets/audio/flap_1.wav",
    "flap_2": "assets/audio/flap_2.wav",
    "flap_3": "assets/audio/flap_3.wav",
    "score": "assets/audio/score.wav",
    "hit": "assets/audio/collision.wav",
    "gameover": "assets/audio/game_over.wav",
    "menu_move": "assets/audio/menu_move.wav",
    "menu_confirm": "assets/audio/menu_confirm.wav",
    "calib_ok": "assets/audio/calibration_complete.wav",
}


def _synth(f0: float, f1: float, duration: float, volume: float = 0.4,
           wave: str = "sine") -> Optional[pygame.mixer.Sound]:
    """Tong hop mot am don: quet tan so f0 -> f1 voi envelope decay."""
    try:
        n = int(_SAMPLE_RATE * duration)
        t = np.linspace(0.0, duration, n, endpoint=False)
        freq = np.linspace(f0, f1, n)
        phase = 2.0 * np.pi * np.cumsum(freq) / _SAMPLE_RATE
        if wave == "sine":
            sig = np.sin(phase)
        elif wave == "square":
            sig = np.sign(np.sin(phase)) * 0.6
        else:  # noise
            sig = np.random.uniform(-1.0, 1.0, n)
        # Attack 5ms + decay mu de khong bi "click"
        env = np.minimum(t / 0.005, 1.0) * np.exp(-4.0 * t / duration)
        samples = (sig * env * volume * 32767).astype(np.int16)
        stereo = np.ascontiguousarray(np.column_stack([samples, samples]))
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return None


def _concat(*sounds: Optional[pygame.mixer.Sound]
            ) -> Optional[pygame.mixer.Sound]:
    """Ghep nhieu am thanh lien tiep thanh mot."""
    try:
        arrays = [pygame.sndarray.array(s) for s in sounds if s is not None]
        if not arrays:
            return None
        return pygame.sndarray.make_sound(
            np.ascontiguousarray(np.concatenate(arrays)))
    except Exception:
        return None


class SoundBank:
    """Tap hop hieu ung am thanh; tu vo hieu hoa neu mixer loi.

    enabled va volume dieu khien duoc trong runtime tu Settings.
    """

    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self.enabled = False
        self._available = False
        self._volume = 1.0
        if not config.SOUND_ENABLED:
            return
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(_SAMPLE_RATE, -16, 2, 512)
            self._load()
            self._available = True
            self.enabled = True
        except Exception:
            # Khong co thiet bi am thanh -> game van chay binh thuong
            self._available = False
            self.enabled = False

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled) and self._available

    def set_volume(self, volume_percent: int) -> None:
        """Am luong 0..100 ap dung cho moi hieu ung."""
        self._volume = max(0, min(100, int(volume_percent))) / 100.0
        for sound in self._sounds.values():
            try:
                sound.set_volume(self._volume)
            except Exception:
                pass

    def _load(self) -> None:
        # Uu tien file WAV dong goi trong assets/ (resource_path de chay
        # duoc ca tu source lan tu PyInstaller bundle)
        for name, rel in _ASSET_FILES.items():
            path = resource_path(rel)
            if path.exists():
                try:
                    self._sounds[name] = pygame.mixer.Sound(str(path))
                    continue
                except Exception:
                    pass

        # Development fallback khi chua chay generate_audio_assets.py
        synth_map = {
            "flap_1": lambda: _synth(350, 720, 0.12, 0.3),
            "flap_2": lambda: _synth(390, 800, 0.12, 0.3),
            "flap_3": lambda: _synth(430, 880, 0.12, 0.3),
            "score": lambda: _concat(_synth(880, 880, 0.07, 0.28),
                                     _synth(1318, 1318, 0.11, 0.28)),
            "hit": lambda: _concat(_synth(0, 0, 0.18, 0.4, wave="noise"),
                                   _synth(160, 90, 0.18, 0.3, wave="square")),
            "gameover": lambda: _synth(440, 150, 0.6, 0.3),
            "calib_ok": lambda: _concat(_synth(660, 660, 0.09, 0.28),
                                        _synth(990, 990, 0.14, 0.28)),
        }
        for name, factory in synth_map.items():
            if name not in self._sounds:
                sound = factory()
                if sound is not None:
                    self._sounds[name] = sound

    _FLAP_VARIANTS = ("flap_1", "flap_2", "flap_3")

    def play(self, name: str) -> None:
        """Phat am thanh theo ten logic. Khong phat khi sound tat."""
        if not self.enabled:
            return
        if name == "flap":
            import random
            name = random.choice(self._FLAP_VARIANTS)
        sound = self._sounds.get(name)
        if sound is not None:
            try:
                sound.play()
            except Exception:
                pass
