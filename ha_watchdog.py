import os.path
import subprocess
import time
from os import getenv

import requests
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook

load_dotenv()

# === 參數設定 ===
VM_NAME = "Home Assistant"  # VirtualBox 中的虛擬機名稱
HA_URL = getenv("HA_HOST","http://192.168.1.100:8123")  # HA 的 IP/網址與 Port (請替換)
HA_TOKEN = getenv("HA_TOKEN","YOUR_LONG_LIVED_ACCESS_TOKEN")  # 長效存取權杖 (選填，/api/ 請求需驗證)

WEBHOOK_URL = getenv("DC_WEBHOOK","YOUR_DISCORD_WEBHOOK_URL")  # Discord Webhook URL

# 檢測與重試參數
CHECK_INTERVAL = 30  # 每 30 秒檢測一次
MAX_FAILURES = 3  # 連續失敗幾次後判定為下線
TIMEOUT = 5  # HTTP 請求超時時間 (秒)

# 若 VBoxManage 未加入系統 PATH，請填寫完整路徑：
# Windows 預設: r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
# Linux 預設: "VBoxManage"
VBOX_MANAGE = "VBoxManage"

BT_DEVICE_NAME = "Realtek Bluetooth 5.3 Adapter"


def print_log(content: str):
    full = "\n".join(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {line}" for line in content.split("\n"))
    print(full)
    try:
        webhook = DiscordWebhook(url=WEBHOOK_URL, content=full)
        webhook.execute()
    except:
        print("[!] 無法發送 Discord Webhook，請檢查 WEBHOOK_URL 是否正確。")

def fix_bluetooth_passthrough():
    """透過 PowerShell 重置 Windows 藍牙裝置，讓 VirtualBox 重新捕獲"""
    ps_script = os.path.join(os.path.dirname(__file__), "reset_bluetooth.ps1")
    try:
        out = subprocess.run(
            ["powershell", ps_script],
            capture_output=True,
            check=True,
            text=True
        ).stdout
        print_log(out+"\n"+"[+] 藍牙 Dongle 已觸發重置。")
    except subprocess.SubprocessError as e:
        print_log(f"[-] 藍牙重置失敗: {e}")


def is_ha_api_alive() -> bool:
    """檢查 Home Assistant API 服務是否正常響應"""
    headers = {}
    if HA_TOKEN and HA_TOKEN != "YOUR_LONG_LIVED_ACCESS_TOKEN":
        headers["Authorization"] = f"Bearer {HA_TOKEN}"

    try:
        # /api/ 通常返回 200 或 401 (若沒 token)，只要有 HTTP 響應即代表服務在線
        resp = requests.get(f"{HA_URL}/api/", headers=headers, timeout=TIMEOUT)
        return resp.status_code in [200, 401]
    except requests.exceptions.RequestException:
        return False


def get_vm_state(vm_name: str) -> str:
    """透過 VBoxManage 取得 VM 狀態 (running, poweroff, aborted 等)"""
    try:
        res = subprocess.run(
            [VBOX_MANAGE, "showvminfo", vm_name, "--machinereadable"],
            capture_output=True,
            text=True,
            check=True
        )
        for line in res.stdout.splitlines():
            if line.startswith('VMState='):
                return line.split('=')[1].strip('"')
    except subprocess.SubprocessError as e:
        print_log(f"[Error] 無法取得 VM 狀態: {e}")
    return "unknown"


def start_vm_headless(vm_name: str):
    """無介面後台啟動 VM"""
    print_log(f"[*] 嘗試啟動虛擬機: {vm_name} (headless 模式)...")
    try:
        subprocess.run(
            [VBOX_MANAGE, "startvm", vm_name, "--type", "headless"],
            check=True
        )
        print_log("[+] 虛擬機啟動指令已送出。")
    except subprocess.SubprocessError as e:
        print_log(f"[-] 啟動失敗: {e}")


def force_restart_vm(vm_name: str):
    """若狀態為 running 但 HA 卡死，強制重啟 VM"""
    print_log(f"[!] 虛擬機卡死，執行強制重啟: {vm_name}...")
    try:
        subprocess.run([VBOX_MANAGE, "controlvm", vm_name, "reset"], check=True)
    except subprocess.SubprocessError as e:
        print_log(f"[-] 強制重啟失敗: {e}")


def main():
    print_log(f"=== HA Watchdog 啟動 (監控 VM: {VM_NAME}) ===")
    consecutive_failures = 0

    while True:
        if is_ha_api_alive():
            if consecutive_failures > 0:
                print_log("[+] Home Assistant 服務已恢復正常。")
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            print_log(f"[-] HA 無回應 (失敗次數: {consecutive_failures}/{MAX_FAILURES})")

            if consecutive_failures >= MAX_FAILURES:
                vm_state = get_vm_state(VM_NAME)
                print_log(f"[!] 達到失敗上限，當前 VM 狀態: {vm_state}")

                if vm_state in ["poweroff", "aborted", "saved"]:
                    start_vm_headless(VM_NAME)
                elif vm_state == "running":
                    force_restart_vm(VM_NAME)
                else:
                    print_log(f"[?] 未知或異常狀態 ({vm_state})，嘗試直接啟動...")
                    start_vm_headless(VM_NAME)

                # 重啟後預留 60 秒開機等待時間，避免連續誤判觸發
                print_log("[*] 等待 60 秒開機冷卻期...")
                time.sleep(60)
                fix_bluetooth_passthrough()
                consecutive_failures = 0

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()