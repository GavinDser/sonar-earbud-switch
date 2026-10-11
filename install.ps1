# 安装：建虚拟环境 -> 自动检测并生成配置 -> 加开机自启 -> 启动
#   powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$venv = Join-Path $root '.venv'
$lnk = Join-Path ([Environment]::GetFolderPath('Startup')) 'sonar-earbud-switch.lnk'

function Find-Python {
    # 返回 Python 3.11+ 解释器的完整路径
    foreach ($cmd in @(@('py', '-3'), @('python'))) {
        try {
            $exe = $cmd[0]; $rest = @($cmd | Select-Object -Skip 1)
            $p = & $exe @rest -c 'import sys; print(sys.executable if sys.version_info >= (3, 11) else "")' 2>$null
            if ($p) { return $p }
        } catch {}
    }
    throw '需要 Python 3.11 或更新版本：https://www.python.org/downloads/ （安装时勾选 Add to PATH 和 tcl/tk）'
}

Write-Host '[1/4] 准备 Python 环境'
if (-not (Test-Path "$venv\Scripts\python.exe")) {
    & (Find-Python) -m venv $venv
}
& "$venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r (Join-Path $root 'requirements.txt')

Write-Host '[2/4] 停掉正在运行的旧实例'
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" |
    Where-Object CommandLine -match 'sonar_earbud_switch' |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Write-Host '[3/4] 自动检测并生成配置'
Push-Location $root
try {
    & "$venv\Scripts\python.exe" -m sonar_earbud_switch setup
    if ($LASTEXITCODE -ne 0) { throw '配置失败，按上面的提示处理后重新运行 install.ps1' }
} finally { Pop-Location }

Write-Host '[4/4] 加入开机自启并启动'
$w = New-Object -ComObject WScript.Shell
$s = $w.CreateShortcut($lnk)
$s.TargetPath = "$venv\Scripts\pythonw.exe"
$s.Arguments = '-m sonar_earbud_switch'
$s.WorkingDirectory = $root
$s.Save()
Start-Process "$venv\Scripts\pythonw.exe" -ArgumentList '-m sonar_earbud_switch' -WorkingDirectory $root

Write-Host "完成。日志：$(Join-Path $root 'switch.log')"
