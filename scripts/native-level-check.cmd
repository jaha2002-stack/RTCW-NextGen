@echo off
setlocal
cd /d "%~dp0" || exit /b 1
set "CHECK_DIR=%LOCALAPPDATA%\RTCW-NextGen\native-level-%RANDOM%-%RANDOM%"
mkdir "%CHECK_DIR%" || exit /b 1
robocopy "%CD%\base" "%CHECK_DIR%\base" /E /R:0 /W:0 /NFL /NDL /NJH /NJS /NP
if errorlevel 8 goto failed
start "" /wait "%CD%\RBDoom3BFG.exe" +set fs_basepath "%CHECK_DIR%" +set fs_savepath "%CHECK_DIR%" +set r_fullscreen 0 +set r_windowWidth 640 +set r_windowHeight 480 +set s_noSound 1 +set logFile 2 +set com_renderSmoke 2 +set com_nativeMapPreview maps/level
if not "%ERRORLEVEL%"=="0" goto failed
set "CHECK_LOG=%CHECK_DIR%\base\qconsole.log"
if not exist "%CHECK_DIR%\base\screenshots\native-map-preview.png" goto failed
findstr /L /C:"Native collision forward fraction=0.6553 endpoint=127.75 0.00 48.00" "%CHECK_LOG%" || goto failed
findstr /L /C:"Native collision down fraction=0.3730 endpoint=-40.00 0.00 0.25" "%CHECK_LOG%" || goto failed
findstr /L /C:"Native collision nearby fraction=1.0000 endpoint=-8.00 0.00 48.00" "%CHECK_LOG%" || goto failed
echo P02 collision check passed.
echo Capture: "%CHECK_DIR%\base\screenshots\native-map-preview.png"
echo Log: "%CHECK_LOG%"
pause
exit /b 0

:failed
echo Native level check failed. Diagnostic folder: "%CHECK_DIR%".
pause
exit /b 1
