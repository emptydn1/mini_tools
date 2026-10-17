# driver-history.ps1  (v2)
# Collects every trace of display (GPU) driver versions this PC has used:
#   1) setupapi*.log files   - Windows' own driver install logs (INF, Panther, Windows.old, $WINDOWS.~BT)
#   2) Windows Update history - drivers installed through Windows Update
#   3) Event log Kernel-PnP/Configuration, event 400 (recent history only)
#   4) Leftover installer files/folders (C:\NVIDIA\DisplayDriver, NVIDIA downloader cache, Downloads)
# It also prints when Windows was installed / upgraded, and which log files it could read.
#
# Run in PowerShell opened as Administrator:
#   powershell -ExecutionPolicy Bypass -File .\driver-history.ps1
# Optional: save the result as CSV
#   powershell -ExecutionPolicy Bypass -File .\driver-history.ps1 -Csv .\driver-history.csv

param(
    [string[]]$LogDir = @(
        "$env:windir\INF",
        "$env:windir\Panther",
        "$env:SystemDrive\Windows.old\Windows\INF",
        "$env:SystemDrive\Windows.old\Windows\Panther",
        "$env:SystemDrive\`$WINDOWS.~BT\Sources\Panther"
    ),
    [string[]]$InstallerDir = @(
        "$env:SystemDrive\NVIDIA\DisplayDriver",
        "$env:ProgramData\NVIDIA Corporation\Downloader",
        "$env:USERPROFILE\Downloads"
    ),
    [string]$Csv
)

$DisplayGuid = '4d36e968-e325-11ce-bfc1-08002be10318'
$records     = New-Object System.Collections.Generic.List[object]
$fileReport  = New-Object System.Collections.Generic.List[object]

function Get-Vendor([string]$text) {
    if     ($text -match 'NVIDIA|VEN_10DE')      { 'NVIDIA' }
    elseif ($text -match 'Intel|VEN_8086')       { 'Intel' }
    elseif ($text -match 'AMD|ATI|Advanced Micro|VEN_1002') { 'AMD' }
    elseif ($text -match 'Microsoft')            { 'Microsoft' }
    else                                         { 'Other' }
}

# The version number people know:
#   NVIDIA 32.0.16.1062  -> 610.62
#   Intel  30.0.100.9864 -> 100.9864
function Get-ShortVer([string]$vendor, [string]$v) {
    $p = $v.Split('.')
    if ($p.Count -ne 4) { return $v }
    if ($vendor -eq 'NVIDIA') {
        $n = $p[2] + $p[3].PadLeft(4, '0')
        if ($n.Length -lt 5) { return $v }
        $n = $n.Substring($n.Length - 5)
        return '{0}.{1}' -f $n.Substring(0, 3), $n.Substring(3)
    }
    if ($vendor -eq 'Intel') { return '{0}.{1}' -f $p[2], $p[3] }
    return $v
}

function Add-Record($firstSeen, $vendor, $version, $shortVer, $drvDate, $source) {
    if (-not $shortVer -and $version) { $shortVer = Get-ShortVer $vendor $version }
    $records.Add([pscustomobject]@{
        FirstSeen  = $firstSeen
        Vendor     = $vendor
        Version    = $version
        ShortVer   = $shortVer
        DriverDate = $drvDate
        Source     = $source
    })
}

# Opens a log even while Windows has it open for writing.
function Read-LogLines([string]$path) {
    $share = [System.IO.FileShare]'ReadWrite, Delete'
    $fs = New-Object System.IO.FileStream($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $share)
    $sr = New-Object System.IO.StreamReader($fs, $true)
    try {
        $lines = New-Object System.Collections.Generic.List[string]
        while ($null -ne ($line = $sr.ReadLine())) { $lines.Add($line) }
        return ,$lines
    } finally { $sr.Dispose() }
}

function Show-Table($data, $props) {
    $text = $data | Format-Table -Property $props -AutoSize | Out-String -Width 300
    foreach ($l in ($text -split "`r?`n")) { $l = $l.TrimEnd(); if ($l) { Write-Host $l } }
}

# ---------- 1) setupapi*.log ----------
$logFiles = foreach ($dir in $LogDir) {
    if ($dir -and (Test-Path -LiteralPath $dir)) {
        Get-ChildItem -LiteralPath $dir -Filter 'setupapi*.log' -Recurse -ErrorAction SilentlyContinue
    }
}

