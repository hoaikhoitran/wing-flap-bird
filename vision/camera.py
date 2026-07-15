"""Wrapper quanh cv2.VideoCapture: mo / doc / mo lai an toan.

Khong bao gio nem exception ra ngoai - moi loi deu tra ve None/False
de vision thread tu xu ly (hien canh bao + thu ket noi lai).
"""
from __future__ import annotations

import sys
from typing import Optional

import cv2
import numpy as np


def scan_available_cameras(max_index: int = 5) -> list[int]:
    """Quet nhanh cac camera index kha dung (0..max_index).

    Mo va release TUNG camera mot (khong giu nhieu VideoCapture cung luc).
    Ham nay blocking vai giay -> goi tu thread rieng, khong goi trong
    game loop.
    """
    available: list[int] = []
    for index in range(max_index + 1):
        cap = None
        try:
            if sys.platform == "win32":
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ok, frame = cap.read()
                if ok and frame is not None:
                    available.append(index)
        except Exception:
            pass
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
    return available


class Camera:
    """Doc frame tu webcam, chiu duoc viec webcam bi rut / bi chiem dung."""

    def __init__(self, index: int, width: int, height: int) -> None:
        self.index = index
        self.width = width
        self.height = height
        self._cap: Optional[cv2.VideoCapture] = None
        self._consecutive_failures = 0

    def open(self) -> bool:
        """Thu mo webcam. Tra ve True neu doc duoc frame dau tien."""
        self.release()
        try:
            # CAP_DSHOW giup mo camera nhanh hon dang ke tren Windows
            if sys.platform == "win32":
                cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(self.index)
            if not cap.isOpened():
                cap.release()
                return False
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            ok, frame = cap.read()
            if not ok or frame is None:
                cap.release()
                return False
            self._cap = cap
            self._consecutive_failures = 0
            return True
        except Exception:
            self._cap = None
            return False

    def read(self) -> Optional[np.ndarray]:
        """Doc 1 frame BGR. Tra ve None neu that bai."""
        if self._cap is None:
            return None
        try:
            ok, frame = self._cap.read()
        except Exception:
            ok, frame = False, None
        if not ok or frame is None:
            self._consecutive_failures += 1
            # Nhieu frame hong lien tiep -> coi nhu webcam da bi ngat
            if self._consecutive_failures >= 15:
                self.release()
            return None
        self._consecutive_failures = 0
        return frame

    @property
    def is_open(self) -> bool:
        return self._cap is not None

    def release(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
