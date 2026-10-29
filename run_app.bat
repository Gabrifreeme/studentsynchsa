@echo off
echo Cleaning up old ADB connections...
adb kill-server
adb start-server

echo Connecting tablet to ACESi server...
adb -s R52N518ESBE reverse tcp:5000 tcp:5000

echo Starting Flutter app...
flutter run -d R52N518ESBE
pauseR