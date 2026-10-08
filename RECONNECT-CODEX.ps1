param([Parameter(Mandatory=$true)][int]$AppPid)
$ErrorActionPreference = 'Stop'
$appPath = Join-Path $PSScriptRoot 'app.py'
$ownedApp = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $AppPid)
if (-not $ownedApp) { exit 0 }
if ($ownedApp.CommandLine -notmatch [regex]::Escape($appPath)) {
    throw 'Process is not this Hourly Coach installation. No process was stopped.'
}
foreach ($child in @(Get-CimInstance Win32_Process -Filter ('ParentProcessId=' + $AppPid))) {
    if ($child.CommandLine -match 'codex.+app-server') {
        Stop-Process -Id $child.ProcessId -Force
    }
}
Stop-Process -Id $AppPid -Force
