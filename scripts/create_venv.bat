@echo off
REM Tao virtual environment + cai dependency cho developer.
setlocal
cd /d "%~dp0.."
python --version || (
    echo [LOI] Khong tim thay Python. Cai Python 3.11 x64 truoc.
    exit /b 1
)
python -m venv .venv || exit /b 1
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt || exit /b 1
echo.
echo Xong. Chay game: scripts\run_source.bat
endlocal
