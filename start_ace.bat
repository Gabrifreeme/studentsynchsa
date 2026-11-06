@echo off
title ACEsi Server
chcp 65001 >nul
cd /d C:\Users\chris\LipSyncStudent
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo Starting ACESi...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:5000

:: This runs the server, AND a timer that kills it if the window is closed
python server.py

:: If the server crashes or you close it, kill Python entirely
taskkill /F /IM python.exe > nul 2>&1
exit