foreach ($f in ($logFiles | Sort-Object FullName -Unique)) {
    $info = [pscustomobject]@{ File = $f.FullName; From = ''; To = ''; GpuEntries = 0; Status = 'ok' }
    try { $lines = Read-LogLines $f.FullName }
    catch { $info.Status = 'CANNOT READ: ' + $_.Exception.InnerException.Message + $_.Exception.Message; $fileReport.Add($info); continue }

    $time = $null; $cur = @{}
    foreach ($line in $lines) {
        if ($line -match '^>>>\s+Section start\s+(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})') {
            $time = $Matches[1]
            if (-not $info.From) { $info.From = $time }
            $info.To = $time
            $cur = @{}
            continue
        }
        if ($line -match '^>>>\s+\[|Setup Import Driver Package') { $cur = @{}; continue }

        if     ($line -match 'inf:\s+Provider:\s*(.+?)\s*$')                     { $cur.Provider = $Matches[1] }
        elseif ($line -match 'inf:\s+Class GUID:\s*\{?([0-9a-fA-F-]{36})')       { $cur.Guid = $Matches[1] }
        elseif ($line -match 'inf:\s+Driver Version:\s*([\d/]+)\s*,\s*([\d.]+)') { $cur.Date = $Matches[1]; $cur.Version = $Matches[2] }
        else { continue }

        if ($cur.Provider -and $cur.Guid -and $cur.Version) {
            if ($cur.Guid -eq $DisplayGuid) {
                Add-Record $time (Get-Vendor $cur.Provider) $cur.Version $null $cur.Date 'setupapi log'
                $info.GpuEntries++
            }
            $cur = @{}
        }
    }
    $fileReport.Add($info)
}

