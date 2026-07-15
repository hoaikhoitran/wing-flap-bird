"""Bao boc MediaPipe Pose: xu ly frame -> landmark can thiet + ve minh hoa.

Ho tro 2 backend, tu chon theo phien ban mediapipe da cai:
  1. Tasks API (mediapipe >= 0.10.x moi, `mp.solutions` da bi go bo):
     dung PoseLandmarker + file model .task (tu tai ve assets/models/).
  2. Legacy API (`mp.solutions.pose`) cho mediapipe cu.

Chi trich xuat 6 landmark than tren can cho nhan dien vo canh:
vai trai/phai, khuyu tay trai/phai, co tay trai/phai.
"""
from __future__ import annotations

import logging
import os
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np

from core.paths import get_user_models_dir, resource_path

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    _MP_IMPORT_ERROR = ""
except Exception as exc:  # pragma: no cover - chi xay ra khi thieu thu vien
    mp = None  # type: ignore[assignment]
    MEDIAPIPE_AVAILABLE = False
    _MP_IMPORT_ERROR = str(exc)

# Chi so landmark theo chuan MediaPipe Pose (33 diem)
_L_SHOULDER, _R_SHOULDER = 11, 12
_L_ELBOW, _R_ELBOW = 13, 14
_L_WRIST, _R_WRIST = 15, 16

# Khung xuong ve len webcam (chi phan than tren + canh tay)
_SKELETON_CONNECTIONS = [
    (_L_SHOULDER, _R_SHOULDER),
    (_L_SHOULDER, _L_ELBOW), (_L_ELBOW, _L_WRIST),
    (_R_SHOULDER, _R_ELBOW), (_R_ELBOW, _R_WRIST),
    (_L_SHOULDER, 23), (_R_SHOULDER, 24), (23, 24),  # than -> hong
]

# Model .task cho Tasks API: 0=lite (nhanh), 1=full, 2=heavy
_MODEL_VARIANTS = {0: "lite", 1: "full", 2: "heavy"}
_MODEL_URL_TEMPLATE = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_{name}/float16/latest/pose_landmarker_{name}.task"
)
_MIN_MODEL_BYTES = 1_000_000  # model that luon > 1MB; nho hon = file hong
_DOWNLOAD_TIMEOUT = 30.0


@dataclass(frozen=True)
class LandmarkPoint:
    """Mot landmark da chuan hoa [0..1] kem do tin cay."""
    x: float
    y: float
    visibility: float


@dataclass(frozen=True)
class UpperBodySample:
    """6 landmark than tren cua mot frame."""
    left_shoulder: LandmarkPoint
    right_shoulder: LandmarkPoint
    left_elbow: LandmarkPoint
    right_elbow: LandmarkPoint
    left_wrist: LandmarkPoint
    right_wrist: LandmarkPoint

    @property
    def key_points(self) -> tuple[LandmarkPoint, ...]:
        return (
            self.left_shoulder, self.right_shoulder,
            self.left_elbow, self.right_elbow,
            self.left_wrist, self.right_wrist,
        )

    @property
    def min_visibility(self) -> float:
        """Visibility thap nhat trong 6 diem - dung de loc frame mat dau."""
        return min(p.visibility for p in self.key_points)

    @property
    def shoulder_width(self) -> float:
        """Khoang cach vai (don vi chuan hoa) - thuoc do ti le co the."""
        dx = self.left_shoulder.x - self.right_shoulder.x
        dy = self.left_shoulder.y - self.right_shoulder.y
        return float(np.hypot(dx, dy))


def mediapipe_import_error() -> str:
    return _MP_IMPORT_ERROR


def _model_filename(complexity: int) -> str:
    name = _MODEL_VARIANTS.get(complexity, "lite")
    return f"pose_landmarker_{name}.task"


def bundled_model_path(complexity: int) -> Path:
    """Model dong goi cung game (chi doc, qua resource_path)."""
    return resource_path(f"assets/models/{_model_filename(complexity)}")


def _valid_model(path: Path) -> bool:
    try:
        return path.exists() and path.stat().st_size > _MIN_MODEL_BYTES
    except OSError:
        return False


