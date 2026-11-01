@echo off
title ACESi Server
cd /d C:\Users\chris\LipSyncStudent
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo Starting ACESi Server...
start /B python server.py

echo Waiting for server to boot...
timeout /t 5 /nobreak > nul

echo Opening ACESi...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:5000

echo.
echo ACESi is running!
echo To QUIT: Just close this window (or press Ctrl+C).
echo.
pause
