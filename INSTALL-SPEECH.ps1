$ErrorActionPreference = 'Stop'
$appRoot = $PSScriptRoot
$speechEnv = Join-Path $appRoot '.speech-venv'
$runtimePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) { $runtimePython = (Get-Command python.exe).Source }
& $runtimePython -m venv $speechEnv
if ($LASTEXITCODE -ne 0) { throw 'Cannot create speech environment.' }
$speechPython = Join-Path $speechEnv 'Scripts\python.exe'
& $speechPython -m pip install --disable-pip-version-check faster-whisper==1.2.1 av==15.1.0
if ($LASTEXITCODE -ne 0) { throw 'Cannot install faster-whisper.' }
$appPython = Join-Path $appRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $appPython)) { $appPython = (Get-Command python.exe).Source }
Push-Location $appRoot
try {
    & $appPython (Join-Path $appRoot 'coach\configure_speech.py') $speechPython
    if ($LASTEXITCODE -ne 0) { throw 'Speech installed, but could not update app configuration.' }
}
finally { Pop-Location }
Write-Output 'Speech recognition installed. The first audio submission downloads the base model locally.'
