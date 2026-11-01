@echo off
chcp 65001 >nul
echo [ACEsi Server Auto-Start]
cd /d C:\Users\chris\LipSyncStudent
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
powershell -NoExit -Command "python server.py"
