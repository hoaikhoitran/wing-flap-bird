"""Sinh am thanh cho Wing Flap Bird bang NumPy (khong asset thuong mai).

Chay (deterministic):
    python scripts/generate_audio_assets.py

Output: assets/audio/*.wav (16-bit stereo 44.1kHz, MIT cung repo)
  flap_1..3 (pitch variation), score, collision, game_over,
  menu_move, menu_confirm, calibration_complete

Yeu cau: khong choi tai, fade in/out ngan chong click, bien do vua phai.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "assets" / "audio"


def _env(n: int, attack: float = 0.006, release: float = 0.05,
         dur: float = 1.0) -> np.ndarray:
    """Envelope attack/decay + fade-out chong click."""
    t = np.linspace(0.0, dur, n, endpoint=False)
    env = np.minimum(t / attack, 1.0) * np.exp(-3.2 * t / dur)
    fade = np.minimum((dur - t) / release, 1.0)
    return env * np.clip(fade, 0.0, 1.0)


def tone(f0: float, f1: float, dur: float, vol: float = 0.35,
         shape: str = "sine", vibrato: float = 0.0) -> np.ndarray:
    n = int(SR * dur)
    t = np.linspace(0.0, dur, n, endpoint=False)
    freq = np.linspace(f0, f1, n)
    if vibrato > 0:
        freq = freq * (1.0 + 0.01 * vibrato * np.sin(2 * np.pi * 6 * t))
    phase = 2 * np.pi * np.cumsum(freq) / SR
    if shape == "sine":
        sig = np.sin(phase)
    elif shape == "tri":
        sig = 2 / np.pi * np.arcsin(np.sin(phase))
    elif shape == "square":
        sig = np.sign(np.sin(phase)) * 0.5
    else:  # noise
        rng = np.random.default_rng(20260715)
        sig = rng.uniform(-1, 1, n)
    return sig * _env(n, dur=dur) * vol


def concat(*parts: np.ndarray) -> np.ndarray:
    return np.concatenate(parts)


def mix(*parts: np.ndarray) -> np.ndarray:
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return np.clip(out, -1.0, 1.0)


def save(name: str, sig: np.ndarray) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = (np.clip(sig, -1, 1) * 32767).astype(np.int16)
    stereo = np.ascontiguousarray(np.column_stack([data, data]))
    with wave.open(str(OUT / name), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(stereo.tobytes())
    print(f"  {OUT / name}")


def main() -> None:
    print("Audio:")
    # Flap: whoosh mem (noise thap + sweep) - 3 pitch variation
    for i, base in enumerate((300, 340, 385), start=1):
        whoosh = tone(0, 0, 0.13, 0.16, shape="noise")
        sweep = tone(base, base * 2.1, 0.13, 0.22, shape="tri")
        save(f"flap_{i}.wav", mix(whoosh, sweep))

    # Score: 2 not sang, vui
    save("score.wav", concat(tone(784, 784, 0.07, 0.26),
                             tone(1175, 1175, 0.12, 0.26)))

    # Collision: thud + noise ngan (khong choi tai)
    save("collision.wav", mix(tone(0, 0, 0.16, 0.30, shape="noise"),
                              tone(150, 82, 0.18, 0.34, shape="tri")))

    # Game over: 3 not di xuong cham
    save("game_over.wav", concat(tone(523, 523, 0.16, 0.24, vibrato=1),
                                 tone(392, 392, 0.16, 0.24, vibrato=1),
                                 tone(294, 280, 0.34, 0.24, vibrato=2)))

    # Menu: tick nhe + confirm 2 not
    save("menu_move.wav", tone(900, 860, 0.045, 0.14, shape="tri"))
    save("menu_confirm.wav", concat(tone(660, 660, 0.06, 0.2),
                                    tone(990, 990, 0.09, 0.2)))

    # Calibration complete: hop am rai len
    save("calibration_complete.wav",
         concat(tone(523, 523, 0.09, 0.22), tone(659, 659, 0.09, 0.22),
                tone(784, 784, 0.16, 0.24)))


if __name__ == "__main__":
    main()
