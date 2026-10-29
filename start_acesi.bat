@echo off
chcp 65001 >nul
echo [ACEsi Server Auto-Start]
cd /d C:\Users\chris\StudentSyncSA
python server.py
pause
