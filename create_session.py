from telethon import TelegramClient
import config

client = TelegramClient(config.USER_SESSION, config.API_ID, config.API_HASH)

async def main():
    await client.start()
    print("Session created successfully! You can now upload the .session file to Railway.")

client.loop.run_until_complete(main())
