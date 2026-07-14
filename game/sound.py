"""Am thanh: uu tien file WAV trong assets/, khong co thi tu tong hop
bang NumPy (khong can asset ban quyen).
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np
import pygame

import config

_SAMPLE_RATE = 44100
_ASSET_FILES = {
    "flap": "assets/flap.wav",
    "score": "assets/score.wav",
    "hit": "assets/hit.wav",
    "gameover": "assets/gameover.wav",
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
    """Tap hop hieu ung am thanh; tu vo hieu hoa neu mixer loi."""

    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self.enabled = False
        if not config.SOUND_ENABLED:
            return
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(_SAMPLE_RATE, -16, 2, 512)
            self._load()
            self.enabled = True
        except Exception:
            # Khong co thiet bi am thanh -> game van chay binh thuong
            self.enabled = False

    def _load(self) -> None:
        # Uu tien file trong assets/ neu nguoi dung tu them
        for name, path in _ASSET_FILES.items():
            if os.path.exists(path):
                try:
                    self._sounds[name] = pygame.mixer.Sound(path)
                    continue
                except Exception:
                    pass

        synth_map = {
            "flap": lambda: _synth(350, 720, 0.12, 0.35),
            "score": lambda: _concat(_synth(880, 880, 0.07, 0.3),
                                     _synth(1318, 1318, 0.11, 0.3)),
            "hit": lambda: _concat(_synth(0, 0, 0.18, 0.5, wave="noise"),
                                   _synth(160, 90, 0.18, 0.4, wave="square")),
            "gameover": lambda: _synth(440, 150, 0.6, 0.35),
            "calib_ok": lambda: _concat(_synth(660, 660, 0.09, 0.3),
                                        _synth(990, 990, 0.14, 0.3)),
        }
        for name, factory in synth_map.items():
            if name not in self._sounds:
                sound = factory()
                if sound is not None:
                    self._sounds[name] = sound

    def play(self, name: str) -> None:
        if not self.enabled:
            return
        sound = self._sounds.get(name)
        if sound is not None:
            try:
                sound.play()
            except Exception:
                pass
