# 卸载：停止运行并移除开机自启（不删除本文件夹）
#   powershell -ExecutionPolicy Bypass -File uninstall.ps1
$lnk = Join-Path ([Environment]::GetFolderPath('Startup')) 'sonar-earbud-switch.lnk'

Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" |
    Where-Object CommandLine -match 'sonar_earbud_switch' |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

if (Test-Path $lnk) { Remove-Item $lnk }
Write-Host '已停止并移除开机自启。不再需要的话可以直接删除本文件夹。'
