"""
TechGeekZ Bot - ENTERPRISE ARCHITECTURE with CORRECT Button Types
Strategy Pattern + Observer Pattern + Event-Driven Design
RED = Inline Keyboard Menu, GREEN = Button Menu, BLUE = Inline Buttons
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

# Strategy Pattern for Different Button Types
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

# RED CIRCLE - Inline Keyboard Menu (Main Navigation)
class MainInlineKeyboardMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        """RED CIRCLE - Main inline keyboard menu at bottom"""
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

# GREEN CIRCLE - Button Menu (Reply Keyboard)
class UserButtonMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        """GREEN CIRCLE - User button menu (reply keyboard)"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        keyboard.row("users", "permit <user_id>")
        keyboard.row("remove <user_id>", "<<back")
        
        self.bot.send_message(chat_id, "👥 User Management:", reply_markup=keyboard)

class NewPostButtonMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        """GREEN CIRCLE - Newpost button menu (reply keyboard)"""
        # First show channel selection as inline buttons
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("Channel 1", callback_data="channel_1"))
        keyboard.row(types.InlineKeyboardButton("Channel 2", callback_data="channel_2"))
        keyboard.row(types.InlineKeyboardButton("Channel 3", callback_data="channel_3"))
        keyboard.row(types.InlineKeyboardButton("<<back", callback_data="main_menu"))
        
        self.bot.send_message(chat_id, "📢 Select channel to post in:", reply_markup=keyboard)

class PostCreationButtonMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        """GREEN CIRCLE - Post creation button menu after channel selection"""
        channel = kwargs.get('channel', 'Unknown')
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        keyboard.row("send", "cancel")
        keyboard.row("preview", "delete all")
        keyboard.row("<<back")
        
        self.bot.send_message(chat_id, f"✍️ Creating post for {channel}\n\nSend your content:", reply_markup=keyboard)

class ManagePostButtonMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        """GREEN CIRCLE - Managepost button menu"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        keyboard.row("edit post", "delete post")
        keyboard.row("<<back")
        
        self.bot.send_message(chat_id, "⚙️ Manage Posts:", reply_markup=keyboard)

class SchedulesButtonMenuStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        """GREEN CIRCLE - Schedules button menu"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        keyboard.row("scheduled posts", "self-destruct timings")
        keyboard.row("cancel", "<<back")
        
        self.bot.send_message(chat_id, "⏰ Schedules Management:", reply_markup=keyboard)

# BLUE CIRCLE - Inline Buttons (Action Buttons)
class SendInlineButtonsStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        """BLUE CIRCLE - Send inline buttons"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("schedule post", callback_data="schedule_post"))
        keyboard.row(types.InlineKeyboardButton("self-destruct", callback_data="self_destruct"))
        keyboard.row(types.InlineKeyboardButton("post now", callback_data="post_now"))
        keyboard.row(types.InlineKeyboardButton("<<back", callback_data="newpost_back"))
        
        self.bot.send_message(chat_id, "📤 Send Options:", reply_markup=keyboard)

class CancelInlineButtonsStrategy(MenuStrategy):
    def show_menu(self, chat_id: int, **kwargs):
        """BLUE CIRCLE - Cancel inline buttons"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("self-destruct", callback_data="cancel_destruct"))
        keyboard.row(types.InlineKeyboardButton("scheduled post", callback_data="cancel_scheduled"))
        keyboard.row(types.InlineKeyboardButton("<<back", callback_data="schedules_back"))
        
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
        # Show RED CIRCLE - Main inline keyboard menu
        self.menu_factory.get_menu('main_inline').show_menu(event.chat_id)
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

# Menu Factory Pattern
class MenuFactory:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.menus = {
            'main_inline': MainInlineKeyboardMenuStrategy(bot, db),  # RED
            'user_button': UserButtonMenuStrategy(bot, db),          # GREEN
            'newpost_button': NewPostButtonMenuStrategy(bot, db),    # GREEN
            'post_creation_button': PostCreationButtonMenuStrategy(bot, db), # GREEN
            'managepost_button': ManagePostButtonMenuStrategy(bot, db), # GREEN
            'schedules_button': SchedulesButtonMenuStrategy(bot, db), # GREEN
            'send_inline': SendInlineButtonsStrategy(bot, db),       # BLUE
            'cancel_inline': CancelInlineButtonsStrategy(bot, db)    # BLUE
        }
    
    def get_menu(self, menu_type: str) -> MenuStrategy:
        return self.menus.get(menu_type, self.menus['main_inline'])

