"""
TechGeekZ Bot - CORRECT KEYBOARD IMPLEMENTATION
Reply Keyboard Menu + Inline Buttons + Button Menus
Enterprise Architecture with PROPER keyboard types
"""
import telebot
from telebot import types
from telebot.types import BotCommand, ReplyKeyboardMarkup, KeyboardButton
import os
import time
import logging
from datetime import datetime, timezone, timedelta
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Callable, Optional, Any

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))
BOT_NAME = "TechGeekZ Bot"
WEBAPP_URL = os.getenv('WEBAPP_URL', '')
IST = timezone(timedelta(hours=5, minutes=30))

logger = logging.getLogger(__name__)

def format_current_time():
    return datetime.now(IST).strftime('%d/%m/%Y | %H:%M')

def get_dashboard_status():
    return "Online" if WEBAPP_URL else "Offline"

@dataclass
class BotEvent:
    event_type: str
    user_id: int
    chat_id: int
    data: Any = None
    message: Any = None
    callback_query: Any = None

class EventHandler(ABC):
    @abstractmethod
    def can_handle(self, event: BotEvent) -> bool:
        pass
    
    @abstractmethod
    def handle(self, event: BotEvent) -> bool:
        pass

class EventDispatcher:
    def __init__(self):
        self.handlers: List[EventHandler] = []
    
    def register_handler(self, handler: EventHandler):
        self.handlers.append(handler)
        logger.info(f"Registered handler: {handler.__class__.__name__}")
    
    def dispatch(self, event: BotEvent) -> bool:
        for handler in self.handlers:
            if handler.can_handle(event):
                return handler.handle(event)
        return False

class KeyboardFactory:
    """Factory for creating different keyboard types"""
    
    @staticmethod
    def create_reply_keyboard_menu(buttons: List[List[str]], resize=True, one_time=False) -> ReplyKeyboardMarkup:
        """Create REPLY KEYBOARD MENU (native keyboard menu at bottom)"""
        keyboard = ReplyKeyboardMarkup(resize_keyboard=resize, one_time_keyboard=one_time)
        
        for row in buttons:
            keyboard_buttons = [KeyboardButton(btn) for btn in row]
            keyboard.row(*keyboard_buttons)
        
        return keyboard
    
    @staticmethod
    def create_inline_buttons(buttons: List[List[dict]]) -> types.InlineKeyboardMarkup:
        """Create INLINE BUTTONS (floating above messages)"""
        keyboard = types.InlineKeyboardMarkup()
        
        for row in buttons:
            button_row = []
            for btn in row:
                if btn['type'] == 'callback':
                    button_row.append(types.InlineKeyboardButton(btn['text'], callback_data=btn['data']))
                elif btn['type'] == 'url':
                    button_row.append(types.InlineKeyboardButton(btn['text'], url=btn['url']))
            
            if button_row:
                keyboard.row(*button_row)
        
        return keyboard

