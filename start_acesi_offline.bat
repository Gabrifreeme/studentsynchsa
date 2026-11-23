@echo off
REM ACEsi - one-click local start.
REM Uses ONLY the local .venv Python and loopback 127.0.0.1:5000.
REM Ollama was removed from this PC, so no local model is forced and offline
REM lock is off - the saved Gemini/Groq keys are used for AI replies.
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "ACE_OLLAMA=0"
set "ACESI_OFFLINE=0"
set "ACESI_LOCAL_ONLY=0"

set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo Starting ACEsi at http://127.0.0.1:5000/ (cloud model from Settings)
start "ACEsi server" /min "%PY%" server.py
