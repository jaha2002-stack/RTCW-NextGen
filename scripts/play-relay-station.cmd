@echo off
setlocal
cd /d "%~dp0" || exit /b 1
set "RELAY_RUN=%LOCALAPPDATA%\RTCW-NextGen\relay-%RANDOM%-%RANDOM%"
mkdir "%RELAY_RUN%" || exit /b 1
echo Log: "%RELAY_RUN%\base\qconsole.log"
start "" /wait "%CD%\RBDoom3BFG.exe" +set fs_basepath "%CD%" +set fs_savepath "%RELAY_RUN%" +set r_fullscreen 0 +set r_windowWidth 960 +set r_windowHeight 540 +set s_noSound 1 +set logFile 2 +set com_nativeRelay 1
if not "%ERRORLEVEL%"=="0" (
    echo Relay Station exited with an error. See "%RELAY_RUN%".
    pause
    exit /b 1
)
exit /b 0
