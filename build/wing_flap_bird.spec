# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec cho Wing Flap Bird (Windows onedir, windowed).

Build:
    pyinstaller build/wing_flap_bird.spec --clean --noconfirm ^
        --workpath build_tmp --distpath dist

Ket qua: dist/WingFlapBird/WingFlapBird.exe
- Bundle: assets/ (model pose .task, icon, am thanh neu co) + data mediapipe.
- KHONG bundle: .venv, tests, cache, tools dev.
"""
import os

from PyInstaller.utils.hooks import collect_data_files

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))  # noqa: F821

datas = [
    (os.path.join(ROOT, "assets"), "assets"),
]
# mediapipe can cac file .binarypb/.tflite di kem package
datas += collect_data_files("mediapipe")

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Chi la dev/test tooling - khong can trong ban phat hanh
        "tests", "pytest", "pip", "setuptools", "wheel",
        "tkinter", "IPython",
        # LUU Y: KHONG exclude matplotlib/PIL - mediapipe 0.10.35 import
        # matplotlib ngay khi import (da xac thuc bang exe smoke test:
        # exclude se lam frozen build chet voi "No module named matplotlib").
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WingFlapBird",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # windowed app - khong hien terminal
    icon=os.path.join(ROOT, "assets", "icon", "wing_flap_bird.ico"),
    version=os.path.join(SPECPATH, "version_info.txt"),  # noqa: F821
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="WingFlapBird",
)
