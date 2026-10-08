$appStartup = Join-Path ([Environment]::GetFolderPath('Startup')) 'Hourly Coach.lnk'
if (Test-Path -LiteralPath $appStartup) { Remove-Item -LiteralPath $appStartup }
Write-Output 'Hourly Coach startup disabled. Desktop shortcut and your data are preserved.'
