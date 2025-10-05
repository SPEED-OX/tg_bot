"""
ChatAudit Bot - Bot Command Handlers with Updated Commands
"""
import telebot
from telebot import types
from telebot.types import BotCommand
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BOT_TOKEN, BOT_OWNER_ID, BOT_NAME, IST, WEBAPP_URL
from handlers.menu_handlers import MenuHandler

class BotHandlers:
    def __init__(self, database_manager):
        self.db = database_manager
        self.bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
        self.menu_handler = MenuHandler(self.bot, self.db)
        self.user_states = {}
        
        # Register handlers and update commands
        self.register_handlers()
        
    def set_bot_commands(self):
        """Set updated bot commands with proper descriptions"""
        try:
            commands = [
                BotCommand("start", "🏠 Open main menu with inline keyboards"),
                BotCommand("help", "📖 Complete help guide with all features"),
                BotCommand("addchannel", "📺 Add a channel to manage (e.g., /addchannel @mychannel)"),
                BotCommand("channels", "📋 View your added channels list"),
            ]
            
            self.bot.set_my_commands(commands)
            print("✅ Bot commands updated successfully")
            
        except Exception as e:
            print(f"⚠️ Failed to update bot commands: {e}")
    
    def register_handlers(self):
        """Register all bot command handlers"""
        
        # Update bot commands first
        self.set_bot_commands()
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            user_id = message.from_user.id
            username = message.from_user.username
            first_name = message.from_user.first_name
            
            # Check if user is authorized
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, 
                    "❌ You are not authorized to use this bot. Contact the administrator.")
                return
            
            # Update user info in database
            self.db.add_user_to_whitelist(user_id, username, first_name)
            
            # Send welcome message with main menu
            welcome_text = f"""🤖 **Welcome to {BOT_NAME}**

Hello {first_name}! You are authorized to use this bot.

**Available Features:**
• **Inline Keyboards** - Quick navigation menus
• **User Management** - Whitelist control (owner)
• **Channel Management** - Add and manage channels
• **Post Scheduling** - Schedule posts with IST timezone
• **Web Dashboard** - Advanced management interface

**Current Time (IST):** {datetime.now(IST).strftime('%d/%m %H:%M')}

Use the buttons below to navigate:"""

            self.menu_handler.show_main_menu(message.chat.id, welcome_text)

        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            user_id = message.from_user.id
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "❌ You are not authorized to use this bot.")
                return
            
            help_text = f"""📖 **{BOT_NAME} - Complete Guide**

**🎛️ Menu System:**
• **Inline Keyboards** - Floating buttons above messages
• **Button Menus** - Keyboard replacement menus
• **Mixed Navigation** - Both types for different functions

**🏠 Main Menu (Inline Keyboard):**
• **🏠 Start** - Getting started guide and welcome
• **👥 User** - User management menu (owner only)
• **📝 New Post** - Channel selection and post creation
• **📅 Schedules** - View and manage scheduled tasks
• **📊 Dashboard** - Open web interface

**👥 User Management (Button Menu - Owner Only):**
• **👥 Users** - List all whitelisted users with details
• **➕ Permit <user_id>** - Add user to whitelist
• **➖ Remove <user_id>** - Remove user from whitelist
• **⬅️ Back** - Return to main menu

**📝 Post Creation Flow:**
1. Select **New Post** → Choose from your channels
2. Send content (text, media, buttons)
3. Choose posting option (now, schedule, self-destruct)

**📅 Schedule Management (Button Menu):**
• **📋 Scheduled Posts** - View upcoming posts
• **💣 Self-Destruct Timings** - View auto-delete tasks
• **❌ Cancel** - Cancel scheduled tasks
• **⬅️ Back** - Return to main menu

**📺 Channel Commands:**
• `/addchannel @channelname` - Add channel to manage
• `/channels` - View your added channels

**🕐 Time Format:**
• **dd/mm hh:mm** - Specific date (5/10 15:00 = Oct 5, 3:00 PM)
• **hh:mm** - Same day (15:00 = 3:00 PM today)
• All times in **IST (Indian Standard Time)**

**📊 Web Dashboard:**
Advanced management interface with statistics and controls.

**💡 Navigation Tips:**
• Use **inline buttons** for quick actions
• Use **button menus** for detailed operations
• **/start** always returns to main menu
• **/help** shows this complete guide

**Current Time (IST):** {datetime.now(IST).strftime('%d/%m/%Y %H:%M')}

Ready to manage your channels! 🚀"""

            self.bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

        @self.bot.message_handler(commands=['addchannel'])
        def handle_add_channel(message):
            user_id = message.from_user.id
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "❌ You are not authorized to use this bot.")
                return
            
            try:
                args = message.text.split()
                if len(args) != 2:
                    help_text = """📺 **Add Channel - Help**

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

**Note:** Channel username must start with @"""
                    
                    self.bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
                    return
                
                channel_username = args[1].replace('@', '')
                channel_id = hash(channel_username) % 1000000
                
                self.db.add_channel(channel_id, f"@{channel_username}", channel_username, user_id)
                self.bot.reply_to(message, 
                    f"✅ Channel @{channel_username} added successfully!\n\n"
                    f"You can now create posts for this channel using /start → New Post.")
                
            except Exception as e:
                self.bot.reply_to(message, f"❌ Error adding channel: {str(e)}")

        @self.bot.message_handler(commands=['channels'])
        def handle_list_channels(message):
            user_id = message.from_user.id
            
            if not self.db.is_user_whitelisted(user_id):
                self.bot.reply_to(message, "❌ You are not authorized to use this bot.")
                return
            
            channels = self.db.get_user_channels(user_id)
            
            if not channels:
                text = """📺 **Your Channels**

📭 You haven't added any channels yet.

**To add a channel:**
1. Add me as admin to your channel
2. Use: `/addchannel @yourchannel`

**Example:**
`/addchannel @mynewschannel`"""
            else:
                text = "📺 **Your Channels:**\n\n"
                for i, channel in enumerate(channels, 1):
                    channel_name = channel['name'] or 'Unknown'
                    text += f"{i}. **{channel_name}**\n"
                    text += f"   Username: {channel['username']}\n"
                    text += f"   Added: {channel['added_date'][:10]}\n\n"
                text += "💡 Use /start → New Post to create content for these channels."
            
            self.bot.send_message(message.chat.id, text, parse_mode='Markdown')

        # Temporary command to force update (remove after testing)
        @self.bot.message_handler(commands=['updatecommands'])
        def update_commands_manually(message):
            if message.from_user.id == BOT_OWNER_ID:
                self.set_bot_commands()
                self.bot.reply_to(message, "✅ Bot commands updated manually!")
            else:
                self.bot.reply_to(message, "❌ Owner only command")

        # Register callback query handler
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback_query(call):
            self.menu_handler.handle_callback_query(call)
            
        # Register message handler for menu responses
        @self.bot.message_handler(func=lambda message: True)
        def handle_messages(message):
            self.menu_handler.handle_messages(message)
