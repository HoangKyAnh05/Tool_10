$ErrorActionPreference = 'Stop'
$appRoot = $PSScriptRoot
$taskPython = (Get-Command python.exe -ErrorAction Stop).Source
if (-not (Test-Path -LiteralPath (Join-Path $appRoot '.venv\Scripts\python.exe'))) {
    & $taskPython -m venv --system-site-packages (Join-Path $appRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create Python environment.' }
}
$appPython = Join-Path $appRoot '.venv\Scripts\python.exe'
& $appPython -m pip install --disable-pip-version-check -r (Join-Path $appRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Cannot install dependencies.' }
$pythonWindowless = Join-Path $appRoot '.venv\Scripts\pythonw.exe'
$scriptPath = Join-Path $appRoot 'app.py'
$shell = New-Object -ComObject WScript.Shell
$desktopPath = [Environment]::GetFolderPath('Desktop')
$startupPath = [Environment]::GetFolderPath('Startup')
$desktopLink = $shell.CreateShortcut((Join-Path $desktopPath 'Hourly Coach.lnk'))
$desktopLink.TargetPath = $pythonWindowless
$desktopLink.Arguments = '"' + $scriptPath + '"'
$desktopLink.WorkingDirectory = $appRoot
$desktopLink.IconLocation = (Join-Path $appRoot 'assets\coach.ico') + ',0'
$desktopLink.Description = 'Hourly Coach - Antigravity Telegram learning companion'
$desktopLink.Save()
$startupLink = $shell.CreateShortcut((Join-Path $startupPath 'Hourly Coach.lnk'))
$startupLink.TargetPath = $pythonWindowless
$startupLink.Arguments = '"' + $scriptPath + '" --hidden'
$startupLink.WorkingDirectory = $appRoot
$startupLink.IconLocation = (Join-Path $appRoot 'assets\coach.ico') + ',0'
$startupLink.Description = 'Hourly Coach background startup'
$startupLink.Save()
Write-Output ('Desktop shortcut: ' + $desktopPath + '\Hourly Coach.lnk')
Write-Output ('Windows startup: ' + $startupPath + '\Hourly Coach.lnk')
