#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"
$ProgressPreference = 'SilentlyContinue'

Write-Host "======================================="
Write-Host " Development Environment Setup"
Write-Host "======================================="
# powershell -ExecutionPolicy Bypass -File download.ps1

$DownloadDir = "C:\Users\huy\Downloads"
New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null

# ============================================================
# [1/6] Python 3.10.0
# ============================================================
Write-Host ""
Write-Host "[1/6] Installing Python 3.10.0..."
$pythonUrl = "https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe"
$pythonInstaller = "$DownloadDir\python-3.10.0-amd64.exe"

Invoke-WebRequest $pythonUrl -OutFile $pythonInstaller
Start-Process -FilePath $pythonInstaller -Wait

# ============================================================
# [2/6] Node.js 22.6.0
# ============================================================
Write-Host ""
Write-Host "[2/6] Installing Node.js 22.6.0..."
$nodeUrl = "https://nodejs.org/dist/v22.6.0/node-v22.6.0-x64.msi"
$nodeInstaller = "$DownloadDir\node-v22.6.0-x64.msi"

Invoke-WebRequest $nodeUrl -OutFile $nodeInstaller
Start-Process -FilePath $nodeInstaller -Wait

# ============================================================
# [3/6] ADB (Android Platform Tools)
# ============================================================
Write-Host ""
Write-Host "[3/6] Installing Android Platform Tools..."
$adbUrl = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
$adbZip = "$DownloadDir\platform-tools.zip"

Invoke-WebRequest $adbUrl -OutFile $adbZip
Expand-Archive -Path $adbZip -DestinationPath "C:\" -Force

$adbPath = "C:\platform-tools"
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($machinePath -notlike "*$adbPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$machinePath;$adbPath", "Machine")
}

# ============================================================
# [4/6] Chocolatey
# ============================================================
Write-Host ""
Write-Host "[4/6] Installing Chocolatey..."
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString("https://community.chocolatey.org/install.ps1"))

# Reload env để nhận lệnh choco ngay lập tức trong phiên này
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

# ============================================================
# [5/6] Visual Studio 2019 Community
# ============================================================
Write-Host ""
Write-Host "[5/6] Installing Visual Studio 2019 Community..."
choco install visualstudio2019community -y --no-progress

# ============================================================
# [6/6] OpenCV 4.11.0
# ============================================================
Write-Host ""
Write-Host "[6/6] Installing OpenCV 4.11.0..."
choco install opencv --version=4.11.0 -y --no-progress

# ============================================================
# OpenCV Environment Variables
# ============================================================
Write-Host ""
Write-Host "Configuring OpenCV Environment Variables..."
$opencvRoot = "C:\tools\opencv\build"

if (Test-Path "$opencvRoot\x64\vc16\bin") {
    [Environment]::SetEnvironmentVariable("OPENCV_BIN_DIR", "$opencvRoot\x64\vc16\bin", "Machine")
    [Environment]::SetEnvironmentVariable("OPENCV_INCLUDE_DIR", "$opencvRoot\include", "Machine")
    [Environment]::SetEnvironmentVariable("OPENCV_LIB_DIR", "$opencvRoot\x64\vc16\lib", "Machine")

    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($machinePath -notlike "*$opencvRoot\x64\vc16\bin*") {
        [Environment]::SetEnvironmentVariable("Path", "$machinePath;$opencvRoot\x64\vc16\bin", "Machine")
    }
} else {
    Write-Warning "OpenCV path not found. Environment variables were not set."
}

# ============================================================
# Verification
# ============================================================
Write-Host ""
Write-Host "======================================="
Write-Host " Installed Versions Verification"
Write-Host "======================================="

# Cập nhật lại PATH hiện tại của phiên chạy để test nhanh công cụ vừa cài
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

try { cmd /c python --version } catch { Write-Host "Python is not recognized yet." }
try { cmd /c node --version } catch { Write-Host "Node.js is not recognized yet." }
try { cmd /c adb version | Select-Object -First 1 } catch { Write-Host "ADB is not recognized yet." }

Write-Host ""
Write-Host "Setup completed successfully."
Write-Host "IMPORTANT: Please restart your terminal or restart Windows to apply all changes."
pause