class MenuManager:
    """Advanced menu management with proper keyboard types"""
    
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
    
    def show_main_reply_keyboard_menu(self, chat_id: int):
        """Show MAIN REPLY KEYBOARD MENU (native menu at bottom like red circle)"""
        main_buttons = [["start"]]
        
        if chat_id == BOT_OWNER_ID:
            main_buttons.append(["user"])
        
        main_buttons.extend([
            ["newpost"], 
            ["managepost"], 
            ["schedules"], 
            ["dashboard"]
        ])
        
        keyboard = KeyboardFactory.create_reply_keyboard_menu(main_buttons, resize=True)
        self.bot.send_message(chat_id, "Main menu activated:", reply_markup=keyboard)
    
    def show_user_button_menu(self, chat_id: int):
        """Show USER BUTTON MENU (green circle type)"""
        keyboard = KeyboardFactory.create_inline_buttons([
            [{'text': 'users', 'type': 'callback', 'data': 'users_list'}],
            [{'text': 'permit <user_id>', 'type': 'callback', 'data': 'permit_user'}],
            [{'text': 'remove <user_id>', 'type': 'callback', 'data': 'remove_user'}],
            [{'text': '<<back', 'type': 'callback', 'data': 'main_menu'}]
        ])
        
        self.bot.send_message(chat_id, "👥 User Management:", reply_markup=keyboard)
    
    def show_newpost_inline_buttons(self, chat_id: int):
        """Show NEWPOST INLINE BUTTONS (blue circle type)"""
        keyboard = KeyboardFactory.create_inline_buttons([
            [{'text': 'Channel 1', 'type': 'callback', 'data': 'channel_1'}],
            [{'text': 'Channel 2', 'type': 'callback', 'data': 'channel_2'}],
            [{'text': 'Channel 3', 'type': 'callback', 'data': 'channel_3'}],
            [{'text': '<<back', 'type': 'callback', 'data': 'main_menu'}]
        ])
        
        self.bot.send_message(chat_id, "📢 Select channel to post in:", reply_markup=keyboard)
    
    def show_send_inline_buttons(self, chat_id: int):
        """Show SEND INLINE BUTTONS (blue circle type)"""
        keyboard = KeyboardFactory.create_inline_buttons([
            [{'text': 'schedule post', 'type': 'callback', 'data': 'schedule_post'}],
            [{'text': 'self-destruct', 'type': 'callback', 'data': 'self_destruct'}],
            [{'text': 'post now', 'type': 'callback', 'data': 'post_now'}],
            [{'text': '<<back', 'type': 'callback', 'data': 'newpost_menu'}]
        ])
        
        self.bot.send_message(chat_id, "📤 Send Options:", reply_markup=keyboard)
    
    def show_post_creation_button_menu(self, chat_id: int, channel: str):
        """Show POST CREATION BUTTON MENU (green circle type)"""
        keyboard = KeyboardFactory.create_inline_buttons([
            [{'text': 'send', 'type': 'callback', 'data': 'send_menu'}],
            [{'text': 'cancel', 'type': 'callback', 'data': 'cancel_post'}],
            [{'text': 'preview', 'type': 'callback', 'data': 'preview_post'}],
            [{'text': 'delete all', 'type': 'callback', 'data': 'delete_all'}],
            [{'text': '<<back', 'type': 'callback', 'data': 'newpost'}]
        ])
        
        self.bot.send_message(chat_id, f"✍️ Creating post for {channel}\n\nSend your content:", reply_markup=keyboard)

