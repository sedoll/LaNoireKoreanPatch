@echo off
chcp 65001 > nul
title L.A. Noire 한글패치 제거 (원본 복구)
cd /d "%~dp0"
echo ============================================
echo   L.A. Noire 한글패치 제거 (원본 복구)
echo   게임과 런처(PlayLAN)를 먼저 종료해 주세요.
echo ============================================
echo.
"%~dp0python\python.exe" -I "%~dp0patcher\patcher.py" uninstall %*
if errorlevel 5 if not errorlevel 6 goto elevate
echo.
pause
exit /b
:elevate
echo.
echo 관리자 권한이 필요합니다. 권한 요청 창에서 [예]를 눌러 주세요.
powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
exit /b
