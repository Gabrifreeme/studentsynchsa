@echo off
cd /d C:\Users\chris\StudentSyncSA
adb connect 192.168.0.100:39085
timeout /t 2 /nobreak > nul
start /min python server.py
timeout /t 5 /nobreak > nul
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:5000
exit
