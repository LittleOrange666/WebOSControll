import os

import httpx


def get_env(key) -> str:
    res = os.getenv(key)
    if res is None:
        print(f"Please set the {key} environment variable.")
        exit()
    return res


MAC = get_env("TV_MAC")
TOKEN = get_env("HA_TOKEN")
HA_HOST = get_env("HA_HOST")
TV_ENTITY = get_env("TV_ENTITY")
GC_ENTITY = get_env("GC_ENTITY")
MEDIA_ID = get_env("MEDIA_ID")
headers = {
    "Authorization": "Bearer " + TOKEN,
    "Content-Type": "application/json",
}


async def send_request(uri: str, payload: dict):
    url = HA_HOST + uri
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(url, headers=headers, json=payload)
        return res.status_code, res.json()


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


async def ha_status():
    url = HA_HOST + "/api/states/" + TV_ENTITY
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        return res.status_code, res.json()


async def ha_ison():
    status, data = await ha_status()
    return data["state"] == "on"


async def ha_play():
    data = {
        "entity_id": GC_ENTITY,
        "media_content_id": MEDIA_ID,
        "media_content_type": "video/mp4"
    }
    return await send_request("/api/services/media_player/play_media", data)