# main_botid.py
import asyncio
import sqlite3
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser
import config

# Database setup (same tables / names as your main1.py)
conn = sqlite3.connect(config.DB_PATH)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS keywords (keyword TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS status (monitoring INTEGER)")
conn.commit()

# Ensure status row exists
cursor.execute("SELECT COUNT(*) FROM status")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO status VALUES (0)")
    conn.commit()

# Clients (same as main1 style)
user_client = TelegramClient(config.USER_SESSION, config.API_ID, config.API_HASH)
bot_client = TelegramClient(config.BOT_SESSION, config.API_ID, config.API_HASH)

# --- helpers (same logic as main1) ---
def add_keyword(keyword):
    cursor.execute("INSERT OR IGNORE INTO keywords VALUES (?)", (keyword,))
    conn.commit()

def remove_keyword(keyword):
    cursor.execute("DELETE FROM keywords WHERE keyword=?", (keyword,))
    conn.commit()

def get_keywords():
    cursor.execute("SELECT keyword FROM keywords")
    return [row[0] for row in cursor.fetchall()]

def add_chat(chat_id):
    cursor.execute("INSERT OR IGNORE INTO chats VALUES (?)", (chat_id,))
    conn.commit()

def remove_chat(chat_id):
    cursor.execute("DELETE FROM chats WHERE chat_id=?", (chat_id,))
    conn.commit()

def get_chats():
    cursor.execute("SELECT chat_id FROM chats")
    return [row[0] for row in cursor.fetchall()]

def set_monitoring(status: bool):
    cursor.execute("UPDATE status SET monitoring=?", (1 if status else 0,))
    conn.commit()

def is_monitoring():
    cursor.execute("SELECT monitoring FROM status")
    return cursor.fetchone()[0] == 1

# --- BOT COMMANDS (identical styling to main1) ---
@bot_client.on(events.NewMessage(pattern=r"^/start$"))
async def start_cmd(event):
    await event.reply("Bot started ✅\nUse /help for commands.")

@bot_client.on(events.NewMessage(pattern=r"^/stop$"))
async def stop_cmd(event):
    set_monitoring(False)
    await event.reply("Monitoring stopped ❌")

@bot_client.on(events.NewMessage(pattern=r"^/monitor$"))
async def monitor_start_cmd(event):
    set_monitoring(True)
    await event.reply("Monitoring started ✅")

@bot_client.on(events.NewMessage(pattern=r"^/monitor (-?\d+)$"))
async def monitor_add_chat_cmd(event):
    chat_id = int(event.pattern_match.group(1))
    add_chat(chat_id)
    await event.reply(f"Chat ID {chat_id} saved to database.")

@bot_client.on(events.NewMessage(pattern=r"^/clear (.+)$"))
async def clear_cmd(event):
    target = event.pattern_match.group(1).strip()
    if target.isdigit() or (target.startswith("-") and target[1:].isdigit()):
        remove_chat(int(target))
        await event.reply(f"Removed chat ID {target} from database.")
    else:
        remove_keyword(target)
        await event.reply(f"Removed keyword '{target}' from database.")

@bot_client.on(events.NewMessage(pattern=r"^/link (.+)$"))
async def link_cmd(event):
    keyword = event.pattern_match.group(1).strip()
    add_keyword(keyword)
    await event.reply(f"Keyword '{keyword}' added to database.")

@bot_client.on(events.NewMessage(pattern=r"^/links$"))
async def links_cmd(event):
    kws = get_keywords()
    await event.reply("**Keywords:**\n" + "\n".join(kws) if kws else "No keywords saved.")

@bot_client.on(events.NewMessage(pattern=r"^/status$"))
async def status_cmd(event):
    chats = get_chats()
    kws = get_keywords()
    status = "✅ Running" if is_monitoring() else "❌ Stopped"

    chat_lines = []
    for cid in chats:
        try:
            entity = await user_client.get_entity(cid)
            # preserve same display as main1.py
            chat_lines.append(f"{cid} — {entity.title}")
        except:
            chat_lines.append(f"{cid} — [Name Unavailable]")

    msg = f"**Monitoring:** {status}\n\n**Chats:**\n" + \
          ("\n".join(chat_lines) if chat_lines else "None") + \
          "\n\n**Keywords:**\n" + ("\n".join(kws) if kws else "None")
    await event.reply(msg)

@bot_client.on(events.NewMessage(pattern=r"^/help$"))
async def help_cmd(event):
    help_text = (
        "/start - Start bot\n"
        "/stop - Stop monitoring\n"
        "/monitor - Start monitoring\n"
        "/monitor <chat_id> - Save chat ID\n"
        "/clear <chat_id/keyword> - Remove chat or keyword\n"
        "/link <keyword> - Add keyword\n"
        "/links - Show keywords\n"
        "/status - Show status\n"
        "/help - Show this help"
    )
    await event.reply(help_text)

# --- USER MONITOR (only change: forwarding uses PeerUser(bot_id)) ---
@user_client.on(events.NewMessage)
async def monitor_messages(event):
    if not is_monitoring():
        return
    if event.chat_id in get_chats():
        text = (event.raw_text or "").lower()
        for kw in get_keywords():
            if kw.lower() in text:
                # <<-- replaced ChatAuditBot string with bot-id + PeerUser
                try:
                    bot_id = int(config.BOT_TOKEN.split(":")[0])
                    bot_entity = await user_client.get_entity(PeerUser(bot_id))
                    await user_client.forward_messages(bot_entity, event.message)
                except Exception as e:
                    # keep a simple print so logs show the forwarding error, same as earlier behavior
                    print(f"Forwarding error: {e}")
                break

# --- MAIN (use safe loop start if Termux/python3.12 had problems) ---
async def main():
    await user_client.start()
    # start bot with token exactly as before
    await bot_client.start(bot_token=config.BOT_TOKEN)
    print("Bot & user client running.")
    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )

if __name__ == "__main__":
    # Use event loop runner that avoids the Telethon asyncio loop problem on some Python versions
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())