import asyncio
import os

from aiowebostv import WebOsClient
from loguru import logger

def get_env(key) -> str:
    res = os.getenv(key)
    if res is None:
        print(f"Please set the {key} environment variable.")
        exit()
    return res

HOST = get_env("TV_IP")
KEY = get_env("TV_KEY")
YT_TARGET = get_env("YT_TARGET")
YT_APPID = "youtube.leanback.v4"


async def init() -> WebOsClient:
    logger.info("正在連線...")
    client = WebOsClient(HOST, KEY)
    await client.connect()
    logger.info("正在開螢幕...")
    await client.request('com.webos.service.tvpower/power/turnOnScreen')
    await client.send_message("開螢幕成功")
    return client

async def play(client: WebOsClient, volume: int):
    params = {
        "contentTarget": "https://www.youtube.com/watch?v="+YT_TARGET
    }
    logger.info("正在開啟 YouTube 影片...")
    await client.set_volume(volume)
    await asyncio.sleep(5)
    await client.launch_app_with_params(YT_APPID, params)

async def stop(client: WebOsClient):
    logger.info("正在關閉 YouTube 影片...")
    await client.button("HOME")

async def turn_off(client: WebOsClient):
    try:
        logger.info("正在關螢幕...")
        await client.request('com.webos.service.tvpower/power/turnOffScreen')
        await client.send_message("關螢幕成功")
    except Exception as ex:
        logger.error(ex)
    finally:
        await client.disconnect()


async def run_alarm(second: int, volume: int):
    logger.info("正在執行鬧鐘...")
    client = await init()
    try:
        await asyncio.sleep(5)
        await play(client, volume)
        await asyncio.sleep(second)
        await stop(client)
        await asyncio.sleep(5)
    except Exception as ex:
        logger.error(ex)
    finally:
        await turn_off(client)
    logger.info("鬧鐘執行完成")


async def test_alarm() -> bool:
    client = await init()
    try:
        await asyncio.sleep(5)
    except Exception as ex:
        logger.error(ex)
        return False
    finally:
        await turn_off(client)
    return True