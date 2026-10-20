@echo off
cd /d "%~dp0"
where pyw >nul 2>nul && (start "" pyw "%~dp0KeyClick.pyw" & exit /b 0)
where pythonw >nul 2>nul && (start "" pythonw "%~dp0KeyClick.pyw" & exit /b 0)
echo Khong tim thay Python. Hay cai Python 3 tu https://www.python.org/downloads/
echo Nho tick "Add python.exe to PATH" khi cai.
pause