class CommandEventHandler(EventHandler):
    def __init__(self, bot, db, menu_manager):
        self.bot = bot
        self.db = db
        self.menu_manager = menu_manager
        self.command_handlers = {
            'start': self._handle_start,
            'help': self._handle_help,
            'dashboard': self._handle_dashboard,
            'user': self._handle_user,
            'newpost': self._handle_newpost,
            'managepost': self._handle_managepost,
            'editpost': self._handle_editpost,
            'deletepost': self._handle_deletepost,
            'schedules': self._handle_schedules,
            'permit': self._handle_permit,
            'remove': self._handle_remove
        }
    
    def can_handle(self, event: BotEvent) -> bool:
        return event.event_type == 'command'
    
    def handle(self, event: BotEvent) -> bool:
        handler = self.command_handlers.get(event.data)
        return handler(event) if handler else False
    
    def _handle_start(self, event: BotEvent) -> bool:
        if not self.db.is_user_whitelisted(event.user_id):
            self.bot.reply_to(event.message, "You are not authorized to use this bot.")
            return False
        
        # Get REAL usernames via API
        try:
            user_chat = self.bot.get_chat(event.user_id)
            real_username = user_chat.username or f"User{event.user_id}"
            
            owner_chat = self.bot.get_chat(BOT_OWNER_ID)
            owner_username = f"@{owner_chat.username}" if owner_chat.username else f"@User{BOT_OWNER_ID}"
        except:
            real_username = f"User{event.user_id}"
            owner_username = f"@User{BOT_OWNER_ID}"
        
        # Update user in database
        self.db.add_user_to_whitelist(event.user_id, real_username, event.message.from_user.first_name)
        
        # EXACT welcome message
        start_message = f"""Welcome to {BOT_NAME}

Hello @{real_username}! What new are we thinking today..

Owner: {owner_username}
Dashboard: {get_dashboard_status()}
Time: {format_current_time()}

Bot is active. Send /help for all commands"""

        self.bot.send_message(event.chat_id, start_message)
        
        # Show REPLY KEYBOARD MENU (native menu at bottom)
        self.menu_manager.show_main_reply_keyboard_menu(event.chat_id)
        return True
    
    def _handle_help(self, event: BotEvent) -> bool:
        if not self.db.is_user_whitelisted(event.user_id):
            self.bot.reply_to(event.message, "You are not authorized.")
            return False
        
        help_text = f"""{BOT_NAME} - Available Commands

/start - start the bot
/help - list all commands with descriptions
/user - user settings menu
/newpost - create new posts
/managepost - manage existing posts
/editpost - edit existing post
/deletepost - delete existing post
/schedules - schedule settings menu
/dashboard - web dashboard
/permit <userid> - add user to whitelist
/remove <userid> - remove user from whitelist

Use menu buttons or type commands directly."""
        
        self.bot.send_message(event.chat_id, help_text)
        return True
    
    def _handle_dashboard(self, event: BotEvent) -> bool:
        if not self.db.is_user_whitelisted(event.user_id):
            self.bot.reply_to(event.message, "You are not authorized.")
            return False
        
        if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
            keyboard = KeyboardFactory.create_inline_buttons([
                [{'text': 'Go to Dashboard', 'type': 'url', 'url': f"{WEBAPP_URL}/dashboard"}]
            ])
            self.bot.send_message(event.chat_id, "🌐 Open your dashboard here:", reply_markup=keyboard)
        else:
            self.bot.reply_to(event.message, "Dashboard URL not configured.")
        return True
    
    def _handle_user(self, event: BotEvent) -> bool:
        if event.user_id != BOT_OWNER_ID:
            self.bot.reply_to(event.message, "Owner only.")
            return False
        
        self.menu_manager.show_user_button_menu(event.chat_id)
        return True
    
    def _handle_newpost(self, event: BotEvent) -> bool:
        if not self.db.is_user_whitelisted(event.user_id):
            self.bot.reply_to(event.message, "Unauthorized")
            return False
        
        self.menu_manager.show_newpost_inline_buttons(event.chat_id)
        return True
    
    def _handle_managepost(self, event: BotEvent) -> bool:
        if not self.db.is_user_whitelisted(event.user_id):
            self.bot.reply_to(event.message, "Unauthorized")
            return False
        
        keyboard = KeyboardFactory.create_inline_buttons([
            [{'text': 'edit post', 'type': 'callback', 'data': 'edit_existing'}],
            [{'text': 'delete post', 'type': 'callback', 'data': 'delete_existing'}]
        ])
        self.bot.send_message(event.chat_id, "⚙️ Manage Posts:", reply_markup=keyboard)
        return True
    
    def _handle_editpost(self, event: BotEvent) -> bool:
        if not self.db.is_user_whitelisted(event.user_id):
            self.bot.reply_to(event.message, "Unauthorized")
            return False
        
        self.bot.send_message(event.chat_id, "📝 Edit post feature:\n\nForward the message you want to edit, or use /managepost menu.")
        return True
    
    def _handle_deletepost(self, event: BotEvent) -> bool:
        if not self.db.is_user_whitelisted(event.user_id):
            self.bot.reply_to(event.message, "Unauthorized")
            return False
        
        self.bot.send_message(event.chat_id, "🗑️ Delete post feature:\n\nForward the message you want to delete, or use /managepost menu.")
        return True
    
    def _handle_schedules(self, event: BotEvent) -> bool:
        if not self.db.is_user_whitelisted(event.user_id):
            self.bot.reply_to(event.message, "Unauthorized")
            return False
        
        keyboard = KeyboardFactory.create_inline_buttons([
            [{'text': 'scheduled posts', 'type': 'callback', 'data': 'scheduled_posts'}],
            [{'text': 'self-destruct timings', 'type': 'callback', 'data': 'destruct_timings'}],
            [{'text': 'cancel', 'type': 'callback', 'data': 'cancel_menu'}]
        ])
        self.bot.send_message(event.chat_id, "⏰ Schedules Management:", reply_markup=keyboard)
        return True
    
    def _handle_permit(self, event: BotEvent) -> bool:
        if event.user_id != BOT_OWNER_ID:
            self.bot.reply_to(event.message, "Owner only.")
            return False
        
        parts = event.message.text.split()
        if len(parts) == 2:
            try:
                user_id = int(parts[1].replace('-', ''))
                self.db.add_user_to_whitelist(user_id)
                self.bot.reply_to(event.message, f"✅ User {user_id} permitted!")
            except:
                self.bot.reply_to(event.message, "❌ Invalid user ID.")
        else:
            self.bot.reply_to(event.message, "Format: /permit <user_id>\nExample: /permit 123456789 or /permit -123456789")
        return True
    
    def _handle_remove(self, event: BotEvent) -> bool:
        if event.user_id != BOT_OWNER_ID:
            self.bot.reply_to(event.message, "Owner only.")
            return False
        
        parts = event.message.text.split()
        if len(parts) == 2:
            try:
                user_id = int(parts[1].replace('-', ''))
                if user_id != BOT_OWNER_ID:
                    self.db.remove_user_from_whitelist(user_id)
                    self.bot.reply_to(event.message, f"✅ User {user_id} removed!")
                else:
                    self.bot.reply_to(event.message, "❌ Cannot remove owner!")
            except:
                self.bot.reply_to(event.message, "❌ Error removing user.")
        else:
            self.bot.reply_to(event.message, "Format: /remove <user_id>\nExample: /remove 123456789 or /remove -123456789")
        return True

