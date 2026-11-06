@echo off
chcp 65001 >nul
echo [ACEsi WiFi Connect]
echo.

set TABLET_IP=192.168.0.100
set TABLET_PORT=36512
set ACEsi_DIR=C:\Users\chris\StudentSyncSA

echo [1/4] Connecting to tablet %TABLET_IP%:%TABLET_PORT%...
adb connect %TABLET_IP%:%TABLET_PORT% >nul 2>&1
adb devices
echo.

echo [2/4] Checking StudentSyncSA...
adb -s %TABLET_IP%:%TABLET_PORT% shell ps | findstr studentsyncsa >nul
if %errorlevel% == 0 (
    echo [OK] StudentSyncSA already running
) else (
    echo [3/4] Launching StudentSyncSA...
    adb -s %TABLET_IP%:%TABLET_PORT% shell monkey -p com.studentsyncsa.studentsyncsa 1
    timeout /t 3 /nobreak >nul
)
echo.

echo [4/4] Checking ACEsi server...
python -c "import requests; requests.get('http://localhost:5000/chat', timeout=2)" >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] ACEsi server is running
) else (
    echo [START] Starting ACEsi server...
    start /B python "%ACEsi_DIR%\server.py"
    timeout /t 3 /nobreak >nul
)
echo.
echo Done. Try: "read webview"
