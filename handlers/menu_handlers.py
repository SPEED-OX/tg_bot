"""
ChatAudit Bot - Menu System Handler
Complete inline keyboard menu system
"""
from telebot import types
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BOT_OWNER_ID, BOT_NAME, IST, WEBAPP_URL

class MenuHandler:
    def __init__(self, bot, database_manager):
        self.bot = bot
        self.db = database_manager
        self.user_states = {}
    
    def show_main_menu(self, chat_id, text="🏠 **Main Menu**"):
        """Show the main inline keyboard menu"""
        keyboard = types.InlineKeyboardMarkup()
        
        # Main menu buttons
        keyboard.row(types.InlineKeyboardButton("🏠 Start", callback_data="menu_start"))
        
        # User management for owner only
        if chat_id == BOT_OWNER_ID:
            keyboard.row(types.InlineKeyboardButton("👥 User", callback_data="menu_user"))
        
        keyboard.row(types.InlineKeyboardButton("📝 New Post", callback_data="menu_new_post"))
        keyboard.row(types.InlineKeyboardButton("📅 Schedules", callback_data="menu_schedules"))
        
        # Dashboard button if URL is configured
        if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
            dashboard_url = f"{WEBAPP_URL}/dashboard"
            try:
                keyboard.row(types.InlineKeyboardButton("📊 Dashboard", 
                    web_app=types.WebApp(dashboard_url)))
            except:
                # Fallback if WebApp is not supported
                pass
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')

    def show_user_menu(self, chat_id):
        """Show user management button menu"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.row("👥 Users", "➕ Permit <user_id>")
        keyboard.row("➖ Remove <user_id>", "⬅️ Back")
        
        text = f"""👥 **User Management Menu**

**Available Actions:**
• **Users** - List all whitelisted users
• **Permit <user_id>** - Add user to whitelist (Example: Permit 123456789)
• **Remove <user_id>** - Remove user from whitelist (Example: Remove 123456789)
• **Back** - Return to main menu

**Note:** User IDs can be with or without minus signs (123456789 or -123456789)

**Current Time (IST):** {datetime.now(IST).strftime('%d/%m %H:%M')}"""
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')

    def show_schedules_menu(self, chat_id):
        """Show schedules button menu"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.row("📋 Scheduled Posts", "💣 Self-Destruct Timings")
        keyboard.row("❌ Cancel", "⬅️ Back")
        
        text = f"""📅 **Schedules Menu**

**Available Actions:**
• **Scheduled Posts** - View all scheduled posts and timings
• **Self-Destruct Timings** - View all self-destruct posts and timings
• **Cancel** - Cancel scheduled or self-destruct tasks
• **Back** - Return to main menu

**Current Time (IST):** {datetime.now(IST).strftime('%d/%m %H:%M')}"""
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')

    def show_cancel_menu(self, chat_id):
        """Show cancel submenu with inline buttons"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("💣 Self-Destruct", callback_data="cancel_self_destruct"))
        keyboard.row(types.InlineKeyboardButton("📅 Scheduled Post", callback_data="cancel_scheduled"))
        keyboard.row(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_schedules"))
        
        text = """❌ **Cancel Tasks**

Choose task type to cancel:"""
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')

    def handle_callback_query(self, call):
        """Handle all callback queries from inline keyboards"""
        user_id = call.from_user.id
        
        if not self.db.is_user_whitelisted(user_id):
            self.bot.answer_callback_query(call.id, "❌ Not authorized")
            return
        
        data = call.data
        
        if data == "menu_start":
            self.show_main_menu(call.message.chat.id, "🏠 **Welcome back to the main menu!**")
            
        elif data == "menu_user" and user_id == BOT_OWNER_ID:
            self.show_user_menu(call.message.chat.id)
            
        elif data == "menu_new_post":
            self.show_channel_selection(call.message.chat.id)
            
        elif data == "menu_schedules":
            self.show_schedules_menu(call.message.chat.id)
            
        elif data == "cancel_self_destruct":
            self.bot.send_message(call.message.chat.id, 
                "💣 Self-destruct task cancellation coming soon!")
                
        elif data == "cancel_scheduled":
            self.bot.send_message(call.message.chat.id, 
                "📅 Scheduled post cancellation coming soon!")
        
        self.bot.answer_callback_query(call.id)

    def show_channel_selection(self, chat_id):
        """Show channel selection for new posts"""
        channels = self.db.get_user_channels(chat_id)
        
        if not channels:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_start"))
            
            text = """📝 **New Post**

❌ No channels added yet.

