# 📺 LG webOS TV Discord 鬧鐘與控制系統 (WebOSControl)

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![discord.py](https://img.shields.io/badge/discord.py-2.0+-5865F2.svg)](https://github.com/Rapptz/discord.py)

一個結合 **Discord Bot** 與 **Home Assistant / webOS API** 的智慧電視鬧鐘與遠端控制系統。專為 LG webOS 電視設計，支援定時喚醒電視、自動播放指定 YouTube 影片、控制音量，以及透過 Discord Slash Commands 輕鬆進行遠端管理。

---

## ✨ 主要特色 (Key Features)

- ⏰ **Discord 鬧鐘機器人**：透過斜線指令 (`/`) 靈活設定鬧鐘時間、啟用狀態、音量大小與響鈴持續時間。
- 📺 **自動化喚醒與播放**：響鈴時自動發送 Wake-on-LAN 封包喚醒電視，設定音量並自動開啟指定 YouTube 影片。
- 🏠 **Home Assistant 整合**：透過 HA REST API 達成高穩定度的媒體播放器狀態監控與指令發送。
- 🐳 **容器化部署 (Docker & Docker Compose)**：預先配置 Dockerfile 與 `docker-compose.yml`，適合部署於 NAS、樹莓派或雲端伺服器。
- 🛠️ **獨立 webOS 腳本**：內建配對金鑰擷取 (`get_key.py`)、應用程式清單查詢 (`list.py`)、直接關閉 (`close.py`) 與視窗自動投射等實用腳本。

---

## 📁 專案結構 (Project Structure)

```text
WebOSControll/
├── bot.py                # Discord 鬧鐘機器人主程式
├── main.py               # 獨立定時播放與投射測試腳本
├── get_key.py            # LG webOS TV 第一次連線與金鑰 (Client Key) 獲取腳本
├── list.py               # 查詢電視上已安裝應用程式 ID 的腳本
├── close.py              # 手動關閉電視應用程式與螢幕的腳本
├── modules/
│   ├── tools.py          # 鬧鐘執行邏輯與流程控制
│   └── utils.py          # Home Assistant REST API 呼叫與環境變數處理
├── data/
│   └── config.yml        # 鬧鐘動態設定持久化儲存檔案
├── Dockerfile            # Docker 映像檔建置檔
├── docker-compose.yml    # Docker Compose 部署設定檔
├── requirements.txt      # Python 相依套件清單
└── .env                  # 環境變數設定檔 (需自行建立)
```

---

## ⚙️ 環境變數設定 (Environment Variables)

請在專案根目錄建立 `.env` 檔案，填入以下必要資訊：

```ini
# Discord Bot 設定
DC_TOKEN=your_discord_bot_token

# Home Assistant 設定
HA_HOST=http://your-homeassistant-ip:8123
HA_TOKEN=your_long_lived_access_token
TV_ENTITY=media_player.lg_webos_tv

# 電視與媒體設定
TV_MAC=AA:BB:CC:DD:EE:FF
YT_TARGET=voNEI6sN9DQ

# 直連模式設定 (適用於 main.py / get_key.py / list.py)
TV_IP=192.168.x.x
TV_KEY=your_webos_client_key
TV_NAME=LG_TV_Name
```

### 變數說明：
| 變數名稱 | 說明 | 範例 / 備註 |
| :--- | :--- | :--- |
| `DC_TOKEN` | Discord Bot 的 Token | 自 Discord Developer Portal 取得 |
| `HA_HOST` | Home Assistant 伺服器位址 | `http://192.168.1.100:8123` |
| `HA_TOKEN` | Home Assistant 長期存取權杖 (Long-Lived Access Token) | 在 HA 個人設定頁面建立 |
| `TV_ENTITY` | 電視在 Home Assistant 中顯示的 Entity ID | `media_player.lg_webos_tv` |
| `TV_MAC` | 電視的 MAC 位址 | 用於 Wake-on-LAN 開機 |
| `YT_TARGET` | 響鈴時欲播放的 YouTube 影片 ID | 例如影片網址 `watch?v=XXXX` 中的 `XXXX` |
| `TV_IP` | 電視的區域網路 IP 位址 | 直連模式使用 |
| `TV_KEY` | webOS 配對 Key | 可透過 `python get_key.py` 取得 |

---

## 🚀 快速開始 (Quick Start)

### 方法一：使用 Docker Compose 部署 (推薦)

1. 確保已安裝 Docker 與 Docker Compose。
2. 建立並配置 `.env` 檔案。
3. 啟動服務：
   ```bash
   docker-compose up -d
   ```

### 方法二：本地 Python 環境安裝與執行

1. **複製專案並安裝相依套件**：
   ```bash
   pip install -r requirements.txt
   ```
2. **配置 `.env` 檔案**。
3. **啟動 Discord 機器人**：
   ```bash
   python bot.py
   ```

---

## 🤖 Discord 斜線指令 (Slash Commands)

機器人啟動後，可在 Discord 頻道中輸入以下指令：

| 指令 | 說明 | 範例 |
| :--- | :--- | :--- |
| `/set_alarm <HH:MM>` | 設定每日響鈴時間 (24小時制) | `/set_alarm time_str: 07:30` |
| `/switch <status>` | 開啟或關閉鬧鐘功能 | `/switch status: ON` |
| `/stat` | 顯示目前鬧鐘時間、開關狀態、音量及剩餘倒數時間 | `/stat` |
| `/set_volume <0-100>` | 設定鬧鐘響鈴時的電視音量 | `/set_volume volume: 20` |
| `/set_duration <秒數>` | 設定鬧鐘響鈴持續時間 | `/set_duration seconds: 60` |
| `/trigger [秒數] [音量]` | 立即觸發鬧鐘響鈴（測試用途） | `/trigger seconds: 30 volume: 15` |
| `/wake` | 發送 Wake-on-LAN 嘗試喚醒電視 | `/wake` |
| `/check` | 檢查電視目前是否為開機狀態 | `/check` |
| `/button <按鈕>` | 發送遙控器按鈕指令至電視 | `/button button: HOME` |
| `/command <指令> [payload]` | 發送原生 WebOS API 指令至電視 | `/command command: system/turnOff` |

---

## 🛠️ 輔助腳本使用說明 (Helper Scripts)

### 1. 獲取 webOS Client Key (`get_key.py`)
當初次直連電視時，可執行此腳本在電視螢幕上彈出授權對話框，並自動將 key 存入 `.env`：
```bash
python get_key.py
```

### 2. 查詢電視已安裝 APP ID (`list.py`)
連線至電視並印出所有已安裝應用程式名稱與其 App ID：
```bash
python list.py
```

### 3. 測試關閉應用程式與螢幕 (`close.py`)
手動發送返家指令並關閉電視螢幕：
```bash
python close.py
```
