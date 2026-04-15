import asyncio
import os

from aiowebostv import WebOsClient
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("TV_IP", "PLACEHOLDER")
if HOST == "PLACEHOLDER":
    print("Please set the TV_IP environment variable in a .env file.")
    exit()
KEY = os.getenv("TV_KEY", "PLACEHOLDER")
if KEY == "PLACEHOLDER":
    print("Please set the TV_KEY environment variable in a .env file.")
    exit()
async def main():
    client = WebOsClient(HOST, KEY)
    await client.connect()
    await asyncio.sleep(5)
    await client.button("HOME")
    await asyncio.sleep(5)
    await client.request('com.webos.service.tvpower/power/turnOffScreen')
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())