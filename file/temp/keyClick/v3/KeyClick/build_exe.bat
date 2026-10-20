@echo off
setlocal
cd /d "%~dp0"
echo ==== Dong goi KeyClick thanh file .exe ====
echo.
set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY (
  echo Khong tim thay Python. Hay cai Python 3 tu https://www.python.org/downloads/
  echo Nho tick "Add python.exe to PATH" khi cai.
  pause
  exit /b 1
)
%PY% -m pip install --upgrade pyinstaller
if errorlevel 1 goto :fail
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name KeyClick --icon keyclick.ico KeyClick.pyw
if errorlevel 1 goto :fail
echo.
echo Xong! File exe nam o: %~dp0dist\KeyClick.exe
explorer "%~dp0dist"
pause
exit /b 0

:fail
echo.
echo Co loi khi dong goi - xem thong bao o tren.
pause
exit /b 1