def ensure_pose_model(complexity: int) -> str:
    """Tra ve duong dan model .task hop le.

    Thu tu uu tien:
      1. Model BUNDLE san trong ban phat hanh (assets/models/, chi doc)
         -> release khong can Internet trong lan chay dau.
      2. Model da tai truoc do trong LocalAppData\\WingFlapBird\\models.
      3. Development fallback: tai ve LocalAppData (KHONG bao gio ghi vao
         thu muc cai dat), co timeout, luu qua file .part de chong hong.
    """
    bundled = bundled_model_path(complexity)
    if _valid_model(bundled):
        return str(bundled)

    user_path = get_user_models_dir() / _model_filename(complexity)
    if _valid_model(user_path):
        return str(user_path)

    # --- Development fallback: tai model (khong xay ra o release da bundle)
    name = _MODEL_VARIANTS.get(complexity, "lite")
    url = _MODEL_URL_TEMPLATE.format(name=name)
    tmp = str(user_path) + ".part"
    try:
        logger.info("Dang tai model pose (%s) tu %s", name, url)
        with urllib.request.urlopen(url, timeout=_DOWNLOAD_TIMEOUT) as resp, \
                open(tmp, "wb") as out:
            while True:
                chunk = resp.read(256 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        os.replace(tmp, user_path)
        if not _valid_model(user_path):
            raise RuntimeError("File model tai ve khong hop le (qua nho)")
        logger.info("Da luu model vao %s", user_path)
        return str(user_path)
    except Exception as exc:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise RuntimeError(
            f"Thieu model pose va khong tai duoc ({exc}). "
            f"Hay tai thu cong tu {url} va luu vao {user_path}"
        ) from exc


class PoseTracker:
    """Wrapper thong nhat cho ca 2 backend MediaPipe.

    Su dung:
        sample = tracker.process(frame_bgr)   # None neu khong thay nguoi
        tracker.draw(frame_bgr, sample)       # ve skeleton len frame
    """

    def __init__(self, model_complexity: int = 0) -> None:
        if not MEDIAPIPE_AVAILABLE:
            raise RuntimeError(
                f"Khong import duoc mediapipe: {_MP_IMPORT_ERROR}")
        self._backend = ""
        self._landmarker: Any = None
        self._legacy_pose: Any = None
        self._last_ts_ms = 0
        # Toa do pixel cua 33 landmark frame gan nhat (de ve skeleton)
        self._last_points: list[Optional[tuple[int, int]]] = []

        if hasattr(mp, "solutions"):
            # mediapipe cu: dung legacy API quen thuoc
            self._legacy_pose = mp.solutions.pose.Pose(
                model_complexity=model_complexity,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._backend = "legacy"
        else:
            # mediapipe moi: Tasks API + file model .task
            from mediapipe.tasks import python as mp_tasks
            from mediapipe.tasks.python import vision as mp_vision
            model_path = ensure_pose_model(model_complexity)
            options = mp_vision.PoseLandmarkerOptions(
                base_options=mp_tasks.BaseOptions(
                    model_asset_path=model_path),
                running_mode=mp_vision.RunningMode.VIDEO,
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._landmarker = mp_vision.PoseLandmarker.create_from_options(
                options)
            self._backend = "tasks"

    # ------------------------------------------------------------------
    def process(self, frame_bgr: np.ndarray) -> Optional[UpperBodySample]:
        """Chay pose detection tren 1 frame BGR. Tra ve None neu mat dau."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        if self._backend == "tasks":
            landmarks = self._process_tasks(rgb)
        else:
            landmarks = self._process_legacy(rgb)

        if landmarks is None:
            self._last_points = []
            return None

        h, w = frame_bgr.shape[:2]
        self._last_points = [
            (int(p[0] * w), int(p[1] * h)) if p is not None else None
            for p in landmarks
        ]

        def point(i: int) -> LandmarkPoint:
            x, y, vis = landmarks[i]  # type: ignore[misc]
            return LandmarkPoint(x=x, y=y, visibility=vis)

        return UpperBodySample(
            left_shoulder=point(_L_SHOULDER),
            right_shoulder=point(_R_SHOULDER),
            left_elbow=point(_L_ELBOW),
            right_elbow=point(_R_ELBOW),
            left_wrist=point(_L_WRIST),
            right_wrist=point(_R_WRIST),
        )

    def _process_tasks(
            self, rgb: np.ndarray
    ) -> Optional[list[tuple[float, float, float]]]:
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB,
                            data=np.ascontiguousarray(rgb))
        # detect_for_video yeu cau timestamp ms tang dan nghiem ngat
        ts_ms = int(time.perf_counter() * 1000)
        if ts_ms <= self._last_ts_ms:
            ts_ms = self._last_ts_ms + 1
        self._last_ts_ms = ts_ms
        result = self._landmarker.detect_for_video(mp_image, ts_ms)
        if not result.pose_landmarks:
            return None
        out = []
        for p in result.pose_landmarks[0]:
            vis = p.visibility if p.visibility is not None else 1.0
            out.append((float(p.x), float(p.y), float(vis)))
        return out

    def _process_legacy(
            self, rgb: np.ndarray
    ) -> Optional[list[tuple[float, float, float]]]:
        rgb.flags.writeable = False
        results = self._legacy_pose.process(rgb)
        if not results.pose_landmarks:
            return None
        return [(float(p.x), float(p.y), float(p.visibility))
                for p in results.pose_landmarks.landmark]

    # ------------------------------------------------------------------
    def draw(self, frame_bgr: np.ndarray,
             sample: Optional[UpperBodySample]) -> None:
        """Ve skeleton + to noi bat vai / khuyu tay / co tay len frame."""
        pts = self._last_points
        if pts:
            for a, b in _SKELETON_CONNECTIONS:
                if a < len(pts) and b < len(pts) \
                        and pts[a] is not None and pts[b] is not None:
                    cv2.line(frame_bgr, pts[a], pts[b], (255, 255, 255), 2)

        if sample is None:
            return
        h, w = frame_bgr.shape[:2]
        # (diem, mau BGR, ban kinh) - vai vang, khuyu tay xanh, co tay do
        highlights = [
            (sample.left_shoulder, (0, 215, 255), 9),
            (sample.right_shoulder, (0, 215, 255), 9),
            (sample.left_elbow, (255, 200, 0), 8),
            (sample.right_elbow, (255, 200, 0), 8),
            (sample.left_wrist, (60, 60, 255), 11),
            (sample.right_wrist, (60, 60, 255), 11),
        ]
        for pt, color, radius in highlights:
            cx, cy = int(pt.x * w), int(pt.y * h)
            if 0 <= cx < w and 0 <= cy < h:
                cv2.circle(frame_bgr, (cx, cy), radius, color, -1)
                cv2.circle(frame_bgr, (cx, cy), radius, (255, 255, 255), 2)

    def close(self) -> None:
        try:
            if self._landmarker is not None:
                self._landmarker.close()
            if self._legacy_pose is not None:
                self._legacy_pose.close()
        except Exception:
            pass
