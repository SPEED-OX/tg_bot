"""
TechGeekZ Bot - Advanced Handler Architecture
Fixed message formats and proper inline keyboard menu
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
from typing import Dict, List, Callable, Optional
from enum import Enum

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', 0))
BOT_NAME = "TechGeekZ Bot"
WEBAPP_URL = os.getenv('WEBAPP_URL', '')
IST = timezone(timedelta(hours=5, minutes=30))

logger = logging.getLogger(__name__)

def format_current_time():
    """Format current time for /start message"""
    return datetime.now(IST).strftime('%d/%m/%Y | %H:%M')

def get_dashboard_status():
    """Get dashboard status"""
    return "Online" if WEBAPP_URL else "Offline"

def get_owner_username():
    """Get owner username - customize this"""
    return "@Owner"  # Replace with actual owner telegram username

class UserRole(Enum):
    """User role enumeration"""
    OWNER = "owner"
    USER = "user"
    UNAUTHORIZED = "unauthorized"

@dataclass
class UserContext:
    """User context data"""
    user_id: int
    username: str
    first_name: str
    role: UserRole
    chat_id: int

class Command(ABC):
    """Abstract base command class"""
    
    @abstractmethod
    def execute(self, context: UserContext, message=None, **kwargs) -> bool:
        pass
    
    @abstractmethod
    def can_execute(self, context: UserContext) -> bool:
        pass

class CallbackHandler(ABC):
    """Abstract callback handler"""
    
    @abstractmethod
    def handle(self, context: UserContext, data: str, chat_id: int) -> bool:
        pass
    
    @abstractmethod
    def can_handle(self, data: str) -> bool:
        pass

class MenuRenderer:
    """Advanced menu rendering system"""
    
    @staticmethod
    def create_keyboard(buttons: List[List[dict]]) -> types.InlineKeyboardMarkup:
        """Create inline keyboard from button configuration"""
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

class CommandRegistry:
    """Command registry using Factory pattern"""
    
    def __init__(self):
        self._commands: Dict[str, Command] = {}
    
    def register(self, command_name: str, command: Command):
        """Register a command"""
        self._commands[command_name] = command
        logger.info(f"Registered command: {command_name}")
    
    def get_command(self, command_name: str) -> Optional[Command]:
        """Get command by name"""
        return self._commands.get(command_name)
    
    def get_all_commands(self) -> List[str]:
        """Get all registered command names"""
        return list(self._commands.keys())

class CallbackRegistry:
    """Callback handler registry"""
    
    def __init__(self):
        self._handlers: List[CallbackHandler] = []
    
    def register(self, handler: CallbackHandler):
        """Register callback handler"""
        self._handlers.append(handler)
        logger.info(f"Registered callback handler: {handler.__class__.__name__}")
    
    def handle_callback(self, context: UserContext, data: str, chat_id: int) -> bool:
        """Handle callback with appropriate handler"""
        for handler in self._handlers:
            if handler.can_handle(data):
                return handler.handle(context, data, chat_id)
        return False

# Command Implementations
class StartCommand(Command):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
    
    def execute(self, context: UserContext, message=None, **kwargs) -> bool:
        if not self.can_execute(context):
            self.bot.reply_to(message, "You are not authorized to use this bot.")
            return False
        
        # Update user in database
        self.db.add_user_to_whitelist(context.user_id, context.username, context.first_name)
        
        # EXACT /start welcome message format as requested
        start_message = f"""Welcome to {BOT_NAME}

Hello @{context.username}! What new are we thinking today..

Owner: {get_owner_username()}
Dashboard: {get_dashboard_status()}
Time: {format_current_time()}

Bot is active. Send /help for all commands"""

        self.bot.send_message(context.chat_id, start_message)
        
        # Show INLINE KEYBOARD MENU (not just text "Main Menu")
        self._show_main_menu(context.chat_id)
        return True
    
    def can_execute(self, context: UserContext) -> bool:
        return context.role != UserRole.UNAUTHORIZED
    
    def _show_main_menu(self, chat_id: int):
        """Show proper inline keyboard menu (not text)"""
        buttons = [
            [{'text': 'start', 'type': 'callback', 'data': 'start'}],
        ]
        
        if chat_id == BOT_OWNER_ID:
            buttons.append([{'text': 'user', 'type': 'callback', 'data': 'user_menu'}])
        
        buttons.extend([
            [{'text': 'newpost', 'type': 'callback', 'data': 'newpost'}],
            [{'text': 'managepost', 'type': 'callback', 'data': 'managepost'}],
            [{'text': 'schedules', 'type': 'callback', 'data': 'schedules'}],
        ])
        
        if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
            dashboard_url = f"{WEBAPP_URL}/dashboard"
            buttons.append([{'text': 'dashboard', 'type': 'url', 'url': dashboard_url}])
        
        keyboard = MenuRenderer.create_keyboard(buttons)
        
        # Send EMPTY message with inline keyboard (no "Main Menu" text)
        self.bot.send_message(chat_id, "⚡", reply_markup=keyboard)

class HelpCommand(Command):
    def __init__(self, bot):
        self.bot = bot
    
    def execute(self, context: UserContext, message=None, **kwargs) -> bool:
        if not self.can_execute(context):
            self.bot.reply_to(message, "You are not authorized.")
            return False
        
        help_text = f"""{BOT_NAME} - Available Commands