class CallbackEventHandler(EventHandler):
    def __init__(self, bot, db, menu_manager):
        self.bot = bot
        self.db = db
        self.menu_manager = menu_manager
        self.callback_actions = {
            'main_menu': lambda e: self.menu_manager.show_main_reply_keyboard_menu(e.chat_id),
            'start': lambda e: self.menu_manager.show_main_reply_keyboard_menu(e.chat_id),
            'user_menu': lambda e: self._handle_user_menu(e),
            'newpost': lambda e: self.menu_manager.show_newpost_inline_buttons(e.chat_id),
            'send_menu': lambda e: self.menu_manager.show_send_inline_buttons(e.chat_id),
            'users_list': lambda e: self._show_users_list(e.chat_id),
            'permit_user': lambda e: self._show_permit_format(e.chat_id),
            'remove_user': lambda e: self._show_remove_format(e.chat_id)
        }
        
        self.simple_messages = {
            'schedule_post': "📅 Schedule post format:\n\nDD/MM/YYYY HH:MM (24hr format IST)\nExample: 15/10/2025 14:30\n\nSchedule at same day if date not mentioned",
            'self_destruct': "⏰ Self-destruct format:\n\nDD/MM/YYYY HH:MM (24hr format IST)\nExample: 15/10/2025 14:30\n\nSet at same day if date not mentioned",
            'post_now': "📤 Sends the post instantly... (Feature coming soon)",
            'cancel_post': "❌ Cancel current task",
            'preview_post': "👁️ Shows post preview... (Feature coming soon)",
            'delete_all': "🗑️ Delete the draft/editing post... (Feature coming soon)",
            'edit_existing': "📝 Edit a post on the channel like @controlerbot... (Feature coming soon)",
            'delete_existing': "🗑️ Delete a post on the channel... (Feature coming soon)"
        }
    
    def can_handle(self, event: BotEvent) -> bool:
        return event.event_type == 'callback'
    
    def handle(self, event: BotEvent) -> bool:
        callback_data = event.data
        
        # Handle channel selection
        if callback_data.startswith('channel_'):
            channel = callback_data.replace('channel_', '')
            self.menu_manager.show_post_creation_button_menu(event.chat_id, channel)
            return True
        
        # Handle callback actions
        action = self.callback_actions.get(callback_data)
        if action:
            action(event)
            return True
        
        # Handle simple messages
        message = self.simple_messages.get(callback_data)
        if message:
            self.bot.send_message(event.chat_id, message)
            return True
        
        return False
    
    def _handle_user_menu(self, event: BotEvent):
        if event.user_id == BOT_OWNER_ID:
            self.menu_manager.show_user_button_menu(event.chat_id)
    
    def _show_users_list(self, chat_id: int):
        users = self.db.get_whitelisted_users()
        user_list = f"👥 Whitelisted Users ({len(users)}):\n\n"
        
        for user in users:
            user_id, old_username, first_name = user[0], user[1], user[2]
            try:
                chat = self.bot.get_chat(user_id)
                current_username = chat.username or f"User{user_id}"
            except:
                current_username = f"User{user_id}"
            
            name = first_name or "Unknown"
            user_list += f"{name} @{current_username}\nID: {user_id}\n\n"
        
        keyboard = KeyboardFactory.create_inline_buttons([
            [{'text': '<<back', 'type': 'callback', 'data': 'user_menu'}]
        ])
        self.bot.send_message(chat_id, user_list, reply_markup=keyboard)
    
    def _show_permit_format(self, chat_id: int):
        self.bot.send_message(chat_id, "Format: /permit <user_id>\nExample: /permit 123456789\n\nIgnores '-' before numbers (ex: -1234 or 1234)")
    
    def _show_remove_format(self, chat_id: int):
        self.bot.send_message(chat_id, "Format: /remove <user_id>\nExample: /remove 123456789\n\nIgnores '-' before numbers (ex: -1234 or 1234)")

