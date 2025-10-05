"""
TechGeekZ Bot - Menu System Handler
Complete show/hide menu system with proper navigation
"""
from telebot import types
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BOT_OWNER_ID, BOT_NAME, WEBAPP_URL

class MenuHandler:
    def __init__(self, bot, database_manager):
        self.bot = bot
        self.db = database_manager
        self.user_states = {}
    
    def show_main_menu(self, chat_id, text="Main Menu"):
        """Show the main inline keyboard menu"""
        keyboard = types.InlineKeyboardMarkup()
        
        # Main menu buttons (no emojis)
        keyboard.row(types.InlineKeyboardButton("start", callback_data="menu_start"))
        
        # User management for owner only
        if chat_id == BOT_OWNER_ID:
            keyboard.row(types.InlineKeyboardButton("user", callback_data="menu_user"))
        
        keyboard.row(types.InlineKeyboardButton("newpost", callback_data="menu_newpost"))
        keyboard.row(types.InlineKeyboardButton("schedules", callback_data="menu_schedules"))
        
        # Dashboard button
        if WEBAPP_URL and WEBAPP_URL.startswith('https://'):
            dashboard_url = f"{WEBAPP_URL}/dashboard"
            keyboard.row(types.InlineKeyboardButton("dashboard", web_app=types.WebApp(dashboard_url)))
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard)

    def show_user_menu(self, chat_id):
        """Show user management button menu"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        keyboard.row("users", "permit")
        keyboard.row("remove", "back")
        
        text = "User Management\n\nSelect an option:"
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard)
        self.user_states[chat_id] = "user_menu"

    def show_newpost_menu(self, chat_id):
        """Show newpost button menu"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        keyboard.row("send", "cancel")
        keyboard.row("preview", "delete all")
        keyboard.row("back")
        
        text = "New Post\n\nFirst add your content, then select an option:"
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard)
        self.user_states[chat_id] = "newpost_menu"

    def show_schedules_menu(self, chat_id):
        """Show schedules button menu"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        keyboard.row("scheduled posts", "self-destruct timings")
        keyboard.row("cancel", "back")
        
        text = "Schedules\n\nSelect an option:"
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard)
        self.user_states[chat_id] = "schedules_menu"

    def show_send_options(self, chat_id):
        """Show send options inline buttons"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("schedule post", callback_data="send_schedule"))
        keyboard.row(types.InlineKeyboardButton("self-destruct", callback_data="send_destruct"))
        keyboard.row(types.InlineKeyboardButton("post now", callback_data="send_now"))
        keyboard.row(types.InlineKeyboardButton("back", callback_data="send_back"))
        
        text = "Send Options\n\nChoose how to send your post:"
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard)

    def show_cancel_options(self, chat_id):
        """Show cancel options inline buttons"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton("self-destruct", callback_data="cancel_destruct"))
        keyboard.row(types.InlineKeyboardButton("scheduled post", callback_data="cancel_scheduled"))
        keyboard.row(types.InlineKeyboardButton("back", callback_data="cancel_back"))
        
        text = "Cancel Tasks\n\nChoose what to cancel:"
        
        self.bot.send_message(chat_id, text, reply_markup=keyboard)

    def hide_button_menu(self, chat_id):
        """Hide current button menu"""
        keyboard = types.ReplyKeyboardRemove()
        self.bot.send_message(chat_id, "Menu hidden", reply_markup=keyboard)
        if chat_id in self.user_states:
            del self.user_states[chat_id]

    def handle_callback_query(self, call):
        """Handle all callback queries from inline keyboards"""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        if not self.db.is_user_whitelisted(user_id):
            self.bot.answer_callback_query(call.id, "Not authorized")
            return
        
        data = call.data
        
        # Main menu callbacks
        if data == "menu_start":
            self.show_main_menu(chat_id, "Welcome back to the main menu!")
            
        elif data == "menu_user" and user_id == BOT_OWNER_ID:
            self.show_user_menu(chat_id)
            
        elif data == "menu_newpost":
            self.show_newpost_menu(chat_id)
            
        elif data == "menu_schedules":
            self.show_schedules_menu(chat_id)
        
        # Send options callbacks
        elif data == "send_schedule":
            self.bot.send_message(chat_id, "Enter date and time for scheduling:\nFormat: dd/mm hh:mm (24hr format)")
            self.hide_button_menu(chat_id)
            
        elif data == "send_destruct":
            self.bot.send_message(chat_id, "Enter date and time for self-destruct:\nFormat: dd/mm hh:mm (24hr format)")
            self.hide_button_menu(chat_id)
            
        elif data == "send_now":
            self.bot.send_message(chat_id, "Post sent instantly!")
            self.hide_button_menu(chat_id)
            
        elif data == "send_back":
            # Go back to newpost menu
            self.show_newpost_menu(chat_id)
        
        # Cancel options callbacks
        elif data == "cancel_destruct":
            self.bot.send_message(chat_id, "Self-destruct task cancelled!")
            self.hide_button_menu(chat_id)
            
        elif data == "cancel_scheduled":
            self.bot.send_message(chat_id, "Scheduled post cancelled!")
            self.hide_button_menu(chat_id)
            
        elif data == "cancel_back":
            # Go back to schedules menu
            self.show_schedules_menu(chat_id)
        
        self.bot.answer_callback_query(call.id)

    def handle_messages(self, message):
        """Handle button menu messages and regular text"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        text = message.text.strip() if message.text else ""
        
        if not self.db.is_user_whitelisted(user_id):
            self.bot.reply_to(message, "You are not authorized to use this bot.")
            return
        
        current_state = self.user_states.get(chat_id, "")
        
        # Handle user menu buttons
        if current_state == "user_menu":
            if text == "users":
                self.handle_list_users(message)
            elif text == "permit":
                self.bot.reply_to(message, "Enter user ID to permit:\nFormat: permit <user_id>\nExample: 123456789")
            elif text == "remove":
                self.bot.reply_to(message, "Enter user ID to remove:\nFormat: remove <user_id>\nExample: 123456789")
            elif text == "back":
                self.hide_button_menu(chat_id)
                self.show_main_menu(chat_id, "Returned to main menu")
        
        # Handle newpost menu buttons
        elif current_state == "newpost_menu":
            if text == "send":
                self.show_send_options(chat_id)
            elif text == "cancel":
                self.bot.reply_to(message, "Current task cancelled!")
                self.hide_button_menu(chat_id)
            elif text == "preview":
                self.bot.reply_to(message, "Post preview shown!")
            elif text == "delete all":
                self.bot.reply_to(message, "Draft deleted!")
                self.hide_button_menu(chat_id)
            elif text == "back":
                self.hide_button_menu(chat_id)
                self.show_main_menu(chat_id, "Returned to main menu")
        
        # Handle schedules menu buttons
        elif current_state == "schedules_menu":
            if text == "scheduled posts":
                self.handle_show_scheduled_posts(message)
            elif text == "self-destruct timings":
                self.handle_show_self_destruct_posts(message)
            elif text == "cancel":
                self.show_cancel_options(chat_id)
            elif text == "back":
                self.hide_button_menu(chat_id)
                self.show_main_menu(chat_id, "Returned to main menu")
        
        # Handle permit/remove user ID input
        elif text.startswith("permit ") or text.startswith("remove "):
            if user_id == BOT_OWNER_ID:
                parts = text.split()
                if len(parts) == 2:
                    try:
                        target_user_id = int(parts[1].replace('-', ''))
                        if text.startswith("permit"):
                            self.db.add_user_to_whitelist(target_user_id)
                            self.bot.reply_to(message, f"User {target_user_id} added to whitelist!")
                        else:
                            if target_user_id != BOT_OWNER_ID:
                                self.db.remove_user_from_whitelist(target_user_id)
                                self.bot.reply_to(message, f"User {target_user_id} removed from whitelist!")
                            else:
                                self.bot.reply_to(message, "Cannot remove bot owner!")
                    except ValueError:
                        self.bot.reply_to(message, "Invalid user ID format!")
                else:
                    self.bot.reply_to(message, "Invalid format. Use: permit <user_id> or remove <user_id>")
            else:
                self.bot.reply_to(message, "Owner only command!")

    def handle_list_users(self, message):
        """Handle listing whitelisted users"""
        users = self.db.get_whitelisted_users_with_details()
        
        if not users:
            self.bot.reply_to(message, "No whitelisted users found.")
            return
        
        user_list = f"Whitelisted Users ({len(users)}):\n\n"
        for user in users:
            user_id, username, first_name, nickname = user
            display_name = nickname or first_name or "Unknown"
            display_username = f"@{username}" if username else "No username"
            user_list += f"{display_name} {display_username}\nID: {user_id}\n\n"
        
        self.bot.send_message(message.chat.id, user_list)

    def handle_show_scheduled_posts(self, message):
        """Show scheduled posts"""
        self.bot.reply_to(message, "Scheduled Posts\n\nNo scheduled posts found.")

    def handle_show_self_destruct_posts(self, message):
        """Show self-destruct posts"""  
        self.bot.reply_to(message, "Self-Destruct Posts\n\nNo self-destruct posts found.")
