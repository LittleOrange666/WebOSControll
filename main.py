import asyncio

from dotenv import load_dotenv

load_dotenv()


async def main():
    from modules import utils
    #await utils.send_request("/api/services/homeassistant/restart",{})
    print(await utils.get_info("/api/states/media_player.lg_webos_tv"))

if __name__ == "__main__":
    asyncio.run(main())
