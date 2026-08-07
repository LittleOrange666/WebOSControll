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
headers = {
    "Authorization": "Bearer "+TOKEN,
    "Content-Type": "application/json",
}


async def ha_turn_on():
    url = HA_HOST+"/api/services/wake_on_lan/send_magic_packet"
    data = {
        "mac": MAC
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=data)
        return res.status_code, res.json()



async def ha_turn_off():
    url = HA_HOST+"/api/services/media_player/turn_off"
    data = {
        "entity_id": TV_ENTITY
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=data)
        return res.status_code, res.json()


async def ha_command(command: str, payload: dict | None = None):
    url = HA_HOST+"/api/services/webostv/command"
    data = {
        "entity_id": TV_ENTITY,
        "command": command
    }
    if payload is not None:
        data["payload"] = payload
    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=data)
        return res.status_code, res.json()


async def ha_button(button: str):
    url = HA_HOST+"/api/services/webostv/button"
    data = {
        "entity_id": TV_ENTITY,
        "button": button
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=data)
        return res.status_code, res.json()


async def ha_status():
    url = HA_HOST+"/api/states/"+TV_ENTITY
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        return res.status_code, res.json()

async def ha_ison():
    status, data = await ha_status()
    return data["state"] == "on"