/start - start the bot
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
        
        self.bot.send_message(context.chat_id, help_text)
        return True
    
    def can_execute(self, context: UserContext) -> bool:
        return context.role != UserRole.UNAUTHORIZED

class DashboardCommand(Command):
    def __init__(self, bot):
        self.bot = bot
    
    def execute(self, context: UserContext, message=None, **kwargs) -> bool:
        if not self.can_execute(context):
            self.bot.reply_to(message, "You are not authorized.")
            return False
        
        if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
            dashboard_url = f"{WEBAPP_URL}/dashboard"
            buttons = [[{'text': 'Go to Dashboard', 'type': 'url', 'url': dashboard_url}]]
            keyboard = MenuRenderer.create_keyboard(buttons)
            self.bot.send_message(context.chat_id, "🌐 Open your dashboard here:", reply_markup=keyboard)
        else:
            self.bot.reply_to(message, "Dashboard URL not configured.")
        return True
    
    def can_execute(self, context: UserContext) -> bool:
        return context.role != UserRole.UNAUTHORIZED

class UserManagementCommand(Command):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
    
    def execute(self, context: UserContext, message=None, **kwargs) -> bool:
        if not self.can_execute(context):
            self.bot.reply_to(message, "Owner only.")
            return False
        
        self._show_user_menu(context.chat_id)
        return True
    
    def can_execute(self, context: UserContext) -> bool:
        return context.role == UserRole.OWNER
    
    def _show_user_menu(self, chat_id: int):
        """Show user management menu"""
        buttons = [
            [{'text': 'users', 'type': 'callback', 'data': 'users_list'}],
            [{'text': 'permit <user_id>', 'type': 'callback', 'data': 'permit_user'}],
            [{'text': 'remove <user_id>', 'type': 'callback', 'data': 'remove_user'}],
            [{'text': '<<back', 'type': 'callback', 'data': 'main_menu'}],
        ]
        
        keyboard = MenuRenderer.create_keyboard(buttons)
        self.bot.send_message(chat_id, "👥 User Management", reply_markup=keyboard)

# Callback Handlers
class MainMenuCallbackHandler(CallbackHandler):
    def __init__(self, bot, command_registry):
        self.bot = bot
        self.command_registry = command_registry
        self.menu_actions = {
            'main_menu': self._show_main_menu,
            'start': self._show_main_menu,
            'user_menu': self._show_user_menu,
            'newpost': self._show_newpost_menu,
            'managepost': self._show_managepost_menu,
            'schedules': self._show_schedules_menu,
        }
    
    def handle(self, context: UserContext, data: str, chat_id: int) -> bool:
        action = self.menu_actions.get(data)
        if action:
            action(context, chat_id)
            return True
        return False
    
    def can_handle(self, data: str) -> bool:
        return data in self.menu_actions
    
    def _show_main_menu(self, context: UserContext, chat_id: int):
        """Show main menu - proper inline keyboard"""
        buttons = [
            [{'text': 'start', 'type': 'callback', 'data': 'start'}],
        ]
        
        if chat_id == BOT_OWNER_ID:
            buttons.append([{'text': 'user', 'type': 'callback', 'data': 'user_menu'}])
        
        buttons.extend([
            [{'text': 'newpost', 'type': 'callback', 'data': 'newpost'}],
            [{'text': 'managepost', 'type': 'callback', 'data': 'managepost'}],
            [{'text': 'schedules', 'type': 'callback', 'data': 'schedules'}],
        ])
        
        if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
            dashboard_url = f"{WEBAPP_URL}/dashboard"
            buttons.append([{'text': 'dashboard', 'type': 'url', 'url': dashboard_url}])
        
        keyboard = MenuRenderer.create_keyboard(buttons)
        # Send just the keyboard without "Main Menu" text
        self.bot.send_message(chat_id, "⚡", reply_markup=keyboard)
    
    def _show_user_menu(self, context: UserContext, chat_id: int):
        if context.role != UserRole.OWNER:
            return
        
        user_cmd = self.command_registry.get_command('user')
        if user_cmd:
            user_cmd._show_user_menu(chat_id)
    
    def _show_newpost_menu(self, context: UserContext, chat_id: int):
        buttons = [
            [{'text': 'Channel 1', 'type': 'callback', 'data': 'channel_1'}],
            [{'text': 'Channel 2', 'type': 'callback', 'data': 'channel_2'}],
            [{'text': 'Channel 3', 'type': 'callback', 'data': 'channel_3'}],
            [{'text': '<<back', 'type': 'callback', 'data': 'main_menu'}],
        ]
        
        keyboard = MenuRenderer.create_keyboard(buttons)
        self.bot.send_message(chat_id, "📢 Select channel to post in:", reply_markup=keyboard)
    
    def _show_managepost_menu(self, context: UserContext, chat_id: int):
        buttons = [
            [{'text': 'edit post', 'type': 'callback', 'data': 'edit_existing'}],
            [{'text': 'delete post', 'type': 'callback', 'data': 'delete_existing'}],
            [{'text': '<<back', 'type': 'callback', 'data': 'main_menu'}],
        ]
        
        keyboard = MenuRenderer.create_keyboard(buttons)
        self.bot.send_message(chat_id, "⚙️ Manage Posts:", reply_markup=keyboard)
    
    def _show_schedules_menu(self, context: UserContext, chat_id: int):
        buttons = [
            [{'text': 'scheduled posts', 'type': 'callback', 'data': 'scheduled_posts'}],
            [{'text': 'self-destruct timings', 'type': 'callback', 'data': 'destruct_timings'}],
            [{'text': 'cancel', 'type': 'callback', 'data': 'cancel_menu'}],
            [{'text': '<<back', 'type': 'callback', 'data': 'main_menu'}],
        ]
        
        keyboard = MenuRenderer.create_keyboard(buttons)
        self.bot.send_message(chat_id, "⏰ Schedules Management:", reply_markup=keyboard)

