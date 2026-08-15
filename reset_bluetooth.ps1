param (
    [string]$DeviceFriendlyName = "Realtek Bluetooth 5.3 Adapter" # 替換為你的藍牙裝置名稱 (支援萬用字元如 "*Bluetooth*")
)

# 1. 檢查 Windows 宿主機是否還看得到該藍牙裝置
$btDevice = Get-PnpDevice | Where-Object { $_.FriendlyName -like $DeviceFriendlyName -and $_.Present -eq $true }

if ($btDevice) {
    Write-Host "[*] 發現藍牙 Dongle 仍被 Windows 佔用 (Status: $($btDevice.Status))，準備重置..." -ForegroundColor Yellow

    # 停用裝置
    Disable-PnpDevice -InstanceId $btDevice.InstanceId -Confirm:$false
    Start-Sleep -Seconds 2

    # 啟用裝置 (啟用後 VirtualBox USB Filter 應會自動將其抓進 VM)
    Enable-PnpDevice -InstanceId $btDevice.InstanceId -Confirm:$false
    Write-Host "[+] 已執行啟用，等待 VirtualBox 捕獲..." -ForegroundColor Cyan

    Start-Sleep -Seconds 3

    # 再次檢查是否已從 Windows 消失 (正確直通給 VM)
    $checkAgain = Get-PnpDevice | Where-Object { $_.FriendlyName -like $DeviceFriendlyName -and $_.Present -eq $true }
    if (-not $checkAgain) {
        Write-Host "[+] 成功！藍牙裝置已從 Windows 消失，已正確掛載至 VirtualBox。" -ForegroundColor Green
    } else {
        Write-Host "[!] 裝置仍在 Windows 中，可能需要確認 VirtualBox USB 過濾器設定。" -ForegroundColor Red
    }
} else {
    Write-Host "[+] 藍牙裝置未在 Windows 裝置管理員中（狀態正確，已被 VirtualBox 接管）。" -ForegroundColor Green
}