"""Sinh asset am thanh placeholder (WAV 16-bit stereo) vao thu muc assets/.

Khong dung asset ban quyen - moi am thanh deu duoc tong hop bang NumPy.
Chay mot lan:  python tools/generate_assets.py
Game se tu uu tien dung cac file nay (xem game/sound.py).
"""
from __future__ import annotations

import os
import wave

import numpy as np

SAMPLE_RATE = 44100
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "assets")


def synth(f0: float, f1: float, duration: float, volume: float = 0.4,
          shape: str = "sine") -> np.ndarray:
    """Quet tan so f0 -> f1 voi envelope attack/decay, tra ve int16 mono."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0.0, duration, n, endpoint=False)
    freq = np.linspace(f0, f1, n)
    phase = 2.0 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    if shape == "sine":
        sig = np.sin(phase)
    elif shape == "square":
        sig = np.sign(np.sin(phase)) * 0.6
    else:  # noise
        sig = np.random.uniform(-1.0, 1.0, n)
    env = np.minimum(t / 0.005, 1.0) * np.exp(-4.0 * t / duration)
    return (sig * env * volume * 32767).astype(np.int16)


def save_wav(name: str, *parts: np.ndarray) -> None:
    mono = np.concatenate(parts)
    stereo = np.column_stack([mono, mono])
    path = os.path.join(OUT_DIR, name)
    with wave.open(path, "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)  # int16
        f.setframerate(SAMPLE_RATE)
        f.writeframes(stereo.tobytes())
    print(f"  da tao {path}")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    print("Dang sinh asset am thanh...")
    save_wav("flap.wav", synth(350, 720, 0.12, 0.35))
    save_wav("score.wav", synth(880, 880, 0.07, 0.3),
             synth(1318, 1318, 0.11, 0.3))
    save_wav("hit.wav", synth(0, 0, 0.18, 0.5, shape="noise"),
             synth(160, 90, 0.18, 0.4, shape="square"))
    save_wav("gameover.wav", synth(440, 150, 0.6, 0.35))
    print("Xong.")


if __name__ == "__main__":
    main()
