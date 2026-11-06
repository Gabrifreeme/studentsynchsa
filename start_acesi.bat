@echo off
title ACEsi Server
chcp 65001 >nul
cd /d C:\Users\chris\LipSyncStudent
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: Start the server minimized
start /min python server.py

:: Wait for Chrome to close
start /wait "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:5000

:: Kill Python and exit
taskkill /F /IM python.exe > nul 2>&1
exit
