param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "status", "install", "uninstall")]
    [string]$Action = "status"
)
# ======================== 參數設定 ========================
$TaskName   = "HA_Watchdog"
$PythonPath = (Get-Command pythonw).Source                         # 使用 pythonw.exe 避免彈出黑色命令視窗
$ScriptPath = "$PSScriptRoot\ha_watchdog.py"            # 你的 watchdog 腳本絕對路徑
$WorkDir    = [System.IO.Path]::GetDirectoryName($ScriptPath)
# ==========================================================

$ThisName = $MyInvocation.MyCommand.Name

# ===== 自動檢查並提升管理員權限 (放置在 ha-service.ps1 最開頭) =====
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[*] 正在請求系統管理員權限以操作工作排程器..." -ForegroundColor Cyan
    $argsList = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" $Action"
    Start-Process powershell.exe -Verb RunAs -ArgumentList $argsList
    exit
}
# ================================================================

function Get-WatchdogProcess {
    return Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -like "*ha_watchdog.py*"
    }
}

function Ensure-TaskInstalled {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "[*] 排程工作 '$TaskName' 尚未安裝，正在自動建立..." -ForegroundColor Cyan
        Install-Task
    }
}

function Install-Task {
    $action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`"" -WorkingDirectory $WorkDir
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0 -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

    # 加入 -User $env:USERNAME
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -User $env:USERNAME -Description "Home Assistant VirtualBox Watchdog Service" -Force | Out-Null
    Write-Host "[+] 已成功註冊工作排程器工作: $TaskName" -ForegroundColor Green
}

function Uninstall-Task {
    Stop-Task
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[+] 已刪除排程工作: $TaskName" -ForegroundColor Green
    } else {
        Write-Host "[-] 排程工作不存在。" -ForegroundColor Yellow
    }
}

function Start-TaskProcess {
    Ensure-TaskInstalled
    $procs = Get-WatchdogProcess
    if ($procs) {
        Write-Host "[!] Watchdog 已在運行中 (PID: $($procs.ProcessId -join ', '))，略過啟動。" -ForegroundColor Yellow
        return
    }

    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 1

    $procs = Get-WatchdogProcess
    if ($procs) {
        Write-Host "[+] Watchdog 啟動成功 (PID: $($procs.ProcessId -join ', '))" -ForegroundColor Green
    } else {
        Write-Host "[!] 已觸發工作排程，若未見行程請確認 Python 路徑與權限。" -ForegroundColor Yellow
    }
}

function Stop-Task {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task -and $task.State -eq "Running") {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    }

    $procs = Get-WatchdogProcess
    if ($procs) {
        $procs | ForEach-Object {
            Stop-Process -Id $_.ProcessId -Force
            Write-Host "[+] 已強制終止行程 (PID: $($_.ProcessId))" -ForegroundColor Green
        }
    } else {
        Write-Host "[-] 目前沒有正在運行的 Watchdog 行程。" -ForegroundColor Yellow
    }
}

function Get-TaskStatus {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    $procs = Get-WatchdogProcess

    Write-Host "================= HA Watchdog 狀態 =================" -ForegroundColor Cyan
    if ($task) {
        Write-Host "工作排程狀態 : $($task.State)" -ForegroundColor Gray
    } else {
        Write-Host "工作排程狀態 : 未安裝 (輸入 .\$ThisName install 可手動安裝)" -ForegroundColor DarkYellow
    }

    if ($procs) {
        Write-Host "行程運行狀態 : 運行中 (Running)" -ForegroundColor Green
        foreach ($p in $procs) {
            Write-Host "  - PID: $($p.ProcessId) | 啟動指令: $($p.CommandLine)" -ForegroundColor DarkGreen
        }
    } else {
        Write-Host "行程運行狀態 : 未運行 (Stopped)" -ForegroundColor Red
    }
    Write-Host "=====================================================" -ForegroundColor Cyan
}

# ======================== 流程分流 ========================
switch ($Action) {
    "start" {
        Start-TaskProcess
    }
    "stop" {
        Stop-Task
    }
    "restart" {
        Write-Host "[*] 正在重啟 Watchdog..." -ForegroundColor Cyan
        Stop-Task
        Start-Sleep -Seconds 1
        Start-TaskProcess
    }
    "status" {
        Get-TaskStatus
    }
    "install" {
        Install-Task
    }
    "uninstall" {
        Uninstall-Task
    }
}
Pause