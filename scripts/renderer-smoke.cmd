@echo off
setlocal
cd /d "%~dp0" || exit /b 1
set "SMOKE_SAVE=%LOCALAPPDATA%\RTCW-NextGen\renderer-smoke-%RANDOM%-%RANDOM%"
mkdir "%SMOKE_SAVE%" || exit /b 1
start "" /wait "%CD%\RBDoom3BFG.exe" +set fs_basepath "%CD%" +set fs_savepath "%SMOKE_SAVE%" +set r_fullscreen 0 +set r_windowWidth 640 +set r_windowHeight 480 +set s_noSound 1 +set logFile 2 +set com_renderSmoke 2
if not "%ERRORLEVEL%"=="0" goto failed
if not exist "%SMOKE_SAVE%\base\screenshots\renderer-smoke.png" goto failed
echo Capture: "%SMOKE_SAVE%\base\screenshots\renderer-smoke.png"
exit /b 0

:failed
echo Renderer smoke test failed. See "%SMOKE_SAVE%\base\qconsole.log".
pause
exit /b 1
