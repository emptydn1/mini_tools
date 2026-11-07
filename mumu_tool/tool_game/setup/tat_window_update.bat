@echo off
:: Tat Windows Update tren Windows 10 - chay bang quyen Administrator
net session >nul 2>&1 || (echo [!] Hay click phai file nay va chon "Run as administrator". & pause & exit /b)

echo Dang dung va vo hieu hoa dich vu Windows Update...
sc stop wuauserv >nul 2>&1
sc config wuauserv start= disabled

echo Dang dung Update Orchestrator...
sc stop UsoSvc >nul 2>&1
sc config UsoSvc start= disabled

echo Dang vo hieu hoa Windows Update Medic (dich vu tu bat lai update)...
reg add "HKLM\SYSTEM\CurrentControlSet\Services\WaaSMedicSvc" /v Start /t REG_DWORD /d 4 /f >nul 2>&1 || echo   (Bo qua: Windows khong cho sua WaaSMedicSvc)

echo Dang dat chinh sach tat tu dong cap nhat...
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoUpdate /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v AUOptions /t REG_DWORD /d 1 /f

echo Dang tat tac vu lich cap nhat...
schtasks /change /tn "\Microsoft\Windows\WindowsUpdate\Scheduled Start" /disable >nul 2>&1

echo.
echo Hoan tat. Nen khoi dong lai may.
pause