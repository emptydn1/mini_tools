@echo off
rem HienConTro.bat - tat "cursor suppression" cua Windows: con tro chuot luon duoc ve,
rem ke ca luc moi bat may va luc MiniKVM dieu khien (khong can di chuot that).
rem Chi them 1 gia tri vao Registry. Muon tra lai: xem dong "TRA LAI" o cuoi file.

rem --- Chua co quyen Admin -> tu mo lai file nay bang quyen Admin (Windows se hoi) ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Dang xin quyen Admin...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo.
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableCursorSuppression /t REG_DWORD /d 0 /f
if %errorlevel% neq 0 (
    echo.
    echo [LOI] Khong ghi duoc vao Registry.
    pause
    exit /b 1
)

echo.
echo [OK] Da tat che do an con tro. Can KHOI DONG LAI may thi moi co tac dung.
echo.


rem TRA LAI nhu cu (chay trong CMD quyen Admin roi khoi dong lai):
rem reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableCursorSuppression /f