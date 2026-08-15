import asyncio
import os

import httpx
from loguru import logger


def get_env(key) -> str:
    res = os.getenv(key)
    if res is None:
        print(f"Please set the {key} environment variable.")
        exit()
    return res

TIMEOUT = 30.0


MAC = get_env("TV_MAC")
TOKEN = get_env("HA_TOKEN")
HA_HOST = get_env("HA_HOST")
TV_ENTITY = get_env("TV_ENTITY")
GC_ENTITY = get_env("GC_ENTITY")
MEDIA_ID = get_env("MEDIA_ID")
YT_TARGET = get_env("YT_TARGET")
YT_APPID = "youtube.leanback.v4"
headers = {
    "Authorization": "Bearer " + TOKEN,
    "Content-Type": "application/json",
}


async def send_request(uri: str, payload: dict):
    logger.info(f"Sending request to {uri} with payload: {payload}")
    url = HA_HOST + uri
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        res = await client.post(url, headers=headers, json=payload)
        return res.status_code==200


async def get_info(uri: str):
    logger.info(f"Getting info from {uri}")
    url = HA_HOST + uri
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        res = await client.get(url, headers=headers)
        return res.json()


async def ha_turn_on():
    data = {
        "mac": MAC
    }
    return await send_request("/api/services/wake_on_lan/send_magic_packet", data)


async def ha_turn_off():
    data = {
        "entity_id": TV_ENTITY
    }
    return await send_request("/api/services/media_player/turn_off", data)


async def ha_command(command: str, payload: dict | None = None):
    data = {
        "entity_id": TV_ENTITY,
        "command": command
    }
    if payload is not None:
        data["payload"] = payload
    return await send_request("/api/services/webostv/command", data)


async def ha_button(button: str):
    data = {
        "entity_id": TV_ENTITY,
        "button": button
    }
    return await send_request("/api/services/webostv/button", data)


async def ha_status(entity):
    return await get_info("/api/states/" + entity)

async def ha_state(entity):
    data = await ha_status(entity)
    return data["state"]


async def ha_ison():
    data = await ha_status(TV_ENTITY)
    return data["state"] not in ("unavailable", "off")


async def wait(limit: int = 30):
    for _ in range(limit):
        if await ha_ison() and await ha_state(GC_ENTITY) != "unavailable":
            return True
        await asyncio.sleep(1)
    logger.warning("等待電視開啟超時，請檢查電視狀態。")
    return False


async def ha_play_fallback():
    logger.warning("Chromecast 異常，使用 YouTube App 播放影片作為 fallback。")
    data = {
        "id": YT_APPID,
        "params": {
            "contentTarget": "https://www.youtube.com/watch?v=" + YT_TARGET
        }
    }
    return await ha_command("system.launcher/launch", data)

async def ha_play():
    if await ha_state(GC_ENTITY) == "unavailable":
        await ha_play_fallback()
    data = {
        "entity_id": GC_ENTITY,
        "media_content_id": MEDIA_ID,
        "media_content_type": "video/mp4"
    }
    return await send_request("/api/services/media_player/play_media", data)