# Changelog

## v0.1.0-beta — 2026-07-15

### Added
- Webcam-controlled wing flap gameplay (raise both arms, bring them down
  quickly = one flap)
- MediaPipe Pose detection (Tasks API, bundled `pose_landmarker_lite` model —
  no Internet required on first run)
- Guided calibration flow with progress bar, skip/retry, distance and
  lighting hints; results persist per camera in LocalAppData
- Easy and Normal difficulty (switchable in Settings, applies on next run)
- Keyboard fallback (SPACE) — game is fully playable without a camera
- Main menu, Settings (camera picker with scan/test/preview, sensitivity,
  audio, display, data reset), How to Play with live gesture test,
  Credits, Pause menu
- First-run privacy notice; local-only webcam processing (see PRIVACY.md)
- Vietnamese and English UI
- High score persistence in `%LOCALAPPDATA%\WingFlapBird`
- Optional developer support link (disabled until configured)
- Windows executable build (PyInstaller onedir) + GitHub Actions CI/release
- Rotating file log + friendly crash screen

### Known issues
- Webcam compatibility may vary between devices and drivers
- Windows SmartScreen may warn because the build is unsigned
- Only Windows x64 is officially packaged in this beta
- Camera device names are shown as "Camera 0/1/..." (OpenCV cannot query
  friendly device names)
