@echo off
REM ACEsi - one-click OFFLINE start.
REM Uses ONLY the local .venv Python and loopback 127.0.0.1:5000.
REM No internet access, no pip checks, no cloud API calls at startup.
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "ACE_OLLAMA=1"
set "ACESI_OFFLINE=1"

set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo Starting ACEsi offline at http://127.0.0.1:5000/
start "ACEsi offline server" /min "%PY%" server.py
