@echo off
timeout /t 2 /nobreak > nul
taskkill /F /IM python.exe > nul 2>&1
cd /d C:\Users\chris\LipSyncStudent
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
start "" /min python server.py
