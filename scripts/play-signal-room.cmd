@echo off
setlocal
cd /d "%~dp0" || exit /b 1
set "SIGNAL_SAVE=%LOCALAPPDATA%\RTCW-NextGen\signal-room-%RANDOM%-%RANDOM%"
mkdir "%SIGNAL_SAVE%" || exit /b 1
start "" /wait "%CD%\RBDoom3BFG.exe" +set fs_basepath "%CD%" +set fs_savepath "%SIGNAL_SAVE%" +set r_fullscreen 0 +set r_windowWidth 960 +set r_windowHeight 600 +set s_noSound 1 +set logFile 2 +set com_signalRoom 1
if not "%ERRORLEVEL%"=="0" goto failed
exit /b 0

:failed
echo Signal Room could not start or stopped unexpectedly.
echo Log file: "%SIGNAL_SAVE%\base\qconsole.log"
pause
exit /b 1
