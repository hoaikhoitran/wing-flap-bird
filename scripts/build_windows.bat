@echo off
REM ============================================================
REM Build Wing Flap Bird cho Windows (developer only).
REM Ket qua: dist\WingFlapBird\WingFlapBird.exe
REM          release\WingFlapBird-v<version>-Windows-x64.zip
REM ============================================================
setlocal
cd /d "%~dp0.."

REM 1. Kiem tra Python trong venv
if not exist ".venv\Scripts\python.exe" (
    echo [LOI] Chua co virtual environment. Chay scripts\create_venv.bat truoc.
    exit /b 1
)
set PY=.venv\Scripts\python.exe
%PY% --version || exit /b 1

REM 2. Chay test truoc khi build - KHONG build neu test fail
echo === Chay pytest ===
%PY% -m pytest tests -q || (
    echo [LOI] Test that bai - dung build.
    exit /b 1
)

REM 3. Xoa build cu
if exist build_tmp rmdir /s /q build_tmp
if exist dist rmdir /s /q dist

REM 4. Build PyInstaller
echo === Build PyInstaller ===
%PY% -m PyInstaller build\wing_flap_bird.spec --clean --noconfirm ^
    --workpath build_tmp --distpath dist || (
    echo [LOI] PyInstaller that bai.
    exit /b 1
)

REM 5. Smoke test exe (khong camera, tu thoat sau ~120 frame)
echo === Smoke test EXE ===
dist\WingFlapBird\WingFlapBird.exe --smoke --no-camera
if errorlevel 1 (
    echo [LOI] EXE smoke test that bai.
    exit /b 1
)

REM 6. Dong goi ZIP + copy docs
echo === Dong goi release ===
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\package_release.ps1 || exit /b 1

echo.
echo === HOAN TAT ===
echo EXE: dist\WingFlapBird\WingFlapBird.exe
dir release
endlocal