Use /addchannel @channelname to add channels first.

**Example:** /addchannel @mychannel"""
            
            self.bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')
            return
        
        keyboard = types.InlineKeyboardMarkup()
        
        for channel in channels:
            keyboard.row(types.InlineKeyboardButton(f"{channel['name']}", 
                callback_data=f"select_channel_{channel['id']}"))
        
        keyboard.row(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_start"))
        
        text = """📝 **New Post - Select Channel**

Choose a channel to post in:"""
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='Markdown')

    def handle_messages(self, message):
        """Handle button menu messages and regular text"""
        user_id = message.from_user.id
        text = message.text.strip() if message.text else ""
        
        if not self.db.is_user_whitelisted(user_id):
            self.bot.reply_to(message, "❌ You are not authorized to use this bot.")
            return
        
        # Handle button menu commands
        if text == "👥 Users" and user_id == BOT_OWNER_ID:
            self.handle_list_users(message)
            
        elif text.startswith("➕ Permit") and user_id == BOT_OWNER_ID:
            self.handle_permit_user(message)
            
        elif text.startswith("➖ Remove") and user_id == BOT_OWNER_ID:
            self.handle_remove_user(message)
            
        elif text == "⬅️ Back":
            self.show_main_menu(message.chat.id)
            
        elif text == "📋 Scheduled Posts":
            self.handle_show_scheduled_posts(message)
            
        elif text == "💣 Self-Destruct Timings":
            self.handle_show_self_destruct_posts(message)
            
        elif text == "❌ Cancel":
            self.show_cancel_menu(message.chat.id)
            
        else:
            # Handle as regular message or unknown command
            if text and not text.startswith('/'):
                self.bot.reply_to(message, 
                    "📝 Message received. Use the menu buttons or /help for available commands.")

    def handle_list_users(self, message):
        """Handle listing whitelisted users"""
        users = self.db.get_whitelisted_users()
        
        if not users:
            self.bot.reply_to(message, "📋 No whitelisted users found.")
            return
        
        user_list = f"👥 **Whitelisted Users ({len(users)}):**\n\n"
        for user in users:
            display_name = f"@{user[1]}" if user[1] else user[2] or "Unknown"
            user_list += f"• **{display_name}** (ID: `{user[0]}`)\n"
        
        self.bot.send_message(message.chat.id, user_list, parse_mode='Markdown')

    def handle_permit_user(self, message):
        """Handle adding user to whitelist"""
        try:
            parts = message.text.split()
            if len(parts) < 2:
                self.bot.reply_to(message, 
                    "**Usage:** Permit <user_id>\n**Example:** Permit 123456789")
                return
            
            user_id_str = parts[1].replace('-', '')
            user_id = int(user_id_str)
            
            self.db.add_user_to_whitelist(user_id)
            self.bot.reply_to(message, f"✅ User `{user_id}` added to whitelist!")
            
        except ValueError:
            self.bot.reply_to(message, "❌ Invalid user ID. Please provide a numeric user ID.")
        except Exception as e:
            self.bot.reply_to(message, f"❌ Error: {str(e)}")

    def handle_remove_user(self, message):
        """Handle removing user from whitelist"""
        try:
            parts = message.text.split()
            if len(parts) < 2:
                self.bot.reply_to(message, 
                    "**Usage:** Remove <user_id>\n**Example:** Remove 123456789")
                return
            
            user_id_str = parts[1].replace('-', '')
            user_id = int(user_id_str)
            
            if user_id == BOT_OWNER_ID:
                self.bot.reply_to(message, "❌ Cannot remove bot owner from whitelist!")
                return
            
            self.db.remove_user_from_whitelist(user_id)
            self.bot.reply_to(message, f"✅ User `{user_id}` removed from whitelist!")
            
        except ValueError:
            self.bot.reply_to(message, "❌ Invalid user ID. Please provide a numeric user ID.")
        except Exception as e:
            self.bot.reply_to(message, f"❌ Error: {str(e)}")

    def handle_show_scheduled_posts(self, message):
        """Show scheduled posts"""
        # For now, return placeholder
        self.bot.reply_to(message, 
            "📋 **Scheduled Posts**\n\nNo scheduled posts found.\n\nScheduled post feature coming soon!")

    def handle_show_self_destruct_posts(self, message):
        """Show self-destruct posts"""  
        # For now, return placeholder
        self.bot.reply_to(message, 
            "💣 **Self-Destruct Posts**\n\nNo self-destruct posts found.\n\nSelf-destruct feature coming soon!")
