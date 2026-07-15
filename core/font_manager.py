"""Quan ly font Be Vietnam Pro (bundle, SIL OFL 1.1) theo ROLE.

Quy tac:
  - KHONG dung font he thong (Sys-Font) hay font mac dinh (Font-None)
    o runtime - chi font bundle.
  - Load qua resource_path, cache theo (role, size) - khong tao Font moi frame.
  - Text duoc normalize Unicode NFC truoc khi render (tranh loi dau to hop).
"""
from __future__ import annotations

import unicodedata
from typing import Optional

import pygame

from core.paths import resource_path

_FONT_DIR = "assets/fonts"

# role -> (weight file, size mac dinh)
_ROLES: dict[str, tuple[str, int]] = {
    "display": ("ExtraBold", 58),   # title man hinh lon
    "title": ("Bold", 34),          # tieu de section
    "heading": ("SemiBold", 24),    # nhom setting, ten card
    "body": ("Regular", 19),        # noi dung
    "button": ("SemiBold", 21),     # nhan nut
    "caption": ("Regular", 15),     # chu thich nho / fps
    "score": ("ExtraBold", 52),     # diem trong gameplay
    "debug": ("Regular", 14),       # overlay debug
}

_cache: dict[tuple[str, int], pygame.font.Font] = {}


class FontError(RuntimeError):
    pass


def _weight_path(weight: str) -> str:
    return str(resource_path(f"{_FONT_DIR}/BeVietnamPro-{weight}.ttf"))


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def get(role: str, size: Optional[int] = None) -> pygame.font.Font:
    """Font cho role (size None = size mac dinh cua role). Co cache."""
    weight, default_size = _ROLES.get(role, _ROLES["body"])
    size = size or default_size
    key = (weight, size)
    font = _cache.get(key)
    if font is None:
        if not pygame.font.get_init():
            pygame.font.init()
        path = _weight_path(weight)
        try:
            font = pygame.font.Font(path, size)
        except (FileNotFoundError, pygame.error) as exc:
            raise FontError(
                f"Thieu font {path}. Font Be Vietnam Pro phai duoc bundle "
                f"trong assets/fonts/ (xem THIRD_PARTY_NOTICES.md)."
            ) from exc
        _cache[key] = font
    return font


def render(role: str, text: str, color, size: Optional[int] = None,
           ) -> pygame.Surface:
    """Render text (NFC-normalized)."""
    return get(role, size).render(nfc(text), True, color)


def measure(role: str, text: str, size: Optional[int] = None
            ) -> tuple[int, int]:
    return get(role, size).size(nfc(text))


def wrap(text: str, role: str, max_width: int,
         size: Optional[int] = None) -> list[str]:
    """Ngat dong theo chieu rong pixel."""
    font = get(role, size)
    words = nfc(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if font.size(trial)[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_outlined(role: str, text: str, color, outline_color,
                    size: Optional[int] = None,
                    thickness: int = 2) -> pygame.Surface:
    """Render text co vien (cache-free; goi khi ve, khong tao font moi)."""
    font = get(role, size)
    text = nfc(text)
    base = font.render(text, True, color)
    shadow = font.render(text, True, outline_color)
    w, h = base.get_size()
    out = pygame.Surface((w + 2 * thickness, h + 2 * thickness),
                         pygame.SRCALPHA)
    for dx in (-thickness, 0, thickness):
        for dy in (-thickness, 0, thickness):
            if dx or dy:
                out.blit(shadow, (thickness + dx, thickness + dy))
    out.blit(base, (thickness, thickness))
    return out


def clear_cache() -> None:
    _cache.clear()
