from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("=== Telegram Session String Generator ===")
api_id = int(input("Enter API_ID: "))
api_hash = input("Enter API_HASH: ")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\n✅ Login successful!")
    print("\nYour SESSION_STRING (copy this into Railway env variable):\n")
    print(client.session.save())
