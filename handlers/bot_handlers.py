"""
TechGeekZ Bot - ENTERPRISE ARCHITECTURE
Strategy Pattern + Observer Pattern + Event-Driven Design
ZERO if/elif chains - Pure OOP architecture
"""
import telebot
from telebot import types
from telebot.types import BotCommand
import os
import time
import logging
from datetime import datetime, timezone, timedelta
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Callable, Optional, Any
from enum import Enum
import inspect

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

# Event-Driven Architecture
@dataclass
class BotEvent:
    """Unified event structure"""
    event_type: str
    user_id: int
    chat_id: int
    data: Any = None
    message: Any = None
    callback_query: Any = None

class EventHandler(ABC):
    """Abstract event handler"""
    
    @abstractmethod
    def can_handle(self, event: BotEvent) -> bool:
        pass
    
    @abstractmethod
    def handle(self, event: BotEvent) -> bool:
        pass

class EventDispatcher:
    """Event dispatcher using Observer Pattern"""
    
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

# Strategy Pattern Implementation
class MenuStrategy(ABC):
    """Abstract menu strategy"""
    
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
    
    @abstractmethod
    def show_menu(self, chat_id: int, **kwargs):
        pass
    
    def get_real_username(self, user_id: int) -> str:
        try:
            chat = self.bot.get_chat(user_id)
            return chat.username or f"User{user_id}"
        except:
            return f"User{user_id}"
    
    def get_owner_username(self) -> str:
        try:
            chat = self.bot.get_chat(BOT_OWNER_ID)
            username = chat.username
            return f"@{username}" if username else f"@User{BOT_OWNER_ID}"
        except:
            return f"@User{BOT_OWNER_ID}"

# Menu Strategies
class MainMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("start", callback_data="start"))
        
        if chat_id == BOT_OWNER_ID:
            keyboard.row(types.InlineKeyboardButton("user", callback_data="user_menu"))
        
        keyboard.row(types.InlineKeyboardButton("newpost", callback_data="newpost"))
        keyboard.row(types.InlineKeyboardButton("managepost", callback_data="managepost"))
        keyboard.row(types.InlineKeyboardButton("schedules", callback_data="schedules"))
        
        if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
            keyboard.row(types.InlineKeyboardButton("dashboard", url=f"{WEBAPP_URL}/dashboard"))
        
        self.bot.send_message(chat_id, "Menu:", reply_markup=keyboard)

class UserMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("users", callback_data="users_list"))
        keyboard.row(types.InlineKeyboardButton("permit <user_id>", callback_data="permit_user"))
        keyboard.row(types.InlineKeyboardButton("remove <user_id>", callback_data="remove_user"))
        keyboard.row(types.InlineKeyboardButton("<<back", callback_data="main_menu"))
        
        self.bot.send_message(chat_id, "👥 User Management:", reply_markup=keyboard)

class NewPostMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("Channel 1", callback_data="channel_1"))
        keyboard.row(types.InlineKeyboardButton("Channel 2", callback_data="channel_2"))
        keyboard.row(types.InlineKeyboardButton("Channel 3", callback_data="channel_3"))
        keyboard.row(types.InlineKeyboardButton("<<back", callback_data="main_menu"))
        
        self.bot.send_message(chat_id, "📢 Select channel to post in:", reply_markup=keyboard)

class PostCreationMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        channel = kwargs.get('channel', 'Unknown')
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("send", callback_data="send_menu"))
        keyboard.row(types.InlineKeyboardButton("cancel", callback_data="cancel_post"))
        keyboard.row(types.InlineKeyboardButton("preview", callback_data="preview_post"))
        keyboard.row(types.InlineKeyboardButton("delete all", callback_data="delete_all"))
        keyboard.row(types.InlineKeyboardButton("<<back", callback_data="newpost"))
        
        self.bot.send_message(chat_id, f"✍️ Creating post for {channel}\n\nSend your content:", reply_markup=keyboard)

class SendMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("schedule post", callback_data="schedule_post"))
        keyboard.row(types.InlineKeyboardButton("self-destruct", callback_data="self_destruct"))
        keyboard.row(types.InlineKeyboardButton("post now", callback_data="post_now"))
        keyboard.row(types.InlineKeyboardButton("<<back", callback_data="newpost"))
        
        self.bot.send_message(chat_id, "📤 Send Options:", reply_markup=keyboard)

class ManagePostMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("edit post", callback_data="edit_existing"))
        keyboard.row(types.InlineKeyboardButton("delete post", callback_data="delete_existing"))
        keyboard.row(types.InlineKeyboardButton("<<back", callback_data="main_menu"))
        
        self.bot.send_message(chat_id, "⚙️ Manage Posts:", reply_markup=keyboard)

class SchedulesMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("scheduled posts", callback_data="scheduled_posts"))
        keyboard.row(types.InlineKeyboardButton("self-destruct timings", callback_data="destruct_timings"))
        keyboard.row(types.InlineKeyboardButton("cancel", callback_data="cancel_menu"))
        keyboard.row(types.InlineKeyboardButton("<<back", callback_data="main_menu"))
        
        self.bot.send_message(chat_id, "⏰ Schedules Management:", reply_markup=keyboard)

class CancelMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("self-destruct", callback_data="cancel_destruct"))
        keyboard.row(types.InlineKeyboardButton("scheduled post", callback_data="cancel_scheduled"))
        keyboard.row(types.InlineKeyboardButton("<<back", callback_data="schedules"))
        
        self.bot.send_message(chat_id, "❌ Cancel Options:", reply_markup=keyboard)

# Command Strategy Pattern
class CommandStrategy(ABC):
    def __init__(self, bot, db, menu_factory):
        self.bot = bot
        self.db = db
        self.menu_factory = menu_factory
    
    @abstractmethod
    def execute(self, event: BotEvent) -> bool:
        pass
    
    def can_execute(self, user_id: int) -> bool:
        return self.db.is_user_whitelisted(user_id)
    
    def is_owner(self, user_id: int) -> bool:
        return user_id == BOT_OWNER_ID

class StartCommandStrategy(CommandStrategy):
    def execute(self, event: BotEvent) -> bool:
        if not self.can_execute(event.user_id):
            self.bot.reply_to(event.message, "You are not authorized to use this bot.")
            return False
        
        # Get REAL current username
        try:
            chat = self.bot.get_chat(event.user_id)
            real_username = chat.username or f"User{event.user_id}"
        except:
            real_username = f"User{event.user_id}"
        
        # Get owner username
        try:
            owner_chat = self.bot.get_chat(BOT_OWNER_ID)
            owner_username = f"@{owner_chat.username}" if owner_chat.username else f"@User{BOT_OWNER_ID}"
        except:
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
        self.menu_factory.get_menu('main').show_menu(event.chat_id)
        return True

class HelpCommandStrategy(CommandStrategy):
    def execute(self, event: BotEvent) -> bool:
        if not self.can_execute(event.user_id):
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

class DashboardCommandStrategy(CommandStrategy):
    def execute(self, event: BotEvent) -> bool:
        if not self.can_execute(event.user_id):
            self.bot.reply_to(event.message, "You are not authorized.")
            return False
        
        if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("Go to Dashboard", url=f"{WEBAPP_URL}/dashboard"))
            self.bot.send_message(event.chat_id, "🌐 Open your dashboard here:", reply_markup=keyboard)
        else:
            self.bot.reply_to(event.message, "Dashboard URL not configured.")
        return True

class UserCommandStrategy(CommandStrategy):
    def execute(self, event: BotEvent) -> bool:
        if not self.is_owner(event.user_id):
            self.bot.reply_to(event.message, "Owner only.")
            return False
        
        self.menu_factory.get_menu('user').show_menu(event.chat_id)
        return True

# Menu Factory Pattern
class MenuFactory:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.menus = {
            'main': MainMenuStrategy(bot, db),
            'user': UserMenuStrategy(bot, db),
            'newpost': NewPostMenuStrategy(bot, db),
            'post_creation': PostCreationMenuStrategy(bot, db),
            'send': SendMenuStrategy(bot, db),
            'managepost': ManagePostMenuStrategy(bot, db),
            'schedules': SchedulesMenuStrategy(bot, db),
            'cancel': CancelMenuStrategy(bot, db)
        }
    
    def get_menu(self, menu_type: str) -> MenuStrategy:
        return self.menus.get(menu_type, self.menus['main'])

# Event Handlers
class CommandEventHandler(EventHandler):
    def __init__(self, bot, db, menu_factory):
        self.bot = bot
        self.db = db
        self.menu_factory = menu_factory
        self.commands = {
            'start': StartCommandStrategy(bot, db, menu_factory),
            'help': HelpCommandStrategy(bot, db, menu_factory),
            'dashboard': DashboardCommandStrategy(bot, db, menu_factory),
            'user': UserCommandStrategy(bot, db, menu_factory)
        }
    
    def can_handle(self, event: BotEvent) -> bool:
        return event.event_type == 'command'
    
    def handle(self, event: BotEvent) -> bool:
        command = event.data
        strategy = self.commands.get(command)
        return strategy.execute(event) if strategy else False