class BotHandlers:
    def __init__(self, database_manager):
        self.db = database_manager
        self.bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        
        # Initialize components
        self.menu_manager = MenuManager(self.bot, self.db)
        self.event_dispatcher = EventDispatcher()
        
        # Register event handlers
        self.event_dispatcher.register_handler(CommandEventHandler(self.bot, self.db, self.menu_manager))
        self.event_dispatcher.register_handler(CallbackEventHandler(self.bot, self.db, self.menu_manager))
        
        # Setup bot
        self._setup_commands()
        self._register_handlers()
    
    def _setup_commands(self):
        logger.info("🔄 Clearing and updating bot commands...")
        
        try:
            self.bot.delete_my_commands()
            logger.info("🗑️ Old commands cleared")
            time.sleep(2)
        except:
            logger.warning("⚠️ No old commands to clear")
        
        commands = [
            BotCommand("start", "start the bot"),
            BotCommand("help", "list all commands with descriptions"),
            BotCommand("user", "user settings menu"),
            BotCommand("newpost", "create new posts"),
            BotCommand("managepost", "manage existing posts"),
            BotCommand("editpost", "edit existing post"),
            BotCommand("deletepost", "delete existing post"),
            BotCommand("schedules", "schedule settings menu"),
            BotCommand("dashboard", "web dashboard"),
            BotCommand("permit", "add user to whitelist"),
            BotCommand("remove", "remove user from whitelist")
        ]
        
        self.bot.set_my_commands(commands)
        logger.info("✅ All commands recreated and updated!")
    
    def _register_handlers(self):
        @self.bot.message_handler(commands=['start', 'help', 'dashboard', 'user', 'newpost', 'managepost', 'editpost', 'deletepost', 'schedules', 'permit', 'remove'])
        def handle_commands(message):
            command = message.text[1:].split()[0]  # Extract command without '/'
            event = BotEvent('command', message.from_user.id, message.chat.id, command, message)
            self.event_dispatcher.dispatch(event)
        
        @self.bot.message_handler(content_types=['text'])
        def handle_text_messages(message):
            # Handle reply keyboard button presses (from native menu)
            text = message.text.lower()
            
            # Map reply keyboard button text to callback data
            button_map = {
                'start': 'start',
                'user': 'user_menu', 
                'newpost': 'newpost',
                'managepost': 'managepost',
                'schedules': 'schedules',
                'dashboard': 'dashboard'
            }
            
            callback_data = button_map.get(text)
            if callback_data:
                event = BotEvent('callback', message.from_user.id, message.chat.id, callback_data, message)
                self.event_dispatcher.dispatch(event)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            if not self.db.is_user_whitelisted(call.from_user.id):
                self.bot.answer_callback_query(call.id, "Not authorized")
                return
            
            event = BotEvent('callback', call.from_user.id, call.message.chat.id, call.data, callback_query=call)
            self.event_dispatcher.dispatch(event)
            self.bot.answer_callback_query(call.id)
        
        logger.info("All handlers registered successfully")