# Event Handlers
class CommandEventHandler(EventHandler):
    def __init__(self, bot, db, menu_factory):
        self.bot = bot
        self.db = db
        self.menu_factory = menu_factory
        self.commands = {
            'start': StartCommandStrategy(bot, db, menu_factory),
            'help': HelpCommandStrategy(bot, db, menu_factory)
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
        self.user_states = {}  # Track user button menu states
    
    def can_handle(self, event: BotEvent) -> bool:
        return event.event_type == 'callback'
    
    def handle(self, event: BotEvent) -> bool:
        callback_data = event.data
        
        # Main inline keyboard menu callbacks (RED CIRCLE)
        if callback_data == "main_menu" or callback_data == "start":
            self._hide_button_menu(event.chat_id)
            self.menu_factory.get_menu('main_inline').show_menu(event.chat_id)
            return True
        elif callback_data == "user_menu":
            if event.user_id == BOT_OWNER_ID:
                self.menu_factory.get_menu('user_button').show_menu(event.chat_id)  # GREEN
                self.user_states[event.chat_id] = "user_menu"
            return True
        elif callback_data == "newpost":
            self.menu_factory.get_menu('newpost_button').show_menu(event.chat_id)  # GREEN
            return True
        elif callback_data == "managepost":
            self.menu_factory.get_menu('managepost_button').show_menu(event.chat_id)  # GREEN
            self.user_states[event.chat_id] = "managepost_menu"
            return True
        elif callback_data == "schedules":
            self.menu_factory.get_menu('schedules_button').show_menu(event.chat_id)  # GREEN
            self.user_states[event.chat_id] = "schedules_menu"
            return True
        
        # Channel selection callbacks
        elif callback_data.startswith('channel_'):
            channel = callback_data.replace('channel_', '')
            self.menu_factory.get_menu('post_creation_button').show_menu(event.chat_id, channel=channel)  # GREEN
            self.user_states[event.chat_id] = "post_creation_menu"
            return True
        
        # Inline button callbacks (BLUE CIRCLE)
        elif callback_data == "schedule_post":
            self.bot.send_message(event.chat_id, "📅 Schedule post format:\n\nDD/MM/YYYY HH:MM (24hr format IST)\nExample: 15/10/2025 14:30\n\nSchedule at same day if date not mentioned")
            self._hide_button_menu(event.chat_id)
            return True
        elif callback_data == "self_destruct":
            self.bot.send_message(event.chat_id, "⏰ Self-destruct format:\n\nDD/MM/YYYY HH:MM (24hr format IST)\nExample: 15/10/2025 14:30\n\nSet at same day if date not mentioned")
            self._hide_button_menu(event.chat_id)
            return True
        elif callback_data == "post_now":
            self.bot.send_message(event.chat_id, "📤 Sends the post instantly... (Feature coming soon)")
            self._hide_button_menu(event.chat_id)
            return True
        elif callback_data == "cancel_destruct":
            self.bot.send_message(event.chat_id, "❌ Self-destruct cancelled")
            self._hide_button_menu(event.chat_id)
            return True
        elif callback_data == "cancel_scheduled":
            self.bot.send_message(event.chat_id, "❌ Scheduled post cancelled")
            self._hide_button_menu(event.chat_id)
            return True
        
        return False
    
    def _hide_button_menu(self, chat_id: int):
        """Hide current button menu (GREEN CIRCLE)"""
        keyboard = types.ReplyKeyboardRemove()
        self.bot.send_message(chat_id, "Menu hidden", reply_markup=keyboard)
        if chat_id in self.user_states:
            del self.user_states[chat_id]

class MessageEventHandler(EventHandler):
    def __init__(self, bot, db, menu_factory, callback_handler):
        self.bot = bot
        self.db = db
        self.menu_factory = menu_factory
        self.callback_handler = callback_handler
    
    def can_handle(self, event: BotEvent) -> bool:
        return event.event_type == 'message'
    
    def handle(self, event: BotEvent) -> bool:
        text = event.data
        chat_id = event.chat_id
        current_state = self.callback_handler.user_states.get(chat_id, "")
        
        # Handle button menu messages (GREEN CIRCLE responses)
        if current_state == "user_menu":
            return self._handle_user_menu_buttons(event, text)
        elif current_state == "post_creation_menu":
            return self._handle_post_creation_buttons(event, text)
        elif current_state == "managepost_menu":
            return self._handle_managepost_buttons(event, text)
        elif current_state == "schedules_menu":
            return self._handle_schedules_buttons(event, text)
        
        return False
    
    def _handle_user_menu_buttons(self, event: BotEvent, text: str) -> bool:
        if text == "users":
            self._show_users_list(event.chat_id)
        elif text == "permit <user_id>":
            self.bot.send_message(event.chat_id, "Format: /permit <user_id>\nExample: /permit 123456789\n\nIgnores '-' before numbers (ex: -1234 or 1234)")
        elif text == "remove <user_id>":
            self.bot.send_message(event.chat_id, "Format: /remove <user_id>\nExample: /remove 123456789\n\nIgnores '-' before numbers (ex: -1234 or 1234)")
        elif text == "<<back":
            self.callback_handler._hide_button_menu(event.chat_id)
            self.menu_factory.get_menu('main_inline').show_menu(event.chat_id)
        return True
    
    def _handle_post_creation_buttons(self, event: BotEvent, text: str) -> bool:
        if text == "send":
            self.menu_factory.get_menu('send_inline').show_menu(event.chat_id)  # BLUE
        elif text == "cancel":
            self.bot.send_message(event.chat_id, "❌ Cancel current task")
            self.callback_handler._hide_button_menu(event.chat_id)
        elif text == "preview":
            self.bot.send_message(event.chat_id, "👁️ Shows post preview... (Feature coming soon)")
        elif text == "delete all":
            self.bot.send_message(event.chat_id, "🗑️ Delete the draft/editing post... (Feature coming soon)")
            self.callback_handler._hide_button_menu(event.chat_id)
        elif text == "<<back":
            self.callback_handler._hide_button_menu(event.chat_id)
            self.menu_factory.get_menu('main_inline').show_menu(event.chat_id)
        return True
    
    def _handle_managepost_buttons(self, event: BotEvent, text: str) -> bool:
        if text == "edit post":
            self.bot.send_message(event.chat_id, "📝 Edit a post on the channel like @controlerbot... (Feature coming soon)")
        elif text == "delete post":
            self.bot.send_message(event.chat_id, "🗑️ Delete a post on the channel... (Feature coming soon)")
        elif text == "<<back":
            self.callback_handler._hide_button_menu(event.chat_id)
            self.menu_factory.get_menu('main_inline').show_menu(event.chat_id)
        return True
    
    def _handle_schedules_buttons(self, event: BotEvent, text: str) -> bool:
        if text == "scheduled posts":
            self._show_scheduled_posts(event.chat_id)
        elif text == "self-destruct timings":
            self._show_destruct_timings(event.chat_id)
        elif text == "cancel":
            self.menu_factory.get_menu('cancel_inline').show_menu(event.chat_id)  # BLUE
        elif text == "<<back":
            self.callback_handler._hide_button_menu(event.chat_id)
            self.menu_factory.get_menu('main_inline').show_menu(event.chat_id)
        return True
    
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
        
        self.bot.send_message(chat_id, user_list)
    
    def _show_scheduled_posts(self, chat_id: int):
        posts = self.db.get_scheduled_posts()
        if posts:
            post_list = f"📋 Scheduled Posts ({len(posts)}):\n\n"
            for post in posts:
                post_list += f"Channel: {post['channel_name']}\n"
                post_list += f"Time: {post['scheduled_time']}\n"
                post_list += f"Content: {post['content'][:50]}...\n\n"
        else:
            post_list = "📋 No scheduled posts found."
        
        self.bot.send_message(chat_id, post_list)
    
    def _show_destruct_timings(self, chat_id: int):
        posts = self.db.get_scheduled_posts()
        destruct_posts = [p for p in posts if p['is_self_destruct']]
        
        if destruct_posts:
            post_list = f"⏰ Self-Destruct Posts ({len(destruct_posts)}):\n\n"
            for post in destruct_posts:
                post_list += f"Channel: {post['channel_name']}\n"
                post_list += f"Destruct Time: {post['self_destruct_time']}\n"
                post_list += f"Content: {post['content'][:50]}...\n\n"
        else:
            post_list = "⏰ No self-destruct posts found."
        
        self.bot.send_message(chat_id, post_list)

# Main Bot Handler
class BotHandlers:
    def __init__(self, database_manager):
        self.db = database_manager
        self.bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        
        # Initialize architecture
        self.menu_factory = MenuFactory(self.bot, self.db)
        self.event_dispatcher = EventDispatcher()
        
        # Create handlers with proper dependencies
        self.callback_handler = CallbackEventHandler(self.bot, self.db, self.menu_factory)
        
        # Register event handlers
        self.event_dispatcher.register_handler(CommandEventHandler(self.bot, self.db, self.menu_factory))
        self.event_dispatcher.register_handler(self.callback_handler)
        self.event_dispatcher.register_handler(MessageEventHandler(self.bot, self.db, self.menu_factory, self.callback_handler))
        
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
        
        @self.bot.message_handler(commands=['user'])
        def handle_user(message):
            if message.from_user.id != BOT_OWNER_ID:
                self.bot.reply_to(message, "Owner only.")
                return
            self.menu_factory.get_menu('user_button').show_menu(message.chat.id)
            self.callback_handler.user_states[message.chat.id] = "user_menu"
        
        @self.bot.message_handler(commands=['newpost'])
        def handle_newpost(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "Unauthorized")
                return
            self.menu_factory.get_menu('newpost_button').show_menu(message.chat.id)
        
        @self.bot.message_handler(commands=['managepost'])
        def handle_managepost(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "Unauthorized")
                return
            self.menu_factory.get_menu('managepost_button').show_menu(message.chat.id)
            self.callback_handler.user_states[message.chat.id] = "managepost_menu"
        
        @self.bot.message_handler(commands=['schedules'])
        def handle_schedules(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                self.bot.reply_to(message, "Unauthorized")
                return
            self.menu_factory.get_menu('schedules_button').show_menu(message.chat.id)
            self.callback_handler.user_states[message.chat.id] = "schedules_menu"
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            if not self.db.is_user_whitelisted(message.from_user.id):
                return
            
            event = BotEvent('message', message.from_user.id, message.chat.id, message.text, message)
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
