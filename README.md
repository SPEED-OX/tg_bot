# Telegram Link Monitor Bot

## Features
- Monitors user chats for specific keywords (links)
- Forwards matching messages to your bot
- Add/remove chats and keywords via bot commands
- Persistent storage with SQLite

## Commands
/start - Start bot  
/stop - Stop monitoring  
/monitor - Start monitoring stored chats  
/monitor <chat_id> - Monitor a specific chat  
/clear <chat_id/keyword> - Remove a chat or keyword  
/link <keyword> - Add keyword  
/links - Show keywords  
/status - Show bot status  
/help - Show help

## Setup
1. Edit `config.py` with your API ID, API Hash, Bot Token, and Bot ID.
2. Install dependencies:
```bash
pip install -r requirements.txt