class UserManagementCallbackHandler(CallbackHandler):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.user_actions = {
            'users_list': self._show_users_list,
            'permit_user': self._show_permit_format,
            'remove_user': self._show_remove_format,
        }
    
    def handle(self, context: UserContext, data: str, chat_id: int) -> bool:
        if context.role != UserRole.OWNER:
            return False
        
        action = self.user_actions.get(data)
        if action:
            action(chat_id)
            return True
        return False
    
    def can_handle(self, data: str) -> bool:
        return data in self.user_actions
    
    def _show_users_list(self, chat_id: int):
        users = self.db.get_whitelisted_users()
        user_list = f"👥 Whitelisted Users ({len(users)}):\n\n"
        
        for user in users:
            user_id, username, first_name = user[0], user[1], user[2]
            name = first_name or "Unknown"
            uname = f"@{username}" if username else "No username"
            user_list += f"{name} {uname}\nID: {user_id}\n\n"
        
        buttons = [[{'text': '<<back', 'type': 'callback', 'data': 'user_menu'}]]
        keyboard = MenuRenderer.create_keyboard(buttons)
        self.bot.send_message(chat_id, user_list, reply_markup=keyboard)
    
    def _show_permit_format(self, chat_id: int):
        self.bot.send_message(chat_id, "Format: /permit <user_id>\nExample: /permit 123456789\n\nIgnores '-' before numbers (ex: -1234 or 1234)")
    
    def _show_remove_format(self, chat_id: int):
        self.bot.send_message(chat_id, "Format: /remove <user_id>\nExample: /remove 123456789\n\nIgnores '-' before numbers (ex: -1234 or 1234)")