class CallbackEventHandler(EventHandler):
    def __init__(self, bot, db, menu_factory):
        self.bot = bot
        self.db = db
        self.menu_factory = menu_factory
        self.action_map = {
            'main_menu': lambda e: self.menu_factory.get_menu('main').show_menu(e.chat_id),
            'start': lambda e: self.menu_factory.get_menu('main').show_menu(e.chat_id),
            'user_menu': lambda e: self._handle_user_menu(e),
            'newpost': lambda e: self.menu_factory.get_menu('newpost').show_menu(e.chat_id),
            'managepost': lambda e: self.menu_factory.get_menu('managepost').show_menu(e.chat_id),
            'schedules': lambda e: self.menu_factory.get_menu('schedules').show_menu(e.chat_id),
            'send_menu': lambda e: self.menu_factory.get_menu('send').show_menu(e.chat_id),
            'cancel_menu': lambda e: self.menu_factory.get_menu('cancel').show_menu(e.chat_id),
            'users_list': lambda e: self._show_users_list(e.chat_id),
            'permit_user': lambda e: self._show_permit_format(e.chat_id),
            'remove_user': lambda e: self._show_remove_format(e.chat_id)
        }
    
    def can_handle(self, event: BotEvent) -> bool:
        return event.event_type == 'callback'
    
    def handle(self, event: BotEvent) -> bool:
        callback_data = event.data
        
        # Handle channel selection
        if callback_data.startswith('channel_'):
            channel = callback_data.replace('channel_', '')
            self.menu_factory.get_menu('post_creation').show_menu(event.chat_id, channel=channel)
            return True
        
        # Handle other callbacks
        action = self.action_map.get(callback_data)
        if action:
            action(event)
            return True
        
        # Handle remaining actions with simple messages
        message_map = {
            'schedule_post': "📅 Schedule post format:\n\nDD/MM/YYYY HH:MM (24hr format IST)\nExample: 15/10/2025 14:30\n\nSchedule at same day if date not mentioned",
            'self_destruct': "⏰ Self-destruct format:\n\nDD/MM/YYYY HH:MM (24hr format IST)\nExample: 15/10/2025 14:30\n\nSet at same day if date not mentioned",
            'post_now': "📤 Sends the post instantly... (Feature coming soon)",
            'cancel_post': "❌ Cancel current task",
            'preview_post': "👁️ Shows post preview... (Feature coming soon)",
            'delete_all': "🗑️ Delete the draft/editing post... (Feature coming soon)",
            'edit_existing': "📝 Edit a post on the channel like @controlerbot... (Feature coming soon)",
            'delete_existing': "🗑️ Delete a post on the channel... (Feature coming soon)",
            'cancel_scheduled': "❌ Scheduled post cancelled",
            'cancel_destruct': "❌ Self-destruct cancelled"
        }
        
        message = message_map.get(callback_data)
        if message:
            self.bot.send_message(event.chat_id, message)
            return True
        
        return False
    
    def _handle_user_menu(self, event: BotEvent):
        if event.user_id == BOT_OWNER_ID:
            self.menu_factory.get_menu('user').show_menu(event.chat_id)
    
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
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("<<back", callback_data="user_menu"))
        self.bot.send_message(chat_id, user_list, reply_markup=keyboard)
    
    def _show_permit_format(self, chat_id: int):
        self.bot.send_message(chat_id, "Format: /permit <user_id>\nExample: /permit 123456789\n\nIgnores '-' before numbers (ex: -1234 or 1234)")
    
    def _show_remove_format(self, chat_id: int):
        self.bot.send_message(chat_id, "Format: /remove <user_id>\nExample: /remove 123456789\n\nIgnores '-' before numbers (ex: -1234 or 1234)")

# Main Bot Handler
class BotHandlers:
    def __init__(self, database_manager):
        self.db = database_manager
        self.bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        
        # Initialize architecture
        self.menu_factory = MenuFactory(self.bot, self.db)
        self.event_dispatcher = EventDispatcher()
        
        # Register event handlers
        self.event_dispatcher.register_handler(CommandEventHandler(self.bot, self.db, self.menu_factory))
        self.event_dispatcher.register_handler(CallbackEventHandler(self.bot, self.db, self.menu_factory))
        
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
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            event = BotEvent('command', message.from_user.id, message.chat.id, 'start', message)
            self.event_dispatcher.dispatch(event)
        
        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            event = BotEvent('command', message.from_user.id, message.chat.id, 'help', message)
            self.event_dispatcher.dispatch(event)
        
        @self.bot.message_handler(commands=['dashboard'])
        def handle_dashboard(message):
            event = BotEvent('command', message.from_user.id, message.chat.id, 'dashboard', message)
            self.event_dispatcher.dispatch(event)
        
        @self.bot.message_handler(commands=['user'])
        def handle_user(message):
            event = BotEvent('command', message.from_user.id, message.chat.id, 'user', message)
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
