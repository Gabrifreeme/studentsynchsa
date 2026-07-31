@echo off
cd /d C:\Users\chris\StudentSyncSA
start /min python server.py
timeout /t 5 /nobreak > nul
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:5000
exit
