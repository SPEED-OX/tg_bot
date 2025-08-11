import sqlite3
from telethon import TelegramClient, events
import config

# --- Database Setup ---
conn = sqlite3.connect(config.DB_PATH)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS keywords (keyword TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER)")
conn.commit()

# --- Clients ---
user_client = TelegramClient(config.USER_SESSION, config.API_ID, config.API_HASH)
bot_client = TelegramClient(config.BOT_SESSION, config.API_ID, config.API_HASH).start(bot_token=config.BOT_TOKEN)

# --- Load keywords from DB ---
def get_keywords():
    cursor.execute("SELECT keyword FROM keywords")
    return [row[0] for row in cursor.fetchall()]

# --- Bot Commands ---
@bot_client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    await event.reply("Bot started. Use /help for commands.")

@bot_client.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    help_text = (
        "/monitor - Start monitoring\n"
        "/stop - Stop monitoring\n"
        "/link <keyword> - Add a keyword to monitor\n"
        "/links - Show current keywords"
    )
    await event.reply(help_text)

@bot_client.on(events.NewMessage(pattern=r"/link (.+)"))
async def add_link_handler(event):
    keyword = event.pattern_match.group(1).strip()
    cursor.execute("INSERT INTO keywords VALUES (?)", (keyword,))
    conn.commit()
    await event.reply(f"Keyword '{keyword}' added.")

@bot_client.on(events.NewMessage(pattern="/links"))
async def show_links_handler(event):
    kws = get_keywords()
    if not kws:
        await event.reply("No keywords found.")
    else:
        await event.reply("\n".join(kws))

# --- User Client Monitoring ---
@user_client.on(events.NewMessage)
async def monitor_handler(event):
    kws = get_keywords()
    text = event.raw_text.lower()
    if any(kw.lower() in text for kw in kws):
        await bot_client.send_message("me", event.message)

# --- Start ---
async def main():
    await user_client.start()
    await bot_client.start()
    print("Monitoring started...")
    await user_client.run_until_disconnected()

import asyncio
asyncio.run(main())
