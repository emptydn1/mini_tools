@echo off
setlocal

:: ==========================================================
:: run_setup.bat
:: Chay file download.ps1 (Development Environment Setup)
:: voi quyen Administrator
:: ==========================================================

:: Ten file .ps1 can chay (dat cung thu muc voi file .bat nay)
set "PS1_FILE=%~dp0setup.ps1"

:: Kiem tra file .ps1 co ton tai khong
if not exist "%PS1_FILE%" (
    echo Khong tim thay file: %PS1_FILE%
    echo Hay dat file download.ps1 cung thu muc voi run_setup.bat
    pause
    exit /b 1
)

:: Kiem tra quyen Administrator, neu chua co thi tu elevate
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Dang yeu cau quyen Administrator...
    powershell -NoProfile -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo =======================================
echo  Bat dau chay Development Environment Setup
echo =======================================

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1_FILE%"

echo.
echo Da chay xong. Nhan phim bat ky de dong.
pause >nul
endlocal