# ---------- 2) Windows Update history ----------
$wuNote = ''
try {
    $searcher = (New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher()
    $total = $searcher.GetTotalHistoryCount()
    $wuFound = 0
    if ($total -gt 0) {
        foreach ($h in $searcher.QueryHistory(0, $total)) {
            if ($h.ResultCode -ne 2 -and $h.ResultCode -ne 3) { continue }
            if ($h.Title -notmatch '\bDisplay\b') { continue }
            if ($h.Title -match '(\d+\.\d+\.\d+\.\d+)') {
                Add-Record $h.Date.ToLocalTime().ToString('yyyy/MM/dd HH:mm:ss') (Get-Vendor $h.Title) $Matches[1] $null '' 'Windows Update'
                $wuFound++
            }
        }
    }
    $wuNote = "$total history entries, $wuFound display drivers"
} catch { $wuNote = 'not available: ' + $_.Exception.Message }

# ---------- 3) Kernel-PnP/Configuration event 400 ----------
$evNote = ''
try {
    $events = Get-WinEvent -FilterHashtable @{ LogName = 'Microsoft-Windows-Kernel-PnP/Configuration'; Id = 400 } -ErrorAction Stop
    $evFound = 0
    foreach ($e in $events) {
        $d = @{}
        try { foreach ($n in ([xml]$e.ToXml()).Event.EventData.Data) { $d[$n.Name] = $n.'#text' } } catch { }
        if (-not ("$($d.ClassGuid) $($e.Message)" -match $DisplayGuid)) { continue }
        $ver = $d.DriverVersion; $date = $d.DriverDate; $prov = $d.DriverProvider
        if (-not $ver  -and $e.Message -match 'Driver Version:\s*(\S+)') { $ver  = $Matches[1] }
        if (-not $date -and $e.Message -match 'Driver Date:\s*(\S+)')    { $date = $Matches[1] }
        if (-not $prov -and $e.Message -match 'Driver Provider:\s*(.+)') { $prov = $Matches[1] }
        if (-not $ver) { continue }
        Add-Record $e.TimeCreated.ToString('yyyy/MM/dd HH:mm:ss') (Get-Vendor "$prov $($d.DeviceInstanceId)") $ver $null $date 'event log'
        $evFound++
    }
    $oldestEv = ($events | Select-Object -Last 1).TimeCreated
    $evNote = "$evFound display entries, log goes back to " + $(if ($oldestEv) { $oldestEv.ToString('yyyy/MM/dd') } else { '-' })
} catch { $evNote = 'not available: ' + $_.Exception.Message }

# ---------- 4) Leftover installer files / folders ----------
foreach ($dir in $InstallerDir) {
    if (-not $dir -or -not (Test-Path -LiteralPath $dir)) { continue }
    foreach ($it in Get-ChildItem -LiteralPath $dir -Recurse -Depth 1 -ErrorAction SilentlyContinue) {
        $seen = $it.CreationTime.ToString('yyyy/MM/dd HH:mm:ss')
        if ($it.PSIsContainer) {
            if ($it.FullName -match 'NVIDIA' -and $it.Name -match '^(\d{3}\.\d{2})$') {
                Add-Record $seen 'NVIDIA' '' $Matches[1] '' 'installer folder'
            }
        }
        elseif ($it.Extension -match '^\.(exe|zip)$') {
            if ($it.Name -match '^(\d{3}\.\d{2})-.*(notebook|desktop|win1|dch|whql)') {
                Add-Record $seen 'NVIDIA' '' $Matches[1] '' 'installer file'
            }
            elseif ($it.Name -match '^gfx_win_(\d{3}\.\d{4})') {
                Add-Record $seen 'Intel' '' $Matches[1] '' 'installer file'
            }
        }
    }
}

# ---------- Drivers in use right now ----------
$current = @{}
try {
    foreach ($c in Get-CimInstance Win32_PnPSignedDriver -Filter "DeviceClass='DISPLAY'" -ErrorAction Stop) {
        if (-not $c.DriverVersion) { continue }
        $v = Get-Vendor "$($c.DriverProviderName) $($c.DeviceID)"
        $current["$v|$(Get-ShortVer $v $c.DriverVersion)"] = $c.DriverVersion
    }
} catch { }

# ---------- Merge: one row per version, earliest sighting ----------
$rows = New-Object System.Collections.Generic.List[object]
foreach ($g in ($records | Group-Object Vendor, ShortVer)) {
    $items = @($g.Group | Sort-Object FirstSeen)
    $first = $items[0]
    $key   = "$($first.Vendor)|$($first.ShortVer)"
    $full  = ($items | Where-Object { $_.Version } | Select-Object -First 1).Version
    $ddate = ($items | Where-Object { $_.DriverDate } | Select-Object -First 1).DriverDate
    $inUse = ''
    if ($current.ContainsKey($key)) { $inUse = 'IN USE'; $current.Remove($key) }
    $rows.Add([pscustomobject]@{
        Vendor = $first.Vendor; ShortVer = $first.ShortVer; Version = $full; DriverDate = $ddate
        FirstSeen = $first.FirstSeen; Now = $inUse
        Source = (($items | ForEach-Object { $_.Source } | Select-Object -Unique) -join ', ')
    })
}
foreach ($k in $current.Keys) {
    $v, $s = $k.Split('|')
    $rows.Add([pscustomobject]@{
        Vendor = $v; ShortVer = $s; Version = $current[$k]; DriverDate = ''
        FirstSeen = '?'; Now = 'IN USE'; Source = 'installed now, not found in any log'
    })
}

# ---------- Output ----------
Write-Host ''
Write-Host '=== Windows install / upgrade dates ==='
try {
    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
    Write-Host ("Current : {0} (build {1}), installed or last upgraded {2}" -f $os.Caption, $os.BuildNumber, $os.InstallDate.ToString('yyyy/MM/dd HH:mm'))
} catch { Write-Host 'Current : unknown' }
try {
    foreach ($k in (Get-ChildItem 'HKLM:\SYSTEM\Setup' -ErrorAction Stop | Where-Object { $_.PSChildName -like 'Source OS*' })) {
        $p = Get-ItemProperty -LiteralPath $k.PSPath
        $d = [DateTimeOffset]::FromUnixTimeSeconds([int64]$p.InstallDate).LocalDateTime
        Write-Host ("Earlier : build {0}, installed {1}  [{2}]" -f $p.CurrentBuild, $d.ToString('yyyy/MM/dd'), $k.PSChildName)
    }
} catch { }

Write-Host ''
Write-Host '=== Display driver history ==='
if ($rows.Count -eq 0) {
    Write-Host 'Nothing found. Make sure PowerShell is running as Administrator.'
} else {
    $sorted = $rows | Sort-Object Vendor, FirstSeen
    Show-Table $sorted @('Vendor', 'ShortVer', 'Version', 'DriverDate', 'FirstSeen', 'Now', 'Source')
    if ($Csv) { $sorted | Export-Csv -LiteralPath $Csv -NoTypeInformation -Encoding UTF8; Write-Host "Saved: $Csv" }
}

Write-Host ''
Write-Host '=== Sources checked ==='
if ($fileReport.Count) { Show-Table $fileReport @('File', 'From', 'To', 'GpuEntries', 'Status') }
else { Write-Host 'setupapi logs : none found' }
Write-Host "Windows Update: $wuNote"
Write-Host "Event log     : $evNote"