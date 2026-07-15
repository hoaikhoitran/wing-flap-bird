"""VisionSystem - thread rieng doc webcam + chay MediaPipe + WingFlapDetector.

Thiet ke de webcam KHONG BAO GIO lam game loop bi dung:
  - Toan bo I/O camera va pose detection chay trong 1 thread nen.
  - Game loop chi doc "snapshot" (bao ve bang Lock) va goi consume_flaps().
  - Su kien flap duoc cong don thanh counter, dam bao khong mat su kien
    ke ca khi FPS camera thap hon FPS game.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

import config
from vision.camera import Camera
from vision.flap_detector import (DetectorState, PoseMetrics,
                                  WingFlapDetector)
from vision.pose_tracker import (MEDIAPIPE_AVAILABLE, PoseTracker,
                                 mediapipe_import_error)

logger = logging.getLogger(__name__)


@dataclass
class VisionSnapshot:
    """Anh chup trang thai vision tai mot thoi diem (immutable voi game loop)."""
    camera_ok: bool = False
    camera_message: str = "Đang khởi động webcam..."
    has_pose: bool = False
    detector_state: str = DetectorState.NO_POSE.value
    cooldown_remaining: float = 0.0
    flap_cooldown: float = 0.35
    flap_total: int = 0
    vision_fps: float = 0.0
    frame_rgb: Optional[np.ndarray] = None  # frame RGB da lat guong + ve landmark
    metrics: Optional[PoseMetrics] = None
    debug: dict[str, str] = field(default_factory=dict)


class VisionSystem:
    """Quan ly camera + pose + flap detector trong thread rieng."""

    def __init__(self, camera_index: int = 0) -> None:
        self._camera = Camera(camera_index, config.CAMERA_WIDTH,
                              config.CAMERA_HEIGHT)
        self._detector = WingFlapDetector(config.FlapDetectorConfig())
        self._tracker: Optional[PoseTracker] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        self._pending_flaps = 0
        self._snapshot = VisionSnapshot(
            flap_cooldown=self._detector.config.flap_cooldown)
        self.available = MEDIAPIPE_AVAILABLE

    # ------------------------------------------------------------------
    # Vong doi
    # ------------------------------------------------------------------
    def start(self) -> bool:
        """Khoi dong thread vision. Tra ve False neu thieu mediapipe."""
        if not MEDIAPIPE_AVAILABLE:
            self._set_snapshot(VisionSnapshot(
                camera_ok=False,
                camera_message=("Chưa cài mediapipe: "
                                + mediapipe_import_error()[:60]),
            ))
            return False
        if self._thread is not None:
            return True
        self._running = True
        self._thread = threading.Thread(target=self._loop,
                                        name="vision-thread", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        self._camera.release()
        if self._tracker is not None:
            self._tracker.close()
            self._tracker = None
        logger.info("Vision system stopped")

    @property
    def running(self) -> bool:
        return self._thread is not None and self._running

    @property
    def camera_index(self) -> int:
        return self._camera.index

    def set_camera_index(self, index: int) -> bool:
        """Doi camera trong runtime: dung thread cu, mo camera moi.

        Camera cu duoc release day du truoc khi mo camera moi
        (khong giu nhieu VideoCapture cung luc).
        """
        if index == self._camera.index and self.running:
            return True
        was_running = self.running
        self.stop()
        self._camera = Camera(index, config.CAMERA_WIDTH,
                              config.CAMERA_HEIGHT)
        logger.info("Camera index -> %d", index)
        if was_running:
            return self.start()
        return True

    # ------------------------------------------------------------------
    # API cho game loop (thread-safe)
    # ------------------------------------------------------------------
    def consume_flaps(self) -> int:
        """Lay so su kien flap tich luy tu lan goi truoc (va reset ve 0)."""
        with self._lock:
            n = self._pending_flaps
            self._pending_flaps = 0
            return n

    def snapshot(self) -> VisionSnapshot:
        with self._lock:
            return self._snapshot

    def apply_calibration(self, up_margin_ratio: float,
                          down_margin_ratio: float) -> None:
        """Nhan threshold moi tu man hinh calibration."""
        with self._lock:
            self._detector.apply_thresholds(up_margin_ratio,
                                            down_margin_ratio)
        logger.info("Calibration ap dung: up=%.3f down=%.3f",
                    up_margin_ratio, down_margin_ratio)

    def apply_sensitivity(self, sensitivity: float) -> None:
        """Ap slider sensitivity (0.5..1.5) vao detector, co clamp."""
        with self._lock:
            self._detector.config.apply_sensitivity(sensitivity)

    def apply_flap_cooldown(self, seconds: float) -> None:
        """Cooldown theo do kho (easy 220ms / normal 300ms)."""
        with self._lock:
            self._detector.config.flap_cooldown = max(0.15,
                                                      min(0.45, seconds))

    # ------------------------------------------------------------------
    # Thread nen
    # ------------------------------------------------------------------
    def _loop(self) -> None:
        try:
            self._tracker = PoseTracker(config.POSE_MODEL_COMPLEXITY)
        except Exception as exc:
            self._set_snapshot(VisionSnapshot(
                camera_ok=False,
                camera_message=f"Lỗi khởi tạo MediaPipe: {exc}"[:80]))
            self.available = False
            return

        min_frame_time = 1.0 / config.VISION_MAX_FPS
        last_retry = 0.0
        fps_ema = 0.0
        prev_ts = time.perf_counter()

        while self._running:
            loop_start = time.perf_counter()

            # --- Dam bao camera dang mo, tu ket noi lai khi bi ngat ---
            if not self._camera.is_open:
                now = time.perf_counter()
                if now - last_retry >= config.CAMERA_RETRY_INTERVAL:
                    last_retry = now
                    if not self._camera.open():
                        self._publish(camera_ok=False,
                                      camera_message=("Không mở được webcam "
                                                      f"(index={self._camera.index}) "
                                                      "- đang thử lại..."),
                                      frame_rgb=None, fps=0.0)
                time.sleep(0.05)
                continue

            frame = self._camera.read()
            if frame is None:
                self._publish(camera_ok=False,
                              camera_message="Webcam bị ngắt - đang kết nối lại...",
                              frame_rgb=None, fps=0.0)
                continue

            # --- Lat guong de nguoi choi de dinh huong ---
            frame = cv2.flip(frame, 1)

            # --- Pose detection + flap detection ---
            ts = time.perf_counter()
            try:
                sample = self._tracker.process(frame)
            except Exception:
                sample = None
            flapped = self._detector.update(sample, ts)

            # --- Ve landmark len frame hien thi ---
            try:
                self._tracker.draw(frame, sample)
            except Exception:
                pass
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # --- Tinh FPS cua vision thread (EMA) ---
            dt = ts - prev_ts
            prev_ts = ts
            if dt > 0:
                fps_ema = fps_ema + 0.15 * (1.0 / dt - fps_ema)

            debug = self._detector.debug_info(ts) if config.DEBUG_MODE else {}

            with self._lock:
                if flapped:
                    self._pending_flaps += 1
                self._snapshot = VisionSnapshot(
                    camera_ok=True,
                    camera_message="OK",
                    has_pose=self._detector.state is not DetectorState.NO_POSE,
                    detector_state=self._detector.state.value,
                    cooldown_remaining=self._detector.cooldown_remaining(ts),
                    flap_cooldown=self._detector.config.flap_cooldown,
                    flap_total=self._detector.flap_count,
                    vision_fps=fps_ema,
                    frame_rgb=rgb,
                    metrics=self._detector.metrics,
                    debug=debug,
                )

            # --- Gioi han toc do xu ly de nhuong CPU cho game ---
            elapsed = time.perf_counter() - loop_start
            if elapsed < min_frame_time:
                time.sleep(min_frame_time - elapsed)

    # ------------------------------------------------------------------
    def _publish(self, camera_ok: bool, camera_message: str,
                 frame_rgb: Optional[np.ndarray], fps: float) -> None:
        """Cap nhat snapshot khi camera loi (giu nguyen flap counter)."""
        with self._lock:
            self._snapshot = VisionSnapshot(
                camera_ok=camera_ok,
                camera_message=camera_message,
                has_pose=False,
                detector_state=DetectorState.NO_POSE.value,
                flap_cooldown=self._detector.config.flap_cooldown,
                flap_total=self._detector.flap_count,
                vision_fps=fps,
                frame_rgb=frame_rgb,
                metrics=None,
                debug={},
            )

    def _set_snapshot(self, snap: VisionSnapshot) -> None:
        with self._lock:
            self._snapshot = snap
