@echo off
REM Chay game tu source (developer only).
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
    echo [LOI] Chua co virtual environment. Chay scripts\create_venv.bat truoc.
    exit /b 1
)
.venv\Scripts\python.exe main.py %*
endlocal