class BotHandlers:
    """Advanced bot handler with dependency injection and command pattern"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        
        # Initialize registries
        self.command_registry = CommandRegistry()
        self.callback_registry = CallbackRegistry()
        
        # Setup bot
        self._setup_commands()
        self._register_commands()
        self._register_callbacks()
        self._register_handlers()
    
    def _setup_commands(self):
        """Setup bot commands with Telegram"""
        logger.info("🔄 Setting up bot commands...")
        
        try:
            self.bot.delete_my_commands()
            logger.info("🗑️ Old commands deleted")
            time.sleep(3)
        except:
            logger.warning("⚠️ No old commands to delete")
        
        commands = [
            BotCommand("start", "start the bot"),
            BotCommand("user", "user settings"),
            BotCommand("newpost", "create posts"),
            BotCommand("managepost", "manage posts"),
            BotCommand("editpost", "edit existing post"),
            BotCommand("deletepost", "delete existing post"),
            BotCommand("schedules", "schedule settings"),
            BotCommand("dashboard", "web dashboard"),
            BotCommand("permit", "add user to whitelist"),
            BotCommand("remove", "remove user from whitelist"),
        ]
        
        self.bot.set_my_commands(commands)
        logger.info("✅ Bot commands updated successfully!")
    
    def _register_commands(self):
        """Register all command handlers"""
        self.command_registry.register('start', StartCommand(self.bot, self.db))
        self.command_registry.register('help', HelpCommand(self.bot))
        self.command_registry.register('dashboard', DashboardCommand(self.bot))
        self.command_registry.register('user', UserManagementCommand(self.bot, self.db))
        
        logger.info(f"Registered {len(self.command_registry.get_all_commands())} commands")
    
    def _register_callbacks(self):
        """Register all callback handlers"""
        self.callback_registry.register(MainMenuCallbackHandler(self.bot, self.command_registry))
        self.callback_registry.register(UserManagementCallbackHandler(self.bot, self.db))
        
        logger.info("Callback handlers registered")
    
    def _get_user_context(self, message) -> UserContext:
        """Get user context from message"""
        user_id = message.from_user.id
        username = message.from_user.username or "User"
        first_name = message.from_user.first_name or "Unknown"
        
        # Determine role
        if user_id == BOT_OWNER_ID:
            role = UserRole.OWNER
        elif self.db.is_user_whitelisted(user_id):
            role = UserRole.USER
        else:
            role = UserRole.UNAUTHORIZED
        
        return UserContext(
            user_id=user_id,
            username=username,
            first_name=first_name,
            role=role,
            chat_id=message.chat.id
        )
    
    def _register_handlers(self):
        """Register Telegram handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            context = self._get_user_context(message)
            command = self.command_registry.get_command('start')
            if command:
                command.execute(context, message)
        
        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            context = self._get_user_context(message)
            command = self.command_registry.get_command('help')
            if command:
                command.execute(context, message)
        
        @self.bot.message_handler(commands=['dashboard'])
        def handle_dashboard(message):
            context = self._get_user_context(message)
            command = self.command_registry.get_command('dashboard')
            if command:
                command.execute(context, message)
        
        @self.bot.message_handler(commands=['user'])
        def handle_user(message):
            context = self._get_user_context(message)
            command = self.command_registry.get_command('user')
            if command:
                command.execute(context, message)
        
        # Add missing command handlers
        @self.bot.message_handler(commands=['newpost'])
        def handle_newpost(message):
            context = self._get_user_context(message)
            if context.role == UserRole.UNAUTHORIZED:
                self.bot.reply_to(message, "Unauthorized")
                return
            
            # Show newpost channel selection
            buttons = [
                [{'text': 'Channel 1', 'type': 'callback', 'data': 'channel_1'}],
                [{'text': 'Channel 2', 'type': 'callback', 'data': 'channel_2'}],
                [{'text': 'Channel 3', 'type': 'callback', 'data': 'channel_3'}],
            ]
            keyboard = MenuRenderer.create_keyboard(buttons)
            self.bot.send_message(context.chat_id, "📢 Select channel to post in:", reply_markup=keyboard)
        
        @self.bot.message_handler(commands=['managepost'])
        def handle_managepost(message):
            context = self._get_user_context(message)
            if context.role == UserRole.UNAUTHORIZED:
                self.bot.reply_to(message, "Unauthorized")
                return
            
            buttons = [
                [{'text': 'edit post', 'type': 'callback', 'data': 'edit_existing'}],
                [{'text': 'delete post', 'type': 'callback', 'data': 'delete_existing'}],
            ]
            keyboard = MenuRenderer.create_keyboard(buttons)
            self.bot.send_message(context.chat_id, "⚙️ Manage Posts:", reply_markup=keyboard)
        
        @self.bot.message_handler(commands=['editpost'])
        def handle_editpost(message):
            context = self._get_user_context(message)
            if context.role == UserRole.UNAUTHORIZED:
                self.bot.reply_to(message, "Unauthorized")
                return
            self.bot.send_message(context.chat_id, "📝 Edit post feature:\n\nForward the message you want to edit, or use /managepost menu for advanced options.")
        
        @self.bot.message_handler(commands=['deletepost'])
        def handle_deletepost(message):
            context = self._get_user_context(message)
            if context.role == UserRole.UNAUTHORIZED:
                self.bot.reply_to(message, "Unauthorized")
                return
            self.bot.send_message(context.chat_id, "🗑️ Delete post feature:\n\nForward the message you want to delete, or use /managepost menu for advanced options.")
        
        @self.bot.message_handler(commands=['schedules'])
        def handle_schedules(message):
            context = self._get_user_context(message)
            if context.role == UserRole.UNAUTHORIZED:
                self.bot.reply_to(message, "Unauthorized")
                return
            
            buttons = [
                [{'text': 'scheduled posts', 'type': 'callback', 'data': 'scheduled_posts'}],
