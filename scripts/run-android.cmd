@echo off
rem Move to the project root (parent of this scripts\ folder).
cd /d "%~dp0.."
set found=0
for /f "tokens=1" %%i in ('adb devices ^| findstr /r "device$"') do (
  set found=1
  echo Running on device: %%i
  flutter run -d %%i
)
if "%found%"=="0" echo No Android device connected. Pair/connect via adb first.