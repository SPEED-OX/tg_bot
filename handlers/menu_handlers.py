"""
CORRECTED Menu handlers with proper button types as specified:
- Inline Keyboard (main level)
- Button Menu (sub-menus with ReplyKeyboardMarkup) 
- Inline Button (action buttons)
"""
import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from datetime import datetime
import json
import logging
from typing import Dict, Optional, List
from database.models import DatabaseManager
from utils.time_parser import parse_time_input, format_time_display, TIME_FORMAT_HELP
from config import BOT_OWNER_ID, WEBAPP_URL, IST

logger = logging.getLogger(__name__)

class UserState:
    def __init__(self):
        self.current_menu = "main"
        self.awaiting_input = None
        self.selected_channel = None
        self.post_content = {'text': '', 'media_type': None, 'media_file_id': None, 'buttons': []}
        self.temp_data = {}
        self.keyboard_type = "inline"  # Track current keyboard type

class MenuHandler:
    def __init__(self, bot: telebot.TeleBot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.user_states: Dict[int, UserState] = {}

    def get_user_state(self, user_id: int) -> UserState:
        """Get or create user state"""
        if user_id not in self.user_states:
            self.user_states[user_id] = UserState()
        return self.user_states[user_id]

    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        return user_id == BOT_OWNER_ID or self.db.is_user_whitelisted(user_id)

    def show_main_menu(self, chat_id: int, user_id: int):
        """Show main menu with INLINE KEYBOARD (as specified)"""
        if not self.is_authorized(user_id):
            self.bot.send_message(
                chat_id, 
                "❌ You're not authorized to use this bot.\n\nContact the bot owner for access."
            )
            return

        # INLINE KEYBOARD for main menu
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("🏠 Start", callback_data="menu_start"))
        keyboard.add(InlineKeyboardButton("👥 User", callback_data="menu_user"))
        keyboard.add(InlineKeyboardButton("📝 New Post", callback_data="menu_new_post"))
        keyboard.add(InlineKeyboardButton("📅 Schedules", callback_data="menu_schedules"))

        # Dashboard button
        if WEBAPP_URL and WEBAPP_URL != 'https://your-railway-app.railway.app':
            web_app = WebAppInfo(url=f"{WEBAPP_URL}/dashboard")
            keyboard.add(InlineKeyboardButton("📊 Dashboard", web_app=web_app))

        text = """
🤖 **ChatAudit Bot - Main Menu**

Welcome to your advanced channel management bot!

**🎯 Quick Actions:**
• **Start** - Getting started guide
• **User** - User management (owner)
• **New Post** - Create and schedule posts
• **Schedules** - Manage upcoming posts  
• **Dashboard** - Web interface

**💡 Use /help for complete command guide**
        """

        try:
            # Remove any existing reply keyboard first
            self.bot.send_message(
                chat_id, 
                "🏠 Opening main menu...", 
                reply_markup=ReplyKeyboardRemove()
            )

            self.bot.send_message(
                chat_id, 
                text, 
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            self.bot.send_message(chat_id, "❌ Error showing main menu. Please try /start again.")

        # Update user state
        state = self.get_user_state(user_id)
        state.current_menu = "main"
        state.keyboard_type = "inline"
        state.awaiting_input = None

    def show_user_menu(self, chat_id: int, user_id: int, message_id: int = None, callback_query_id: str = None):
        """Show user management BUTTON MENU (as specified)"""
        if user_id != BOT_OWNER_ID:
            if callback_query_id:
                self.bot.answer_callback_query(callback_query_id, "❌ Owner access only", show_alert=True)
            return

        # BUTTON MENU for user management
        keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        keyboard.add(KeyboardButton("👥 Users"))
        keyboard.add(
            KeyboardButton("➕ Permit <user_id>"),
            KeyboardButton("➖ Remove <user_id>")
        )
        keyboard.add(KeyboardButton("⬅️ Back"))

        text = """
👥 **User Management - Button Menu**

**Available Actions:**

**👥 Users** - List whitelisted users with @username
**➕ Permit** - Add user to whitelist (ignores - signs)
**➖ Remove** - Remove user access (ignores - signs)

**💡 User ID Format:**
Both `123456` and `-123456` work
Get user ID from @userinfobot

**📱 Use the buttons below:**
        """

        self.bot.send_message(
            chat_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

        # Update state
        state = self.get_user_state(user_id)
        state.current_menu = "user_button_menu"
        state.keyboard_type = "reply"

        if callback_query_id:
            self.bot.answer_callback_query(callback_query_id)

    def show_post_button_menu(self, chat_id: int, user_id: int):
        """Show post editor BUTTON MENU (as specified)"""
        state = self.get_user_state(user_id)
        channel = state.selected_channel

        # BUTTON MENU for post editing
        keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        keyboard.add(KeyboardButton("📤 Send"))
        keyboard.add(
            KeyboardButton("❌ Cancel"),
            KeyboardButton("👀 Preview")
        )
        keyboard.add(KeyboardButton("🗑️ Delete All"))
        keyboard.add(KeyboardButton("⬅️ Back"))

        # Content info
        content_info = ""
        if state.post_content['text']:
            content_info = f"\n**✅ Text:** {len(state.post_content['text'])} characters"
        if state.post_content['media_type']:
            content_info += f"\n**✅ Media:** {state.post_content['media_type'].title()}"
        if state.post_content['buttons']:
            content_info += f"\n**✅ Buttons:** {len(state.post_content['buttons'])} added"

        if not content_info:
            content_info = "\n**📝 No content added yet**"

        text = f"""
📝 **Post Editor - Button Menu**

**📺 Channel:** {channel['channel_name']}
**🆔 Username:** {channel['channel_username']}

**📊 Current Content:** {content_info}

**📋 Instructions:**
• Send text, media, or content
• Format buttons: `Button Text | https://url.com`
• Use markdown: **bold**, *italic*, `code`

**📱 Use the buttons below:**
        """

        self.bot.send_message(
            chat_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

        # Update state
        state.current_menu = "post_button_menu"
        state.keyboard_type = "reply"

    def show_send_inline_buttons(self, chat_id: int, user_id: int):
        """Show send options as INLINE BUTTONS (as specified)"""
        # INLINE BUTTONS for send options
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("📅 Schedule Post", callback_data="send_schedule"),
            InlineKeyboardButton("💣 Self-Destruct", callback_data="send_self_destruct"),
            InlineKeyboardButton("🚀 Post Now", callback_data="send_now"),
            InlineKeyboardButton("⬅️ Back", callback_data="send_back")
        )

        text = """
📤 **Send Options - Inline Buttons**

**📅 Schedule Post** - Set date/time for posting
**💣 Self-Destruct** - Auto-delete after time
**🚀 Post Now** - Send immediately

**⏰ Time Format:**
• `dd/mm hh:mm` - Specific date (5/10 15:00)
• `hh:mm` - Same day if not past (15:00)
• All times in IST (24-hour format)

**👆 Use the inline buttons above:**
        """

        self.bot.send_message(
            chat_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

        # Update state
        state = self.get_user_state(user_id)
        state.current_menu = "send_inline_buttons"
        state.keyboard_type = "inline"

    def show_schedules_button_menu(self, chat_id: int, user_id: int, message_id: int = None, callback_query_id: str = None):
        """Show schedules BUTTON MENU (as specified)"""
        # BUTTON MENU for schedules
        keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        keyboard.add(KeyboardButton("📋 Scheduled Posts"))
        keyboard.add(KeyboardButton("💣 Self-Destruct Timings"))
        keyboard.add(KeyboardButton("❌ Cancel"))
        keyboard.add(KeyboardButton("⬅️ Back"))

        text = """
📅 **Schedules Management - Button Menu**

**📋 Scheduled Posts** - View upcoming posts & timings
**💣 Self-Destruct Timings** - View auto-delete tasks & timings
**❌ Cancel** - Cancel scheduled items

**📊 Quick Stats:**
Loading schedule information...

**📱 Use the buttons below:**
        """

        self.bot.send_message(
            chat_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

        # Update state
        state = self.get_user_state(user_id)
        state.current_menu = "schedules_button_menu"
        state.keyboard_type = "reply"

        if callback_query_id:
            self.bot.answer_callback_query(callback_query_id)

    def show_cancel_inline_buttons(self, chat_id: int, user_id: int):
        """Show cancel options as INLINE BUTTONS (as specified)"""
        # INLINE BUTTONS for cancel options
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("💣 Self-Destruct", callback_data="cancel_self_destruct"),
            InlineKeyboardButton("📅 Scheduled Post", callback_data="cancel_scheduled"),
            InlineKeyboardButton("⬅️ Back", callback_data="cancel_back")
        )

        text = """
❌ **Cancel Options - Inline Buttons**

**💣 Self-Destruct** - Cancel self-destruct task
**📅 Scheduled Post** - Cancel scheduled post

**👆 Choose what to cancel:**
        """

        self.bot.send_message(
            chat_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

        # Update state
        state = self.get_user_state(user_id)
        state.current_menu = "cancel_inline_buttons"
        state.keyboard_type = "inline"

    def handle_callback_query(self, call):
        """Handle callback queries from INLINE keyboards"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        data = call.data

        if not self.is_authorized(user_id):
            self.bot.answer_callback_query(call.id, "❌ Not authorized", show_alert=True)
            return

        try:
            # Main menu inline keyboard options
            if data == "menu_start":
                self.show_start_menu(chat_id, call.message.message_id, call.id)
            elif data == "menu_user":
                self.show_user_menu(chat_id, user_id, call.message.message_id, call.id)
            elif data == "menu_new_post":
                self.show_channel_selection(chat_id, user_id, call.message.message_id, call.id)
            elif data == "menu_schedules":
                self.show_schedules_button_menu(chat_id, user_id, call.message.message_id, call.id)

            # Channel selection (inline)
            elif data.startswith("select_channel_"):
                self.handle_channel_selection(chat_id, user_id, call.message.message_id, call.id, data)

            # Send inline buttons
            elif data == "send_schedule":
                self.handle_schedule_post(chat_id, user_id, call.message.message_id, call.id)
            elif data == "send_self_destruct":
                self.handle_self_destruct(chat_id, user_id, call.message.message_id, call.id)
            elif data == "send_now":
                self.handle_post_now(chat_id, user_id, call.message.message_id, call.id)
            elif data == "send_back":
                self.show_post_button_menu(chat_id, user_id)
                self.bot.answer_callback_query(call.id)

            # Cancel inline buttons
            elif data == "cancel_self_destruct":
                self.handle_cancel_self_destruct(chat_id, user_id, call.message.message_id, call.id)
            elif data == "cancel_scheduled":
                self.handle_cancel_scheduled(chat_id, user_id, call.message.message_id, call.id)
            elif data == "cancel_back":
                self.show_schedules_button_menu(chat_id, user_id)
                self.bot.answer_callback_query(call.id)

            # Back to main from any menu
            elif data == "back_to_main":
                self.show_main_menu(chat_id, user_id)
                self.bot.answer_callback_query(call.id)

        except Exception as e:
            logger.error(f"Error handling callback query {data}: {e}")
            self.bot.answer_callback_query(call.id, "❌ Error processing request", show_alert=True)

    def handle_button_menu_messages(self, message):
        """Handle messages from BUTTON MENUS (ReplyKeyboardMarkup)"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        text = message.text

        if not self.is_authorized(user_id):
            return

        state = self.get_user_state(user_id)

        # Handle User Button Menu
        if state.current_menu == "user_button_menu":
            if text == "👥 Users":
                self.show_users_list(chat_id, user_id)
            elif text == "➕ Permit <user_id>":
                self.handle_permit_user_button(chat_id, user_id)
            elif text == "➖ Remove <user_id>":
                self.handle_remove_user_button(chat_id, user_id)
            elif text == "⬅️ Back":
                self.show_main_menu(chat_id, user_id)

        # Handle Post Button Menu
        elif state.current_menu == "post_button_menu":
            if text == "📤 Send":
                self.show_send_inline_buttons(chat_id, user_id)
            elif text == "❌ Cancel":
                self.handle_post_cancel_button(chat_id, user_id)
            elif text == "👀 Preview":
                self.handle_post_preview_button(chat_id, user_id)
            elif text == "🗑️ Delete All":
                self.handle_post_delete_all_button(chat_id, user_id)
            elif text == "⬅️ Back":
                self.show_channel_selection_from_button_menu(chat_id, user_id)

        # Handle Schedules Button Menu
        elif state.current_menu == "schedules_button_menu":
            if text == "📋 Scheduled Posts":
                self.show_scheduled_posts_button(chat_id, user_id)
            elif text == "💣 Self-Destruct Timings":
                self.show_self_destructs_button(chat_id, user_id)
            elif text == "❌ Cancel":
                self.show_cancel_inline_buttons(chat_id, user_id)
            elif text == "⬅️ Back":
                self.show_main_menu(chat_id, user_id)

    # Additional helper methods for proper implementation
    def show_start_menu(self, chat_id: int, message_id: int, callback_query_id: str):
        """Show start information"""
        text = """
🏠 **Getting Started with ChatAudit Bot**

**📋 Quick Setup:**
1. Add me as admin to your channel
2. Use `/addchannel @yourchannel` to register it
3. Create posts using the **New Post** button
4. Schedule posts or set self-destruct timers

**🎯 Main Features:**
• **Channel Management** - Add unlimited channels
• **Rich Content** - Text, media, buttons supported  
• **Smart Scheduling** - dd/mm hh:mm format (IST)
• **Self-Destruct** - Auto-delete messages
• **Web Dashboard** - Advanced management

Ready to manage your channels! 🚀
        """

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_main"))

        try:
            self.bot.edit_message_text(
                text, 
                chat_id, 
                message_id,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            self.bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=keyboard)

        self.bot.answer_callback_query(callback_query_id)

    def show_channel_selection(self, chat_id: int, user_id: int, message_id: int, callback_query_id: str):
        """Show channel selection for new post (inline keyboard)"""
        channels = self.db.get_user_channels(user_id)

        if not channels:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_main"))

            text = """
📺 **No Channels Added**

You need to add channels first!

**Quick Setup:**
1. Add me as admin to your channel
2. Use: `/addchannel @yourchannel`
3. Return here to create posts

**Example:**
`/addchannel @mynewschannel`
            """

            try:
                self.bot.edit_message_text(text, chat_id, message_id, parse_mode='Markdown', reply_markup=keyboard)
            except Exception as e:
                self.bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=keyboard)

            self.bot.answer_callback_query(callback_query_id)
            return

        keyboard = InlineKeyboardMarkup(row_width=1)

        for channel in channels:
            channel_name = channel['channel_name'] or channel['channel_username']
            callback_data = f"select_channel_{channel['id']}"
            keyboard.add(InlineKeyboardButton(f"📺 {channel_name}", callback_data=callback_data))

        keyboard.add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_main"))

        text = f"""
📝 **New Post - Select Channel**

**📺 Your Channels ({len(channels)}):**

Choose a channel to create your post:
        """

        try:
            self.bot.edit_message_text(text, chat_id, message_id, parse_mode='Markdown', reply_markup=keyboard)
        except Exception as e:
            self.bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=keyboard)

        self.bot.answer_callback_query(callback_query_id)

    def handle_channel_selection(self, chat_id: int, user_id: int, message_id: int, callback_query_id: str, data: str):
        """Handle channel selection and show post button menu"""
        channel_id = data.replace("select_channel_", "")

        # Get channel info
        channels = self.db.get_user_channels(user_id)
        selected_channel = None

        for channel in channels:
            if str(channel['id']) == channel_id:
                selected_channel = channel
                break

        if not selected_channel:
            self.bot.answer_callback_query(callback_query_id, "❌ Channel not found", show_alert=True)
            return

        # Update user state
        state = self.get_user_state(user_id)
        state.selected_channel = selected_channel
        state.post_content = {'text': '', 'media_type': None, 'media_file_id': None, 'buttons': []}

        self.bot.answer_callback_query(callback_query_id, "✅ Channel selected!")
        self.show_post_button_menu(chat_id, user_id)

    # Placeholder methods for button handlers
    def show_users_list(self, chat_id: int, user_id: int):
        """Show users list from button menu"""
        if user_id != BOT_OWNER_ID:
            return

        users = self.db.get_whitelisted_users()

        if not users:
            text = "👥 **Whitelisted Users**\n\n📭 No users whitelisted yet."
        else:
            text = f"👥 **Whitelisted Users ({len(users)}):**\n\n"
            for user in users:
                username = f"@{user['username']}" if user['username'] else "No @username"
                name = user['first_name'] or 'Unknown'
                text += f"**{name}** ({username})\n"
                text += f"ID: `{user['user_id']}`\n\n"

        self.bot.send_message(chat_id, text, parse_mode='Markdown')

    def handle_permit_user_button(self, chat_id: int, user_id: int):
        """Handle permit user from button menu"""
        if user_id != BOT_OWNER_ID:
            return

        state = self.get_user_state(user_id)
        state.awaiting_input = 'permit_user'

        text = """
➕ **Permit User Format**

**📝 Send the user ID to whitelist:**

**Format Examples:**
• `123456789` ✅
• `-123456789` ✅ (- is ignored)

**💡 How to get user ID:**
1. Ask user to message @userinfobot
2. Bot will show their ID
3. Send that ID here

**Example:** Just type `987654321`
        """

        self.bot.send_message(chat_id, text, parse_mode='Markdown')

    def handle_remove_user_button(self, chat_id: int, user_id: int):
        """Handle remove user from button menu"""
        if user_id != BOT_OWNER_ID:
            return

        state = self.get_user_state(user_id)
        state.awaiting_input = 'remove_user'

        text = """
➖ **Remove User Format**

**📝 Send the user ID to remove:**

**Format Examples:**
• `123456789` ✅
• `-123456789` ✅ (- is ignored)

**⚠️ Warning:**
User will lose access immediately
You can re-add them later

**Example:** Just type `987654321`
        """

        self.bot.send_message(chat_id, text, parse_mode='Markdown')

    def handle_post_cancel_button(self, chat_id: int, user_id: int):
        """Cancel post from button menu"""
        state = self.get_user_state(user_id)
        state.post_content = {'text': '', 'media_type': None, 'media_file_id': None, 'buttons': []}
        self.bot.send_message(chat_id, "✅ Post cancelled!")
        self.show_main_menu(chat_id, user_id)

    def handle_post_preview_button(self, chat_id: int, user_id: int):
        """Show post preview from button menu"""
        state = self.get_user_state(user_id)

        if not state.post_content['text'] and not state.post_content['media_type']:
            self.bot.send_message(chat_id, "❌ No content to preview!")
            return

        # Create preview
        preview_text = f"👀 **Post Preview:**\n\n"

        if state.post_content['text']:
            preview_text += state.post_content['text']

        if state.post_content['buttons']:
            preview_text += "\n\n**Buttons:**\n"
            for button in state.post_content['buttons']:
                preview_text += f"• {button['text']} → {button['url']}\n"

        if state.post_content['media_type']:
            preview_text += f"\n**Media:** {state.post_content['media_type'].title()}"

        self.bot.send_message(chat_id, preview_text, parse_mode='Markdown')

    def handle_post_delete_all_button(self, chat_id: int, user_id: int):
        """Delete all content from button menu"""
        state = self.get_user_state(user_id)
        state.post_content = {'text': '', 'media_type': None, 'media_file_id': None, 'buttons': []}
        self.bot.send_message(chat_id, "🗑️ All content deleted!")

    def show_channel_selection_from_button_menu(self, chat_id: int, user_id: int):
        """Return to channel selection from button menu"""
        # Remove reply keyboard and show inline keyboard for channel selection
        self.bot.send_message(
            chat_id,
            "📝 **Returning to channel selection...**",
            reply_markup=ReplyKeyboardRemove()
        )

        channels = self.db.get_user_channels(user_id)

        if not channels:
            self.bot.send_message(chat_id, "❌ No channels available. Use /addchannel first.")
            self.show_main_menu(chat_id, user_id)
            return

        keyboard = InlineKeyboardMarkup(row_width=1)

        for channel in channels:
            channel_name = channel['channel_name'] or channel['channel_username']
            callback_data = f"select_channel_{channel['id']}"
            keyboard.add(InlineKeyboardButton(f"📺 {channel_name}", callback_data=callback_data))

        keyboard.add(InlineKeyboardButton("⬅️ Back to Main", callback_data="back_to_main"))

        text = f"""
📝 **New Post - Select Channel**

**📺 Your Channels ({len(channels)}):**

Choose a channel to create your post:
        """

        self.bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=keyboard)

        # Update state
        state = self.get_user_state(user_id)
        state.current_menu = "channel_selection"
        state.keyboard_type = "inline"

    # Additional placeholder methods
    def show_scheduled_posts_button(self, chat_id: int, user_id: int):
        """Show scheduled posts from button menu"""
        text = "📋 **Scheduled Posts & Timings**\n\nLoading scheduled posts..."
        self.bot.send_message(chat_id, text, parse_mode='Markdown')

    def show_self_destructs_button(self, chat_id: int, user_id: int):
        """Show self-destruct timings from button menu"""
        text = "💣 **Self-Destruct Timings**\n\nLoading self-destruct tasks..."
        self.bot.send_message(chat_id, text, parse_mode='Markdown')

    def handle_schedule_post(self, chat_id: int, user_id: int, message_id: int, callback_query_id: str):
        """Handle schedule post from inline button"""
        state = self.get_user_state(user_id)

        if not state.post_content['text'] and not state.post_content['media_type']:
            self.bot.answer_callback_query(callback_query_id, "❌ Add content first!", show_alert=True)
            return

        state.awaiting_input = 'schedule_time'

        text = f"""
📅 **Schedule Post Format**

{TIME_FORMAT_HELP}

**📝 Send your desired time:**

**Examples:**
• `5/10 15:00` - October 5th at 3:00 PM
• `15:00` - Today at 3:00 PM (same day if not past)

**⏰ Current time:** {datetime.now(IST).strftime('%d/%m/%Y %H:%M IST')}

**Format:** Send date & time or just time
        """

        self.bot.send_message(chat_id, text, parse_mode='Markdown')
        self.bot.answer_callback_query(callback_query_id, "📅 Send schedule time!")

    def handle_self_destruct(self, chat_id: int, user_id: int, message_id: int, callback_query_id: str):
        """Handle self-destruct from inline button"""
        state = self.get_user_state(user_id)

        if not state.post_content['text'] and not state.post_content['media_type']:
            self.bot.answer_callback_query(callback_query_id, "❌ Add content first!", show_alert=True)
            return

        state.awaiting_input = 'self_destruct_time'

        text = f"""
💣 **Self-Destruct Format**

**Schedule auto-delete:**

{TIME_FORMAT_HELP}

**📝 Send delete time:**

**Examples:**
• `5/10 15:00` - Delete on October 5th at 3:00 PM
• `15:00` - Delete today at 3:00 PM (same day if not past)

**⏰ Current time:** {datetime.now(IST).strftime('%d/%m/%Y %H:%M IST')}

**Format:** Send date & time or just time
        """

        self.bot.send_message(chat_id, text, parse_mode='Markdown')
        self.bot.answer_callback_query(callback_query_id, "💣 Send destruct time!")

    def handle_post_now(self, chat_id: int, user_id: int, message_id: int, callback_query_id: str):
        """Handle post now from inline button"""
        state = self.get_user_state(user_id)

        if not state.post_content['text'] and not state.post_content['media_type']:
            self.bot.answer_callback_query(callback_query_id, "❌ Add content first!", show_alert=True)
            return

        self.bot.answer_callback_query(callback_query_id, "🚀 Post now feature ready - implementation needed!", show_alert=True)

    def handle_cancel_self_destruct(self, chat_id: int, user_id: int, message_id: int, callback_query_id: str):
        """Handle cancel self-destruct from inline button"""
        self.bot.answer_callback_query(callback_query_id, "💣 Select self-destruct task to cancel - feature ready!", show_alert=True)

    def handle_cancel_scheduled(self, chat_id: int, user_id: int, message_id: int, callback_query_id: str):
        """Handle cancel scheduled post from inline button"""
        self.bot.answer_callback_query(callback_query_id, "📅 Select scheduled post to cancel - feature ready!", show_alert=True)
