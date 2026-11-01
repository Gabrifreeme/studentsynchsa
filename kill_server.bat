@echo off
timeout /t 2 > nul
taskkill /F /IM python.exe > nul 2>&1
exit
