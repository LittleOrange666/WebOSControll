import asyncio
import datetime
import os
import subprocess
import time
from math import ceil

from pywinauto import Application

import pyautogui
from aiowebostv import WebOsClient
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

YT_APPID = "youtube.leanback.v4"
YT_TARGET = "voNEI6sN9DQ"
TARGET_VOLUME = 16
TARGET_TIME = (17,59)
STEP = 10

HOST = os.getenv("TV_IP", "PLACEHOLDER")
if HOST == "PLACEHOLDER":
    print("Please set the TV_IP environment variable in a .env file.")
    exit()
KEY = os.getenv("TV_KEY", "PLACEHOLDER")
if KEY == "PLACEHOLDER":
    print("Please set the TV_KEY environment variable in a .env file.")
    exit()
NAME = os.getenv("TV_NAME", "PLACEHOLDER")
if NAME == "PLACEHOLDER":
    print("Please set the TV_NAME environment variable in a .env file.")
    exit()

def casting_connect():
    pyautogui.hotkey('win', 'k')
    time.sleep(2)

    try:
        app = Application(backend="uia").connect(title="快速設定", timeout=5)
        window = app.window(title="快速設定")

        target = window.child_window(title=NAME, control_type="ListItem")
        if target.exists():
            target.click_input()
            print(f"已點擊 {NAME} 開始連線")
        else:
            print("找不到該設備按鈕")
    except Exception as e:
        print(f"自動化失敗: {e}")

def casting_disconnect():
    try:
        subprocess.run(["displayswitch.exe", "/internal"], check=True)
        print("螢幕模式已切換回「僅電腦螢幕」，投射已中斷。")
    except Exception as e:
        print(f"中斷失敗: {e}")


async def start(client):
    print("正在開螢幕...")
    await client.request('com.webos.service.tvpower/power/turnOnScreen')
    await client.send_message("開螢幕成功")

async def play(client):
    params = {
        "contentTarget": "https://www.youtube.com/watch?v="+YT_TARGET
    }
    print("正在開啟 YouTube 影片...")
    await client.set_volume(TARGET_VOLUME)
    await asyncio.sleep(5)
    await client.launch_app_with_params(YT_APPID, params)

async def stop(client):
    print("正在關閉 YouTube 影片...")
    await client.button("HOME")

async def end(client):
    print("正在關螢幕...")
    await client.request('com.webos.service.tvpower/power/turnOffScreen')
    await client.send_message("關螢幕成功")

async def wait_time():
    target = datetime.time(*TARGET_TIME)
    target_time = datetime.datetime.now()
    if target < target_time.time():
        target_time += datetime.timedelta(days=1)
    target_time = target_time.replace(hour=target.hour, minute=target.minute, second=0,microsecond=0)
    print(f"等待到 {target_time} ...")
    last = (target_time - datetime.datetime.now()).total_seconds()
    print(f"現在時間: {datetime.datetime.now()}，距離目標時間還有 {last} 秒")
    prev = ceil(last/STEP)
    pbar = tqdm(total=prev, desc="等待中")
    with pbar:
        while datetime.datetime.now() < target_time:
            await asyncio.sleep(STEP)
            cur = ceil((target_time - datetime.datetime.now()).total_seconds()/STEP)
            pbar.update(prev-cur)


async def main():
    # await asyncio.sleep(10)
    await wait_time()
    print(f"Connecting to TV at {HOST}...")
    client = WebOsClient(HOST, KEY)
    await client.connect()
    await start(client)
    await asyncio.sleep(10)
    await play(client)
    await asyncio.sleep(120)
    await stop(client)
    await asyncio.sleep(5)
    await end(client)
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
