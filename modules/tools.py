import asyncio

from loguru import logger

from .utils import get_env, ha_turn_on, ha_turn_off, ha_ison, ha_command, ha_button, ha_play

MAC = get_env("TV_MAC")

async def init():
    on = await ha_ison()
    if not on:
        logger.info("電視目前為關閉狀態，嘗試喚醒...")
        await ha_turn_on()
        await asyncio.sleep(5)

async def play(volume: int):
    logger.info("正在開啟 YouTube 影片...")
    await ha_command("audio/setVolume", {"volume": volume})
    await asyncio.sleep(5)
    await ha_play()

async def stop():
    logger.info("正在關閉 YouTube 影片...")
    await ha_button("HOME")

async def turn_off():
    try:
        logger.info("正在關機...")
        await ha_turn_off()
    except Exception:
        logger.exception("出現錯誤")


async def wake_up():
    logger.info("正在喚醒...")
    await ha_turn_on()
    await asyncio.sleep(5)
    if await ha_ison():
        logger.info("喚醒成功")
        return True
    logger.error("喚醒失敗")
    return False


async def run_alarm(second: int, volume: int) -> bool:
    logger.info("正在執行鬧鐘...")
    try:
        await init()
        await asyncio.sleep(5)
        await play(volume)
        await asyncio.sleep(second)
        await stop()
        await asyncio.sleep(5)
    except Exception:
        logger.exception("出現錯誤")
        return False
    finally:
        await turn_off()
    logger.info("鬧鐘執行完成")
    return True


async def test_alarm() -> bool:
    if await ha_ison():
        logger.info("目前為開啟狀態")
        return True
    logger.info("目前為關閉狀態")
    return False