import asyncio
import os

from aiowebostv import WebOsClient
from dotenv import load_dotenv, dotenv_values

load_dotenv()

HOST = os.getenv("TV_IP", "PLACEHOLDER")
if HOST == "PLACEHOLDER":
    print("Please set the TV_IP environment variable in a .env file.")
    exit()


async def main():
    print(f"Connecting to TV at {HOST}...")
    client = WebOsClient(HOST)
    await client.connect()

    # Store this key for future use
    print(f"Client key: {client.client_key}")

    env_values = dotenv_values(".env")
    env_values["TV_KEY"] = client.client_key
    with open(".env", "w") as f:
        for k, v in env_values.items():
            f.write(f"{k}={v}\n")

    # pprint(client.tv_info)
    # pprint(client.tv_state)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())