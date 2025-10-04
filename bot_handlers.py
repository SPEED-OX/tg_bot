"""
Main bot handlers for Controller Bot
Handles commands and message processing
"""
import telebot
from telebot.types import BotCommand
import logging
import re
from typing import Dict, Optional
from datetime import datetime
from database.models import DatabaseManager
from handlers.menu_handlers import MenuHandler
from utils.scheduler import SmartScheduler
from utils.time_parser import parse_time_input, TIME_FORMAT_HELP
from config import BOT_OWNER_ID, IST

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, bot: telebot.TeleBot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.menu_handler = MenuHandler(bot, db)
        self.scheduler = SmartScheduler(bot, db)

        # Register all handlers
        self.register_handlers()
        self.setup_commands()

    def setup_commands(self):
        """Set up bot commands menu"""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help message"),
            BotCommand("addchannel", "Add a channel to manage"),
            BotCommand("channels", "View your channels"),
        ]

        try:
            self.bot.set_my_commands(commands)
            logger.info("✅ Bot commands set successfully")
        except Exception as e:
            logger.error(f"❌ Failed to set bot commands: {e}")

    def register_handlers(self):
        """Register all message and callback handlers"""

        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            self.handle_start(message)

        @self.bot.message_handler(commands=['help'])
        def help_command(message):
            self.handle_help(message)

        @self.bot.message_handler(commands=['addchannel'])
        def addchannel_command(message):
            self.handle_addchannel(message)

        @self.bot.message_handler(commands=['channels'])
        def channels_command(message):
            self.handle_channels(message)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            self.menu_handler.handle_callback_query(call)

        @self.bot.message_handler(content_types=['text', 'photo', 'video', 'document'])
        def handle_messages(message):
            self.handle_user_message(message)

    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        return user_id == BOT_OWNER_ID or self.db.is_user_whitelisted(user_id)

    def handle_start(self, message):
        """Handle /start command"""
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name

        # Add user to database
        self.db.add_user(user_id, username, first_name)

        # Show main menu
        self.menu_handler.show_main_menu(message.chat.id, user_id)

    def handle_help(self, message):
        """Handle /help command - universal help"""
        help_text = f"""
🤖 **Controller Bot - Complete Guide**

**🚀 Quick Start:**
1. Add me as admin to your channel
2. Use /addchannel @yourchannel  
3. Use main menu to create posts

**📋 Commands:**
• /start - Open main menu
• /help - Show this help
• /addchannel @channel - Add channel
• /channels - View your channels

**🎛️ Main Menu Features:**

**🏠 Start** - Welcome and getting started info

**👥 User Management** (Owner only)
├── Users - List whitelisted users
├── Permit <user_id> - Add user (ignores - signs)
├── Remove <user_id> - Remove user (ignores - signs)
└── Back - Return to main menu

**📝 New Post**
├── Select Channel - Choose from your added channels
└── Post Editor:
    ├── Send
    │   ├── Schedule Post - Format: dd/mm hh:mm or hh:mm
    │   ├── Self-Destruct - Auto-delete timer
    │   ├── Post Now - Send immediately  
    │   └── Back
    ├── Cancel - Cancel current post
    ├── Preview - Show post preview
    ├── Delete All - Clear current post
    └── Back

**📅 Schedules**
├── Scheduled Posts - View upcoming posts
├── Self-Destruct Timings - View auto-delete tasks
├── Cancel
│   ├── Cancel Self-Destruct - Stop auto-delete
│   ├── Cancel Scheduled Post - Remove scheduled post
│   └── Back
└── Back

**📊 Dashboard** - Web interface for advanced management

**⏰ Time Format Examples:**
• `5/10 15:00` - October 5th at 3:00 PM
• `15:00` - Today/tomorrow at 3:00 PM
• All times in IST (Indian Standard Time)

**📝 Post Formatting:**
• **Bold**: **text** or __text__
• *Italic*: *text* or _text_
• `Code`: `text` or ```code block```
• Links: [text](https://url.com)
• Buttons: `Button Text | https://url.com` (one per line)

**🔧 Channel Setup:**
1. Add bot to channel as admin
2. Give permissions: Post, Edit, Delete messages
3. Use /addchannel @channelname
4. Start creating posts!

**💡 Pro Tips:**
• Use web dashboard for bulk operations
• Schedule posts during off-peak hours
• Set self-destruct for temporary announcements
• Preview posts before sending

**🛠️ Troubleshooting:**
• Bot not posting? Check admin permissions
• Can't add channel? Ensure bot is admin first
• Time issues? Use IST format (dd/mm hh:mm)

Need more help? Use the main menu buttons! 🎯

**Current User:** {message.from_user.first_name or 'Unknown'}
**Status:** {'✅ Authorized' if self.is_authorized(user_id) else '❌ Not Authorized'}
        """

        self.bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

    def handle_addchannel(self, message):
        """Handle /addchannel command"""
        user_id = message.from_user.id

        if not self.is_authorized(user_id):
            self.bot.reply_to(message, "❌ You're not authorized to use this bot.")
            return

        # Parse command
        parts = message.text.split()
        if len(parts) < 2:
            help_text = """
📺 **Add Channel - Help**

**Usage:** `/addchannel @channelname`

**Examples:**
• `/addchannel @mynewschannel`
• `/addchannel @techupdate`

**Steps:**
1. Add me as admin to your channel
2. Give me these permissions:
   ✅ Post messages
   ✅ Edit messages  
   ✅ Delete messages
3. Use the command above

**Note:** Channel username must start with @
            """
            self.bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
            return

        channel_input = parts[1].strip()

        # Validate channel format
        if not channel_input.startswith('@'):
            self.bot.reply_to(message, "❌ Channel username must start with @ (e.g., @mychannel)")
            return

        channel_username = channel_input

        try:
            # Try to get channel info
            chat_info = self.bot.get_chat(channel_username)

            if chat_info.type not in ['channel', 'supergroup']:
                self.bot.reply_to(message, "❌ This is not a channel or supergroup.")
                return

            # Check if bot is admin
            try:
                bot_member = self.bot.get_chat_member(chat_info.id, self.bot.get_me().id)
                if bot_member.status not in ['administrator', 'creator']:
                    self.bot.reply_to(message, f"❌ I'm not an admin in {channel_username}. Please add me as admin first.")
                    return
            except:
                self.bot.reply_to(message, f"❌ I don't have access to {channel_username}. Add me as admin first.")
                return

            # Add to database
            self.db.add_channel(
                user_id=user_id,
                channel_id=str(chat_info.id),
                channel_username=channel_username,
                channel_name=chat_info.title or channel_username
            )

            self.bot.reply_to(message, f"✅ Channel {channel_username} added successfully!\n\nYou can now create posts for this channel using the main menu.")

        except Exception as e:
            logger.error(f"Error adding channel: {e}")
            self.bot.reply_to(message, f"❌ Error accessing {channel_username}. Make sure:\n• Channel exists\n• I'm added as admin\n• Channel username is correct")

    def handle_channels(self, message):
        """Handle /channels command"""
        user_id = message.from_user.id

        if not self.is_authorized(user_id):
            self.bot.reply_to(message, "❌ You're not authorized to use this bot.")
            return

        channels = self.db.get_user_channels(user_id)

        if not channels:
            text = """
📺 **Your Channels**

📭 You haven't added any channels yet.

**To add a channel:**
1. Add me as admin to your channel
2. Use: `/addchannel @yourchannel`

**Example:**
`/addchannel @mynewschannel`
            """
        else:
            text = "📺 **Your Channels:**\n\n"
            for i, channel in enumerate(channels, 1):
                channel_name = channel['channel_name'] or 'Unknown'
                text += f"{i}. **{channel_name}**\n"
                text += f"   Username: {channel['channel_username']}\n"
                text += f"   Added: {channel['created_at'][:10]}\n\n"

            text += "💡 Use the main menu → New Post to create content for these channels."

        self.bot.send_message(message.chat.id, text, parse_mode='Markdown')

    def handle_user_message(self, message):
        """Handle user messages based on current state"""
        user_id = message.from_user.id

        if not self.is_authorized(user_id):
            return

        state = self.menu_handler.get_user_state(user_id)

        # Handle different awaiting inputs
        if state.awaiting_input == 'permit_user':
            self.handle_permit_input(message, user_id)
        elif state.awaiting_input == 'remove_user':
            self.handle_remove_input(message, user_id)
        elif state.awaiting_input == 'schedule_time':
            self.handle_schedule_time_input(message, user_id)
        elif state.awaiting_input == 'self_destruct_time':
            self.handle_self_destruct_time_input(message, user_id)
        elif state.current_menu == "post_editing":
            self.handle_post_content(message, user_id)

    def handle_permit_input(self, message, user_id: int):
        """Handle permit user ID input"""
        if user_id != BOT_OWNER_ID:
            return

        try:
            # Parse user ID (remove - if present)
            user_input = message.text.strip()
            target_user_id = abs(int(user_input.replace('-', '')))

            self.db.whitelist_user(target_user_id, True)

            self.bot.reply_to(message, f"✅ User {target_user_id} has been added to the whitelist.")

            # Try to notify the user
            try:
                self.bot.send_message(
                    target_user_id,
                    "🎉 You've been granted access to Controller Bot! Send /start to begin."
                )
            except:
                pass  # User might not have started the bot

        except ValueError:
            self.bot.reply_to(message, "❌ Invalid user ID. Please send a numeric ID (e.g., 123456789)")
        except Exception as e:
            self.bot.reply_to(message, f"❌ Error: {str(e)}")

        # Clear state
        state = self.menu_handler.get_user_state(user_id)
        state.awaiting_input = None

    def handle_remove_input(self, message, user_id: int):
        """Handle remove user ID input"""
        if user_id != BOT_OWNER_ID:
            return

        try:
            user_input = message.text.strip()
            target_user_id = abs(int(user_input.replace('-', '')))

            self.db.whitelist_user(target_user_id, False)
            self.bot.reply_to(message, f"✅ User {target_user_id} has been removed from the whitelist.")

        except ValueError:
            self.bot.reply_to(message, "❌ Invalid user ID. Please send a numeric ID (e.g., 123456789)")
        except Exception as e:
            self.bot.reply_to(message, f"❌ Error: {str(e)}")

        # Clear state
        state = self.menu_handler.get_user_state(user_id)
        state.awaiting_input = None

    def handle_post_content(self, message, user_id: int):
        """Handle post content input"""
        state = self.menu_handler.get_user_state(user_id)

        # Parse message content
        if message.content_type == 'text':
            state.post_content['text'] = message.text
        elif message.content_type == 'photo':
            state.post_content['media_type'] = 'photo'
            state.post_content['media_file_id'] = message.photo[-1].file_id
            if message.caption:
                state.post_content['text'] = message.caption
        elif message.content_type in ['video', 'document']:
            state.post_content['media_type'] = message.content_type
            if message.content_type == 'video':
                state.post_content['media_file_id'] = message.video.file_id
            else:
                state.post_content['media_file_id'] = message.document.file_id
            if message.caption:
                state.post_content['text'] = message.caption

        # Parse inline buttons from text
        self.parse_inline_buttons(state)

        self.bot.reply_to(message, "✅ Content received! Use the menu buttons to manage your post.")

    def parse_inline_buttons(self, state):
        """Parse inline buttons from post text"""
        lines = state.post_content['text'].split('\n')
        text_lines = []
        buttons = []

        for line in lines:
            if '|' in line and ('http://' in line or 'https://' in line):
                # This looks like a button definition
                parts = line.split('|', 1)
                if len(parts) == 2:
                    button_text = parts[0].strip()
                    button_url = parts[1].strip()
                    if button_text and button_url:
                        buttons.append({'text': button_text, 'url': button_url})
                        continue
            text_lines.append(line)

        state.post_content['text'] = '\n'.join(text_lines).strip()
        state.post_content['buttons'] = buttons

    def handle_schedule_time_input(self, message, user_id: int):
        """Handle schedule time input"""
        time_str = message.text.strip()
        scheduled_time = parse_time_input(time_str)

        if not scheduled_time:
            error_text = f"❌ Invalid time format.\n\n{TIME_FORMAT_HELP}"
            self.bot.reply_to(message, error_text, parse_mode='Markdown')
            return

        state = self.menu_handler.get_user_state(user_id)

        # Schedule the post
        try:
            post_id = self.scheduler.add_scheduled_post(
                user_id=user_id,
                channel_id=state.selected_channel['channel_id'],
                scheduled_time=scheduled_time
            )

            self.bot.reply_to(message, 
                f"✅ Post scheduled!\n\n"
                f"**Time:** {scheduled_time.strftime('%d/%m/%Y %H:%M IST')}\n"
                f"**Channel:** {state.selected_channel['channel_name']}\n"
                f"**ID:** {post_id}\n\n"
                f"You can manage this in Schedules menu."
            )

            # Clear state
            state.awaiting_input = None
            state.post_content = {'text': '', 'media_type': None, 'media_file_id': None, 'buttons': []}

        except Exception as e:
            logger.error(f"Scheduling error: {e}")
            self.bot.reply_to(message, f"❌ Error scheduling post: {str(e)}")
