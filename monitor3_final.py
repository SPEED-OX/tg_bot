#!/usr/bin/env python3
# Telegram Group Monitor - Tracks when users leave your group
import asyncio
import logging
import os
import datetime
import time
import json
import requests
import pytz
import sys
import signal
import atexit
from telethon import TelegramClient, events
from telethon.tl.types import UpdateChannelParticipant, ChannelParticipantLeft
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsRecent
from telethon.errors import FloodWaitError

# Configure logging - only to file, not console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("telegram_monitor.log")
    ]
)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = 23940372
API_HASH = '8caf9cc524474491f7f525f9d48c4b00'
# For supergroups/channels, use a negative value: -100 followed by the group ID
GROUP_ID = -1002267872993
# Bot token for notifications
BOT_TOKEN = "7667963218:AAEpXQmQXFTZL5n0xYDeStZJZ1NVQd3l0Fc"
# Whether to use the bot for notifications or send to yourself
USE_BOT = True
# Set to True to only receive notifications via bot, not in terminal
NOTIFICATIONS_ONLY_TO_BOT = True

# Path for session file
SESSION_PATH = os.path.join(os.path.expanduser('~'), 'telegram_monitor')

# Path for members cache file
MEMBERS_CACHE_FILE = os.path.join(os.path.expanduser('~'), 'telegram_members_cache.json')

# Set timezone to Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')

# Global variables to store client and group info for cleanup
client_instance = None
my_id_global = None
group_entity_global = None
stop_notification_sent = False  # Flag to prevent multiple stop notifications
login_completed = False  # Flag to track if login was successful

def get_formatted_time_and_date():
    """Get the current time and date in 12-hour format with IST timezone"""
    now = datetime.datetime.now(IST)
    time_str = now.strftime("%I:%M:%S %p [IST]")
    date_str = now.strftime("%d-%b-%Y")
    return time_str, date_str

async def get_group_invite_link(client, group_entity):
    """Get the active invite link for the group"""
    try:
        # Get full channel info which includes invite link
        full_channel = await client(GetFullChannelRequest(group_entity))
        
        # Check if there's an exported invite link
        if hasattr(full_channel.full_chat, 'exported_invite') and full_channel.full_chat.exported_invite:
            return full_channel.full_chat.exported_invite.link
        
        # If no exported invite, try to get the username-based link
        if hasattr(group_entity, 'username') and group_entity.username:
            return f"https://t.me/{group_entity.username}"
        
        # If no username, return a generic message
        return None
    except Exception as e:
        logger.error(f"Error getting invite link: {e}")
        return None

def format_group_message(group_entity, invite_link, message_type="started"):
    """Format the group monitoring message with proper formatting"""
    time_str, date_str = get_formatted_time_and_date()
    
    # Get clean group name (remove @ if present)
    group_name = group_entity.title
    if hasattr(group_entity, 'username') and group_entity.username:
        # Remove @ symbol if present in title for cleaner display
        group_name = group_name.replace('@', '')
    
    # Format the link part - brackets outside the hyperlink
    link_part = ""
    if invite_link:
        link_part = f" [<a href='{invite_link}'>LINK</a>]"
    
    # Create the message based on type
    if message_type == "started":
        status_emoji = "✅"
        action = "Leave monitoring started for :"
    elif message_type == "crashed":
        status_emoji = "❌"
        action = "Leave monitoring CRASHED for :"
    else:  # stopped
        status_emoji = "❌"
        action = "Leave monitoring stopped for :"
    
    message = f"{status_emoji} <b>{action}</b>\n🗨️<b>{group_name}</b>{link_part}\n\n⏰ <b>Time:</b> {time_str}\n🗓️ <b>Date:</b> {date_str}"
    
    return message

def format_leave_message(user_name, username, group_entity, invite_link):
    """Format the member left message with group information"""
    time_str, date_str = get_formatted_time_and_date()
    
    # Get clean group name (remove @ if present)
    group_name = group_entity.title
    if hasattr(group_entity, 'username') and group_entity.username:
        # Remove @ symbol if present in title for cleaner display
        group_name = group_name.replace('@', '')
    
    # Format the group link part - brackets outside the hyperlink
    group_link_part = ""
    if invite_link:
        group_link_part = f" [<a href='{invite_link}'>LINK</a>]"
    
    # Format user profile link
    profile_link = get_user_profile_link(username)
    
    # Create the leave message with group information
    leave_message = f"🚨 <b>MEMBER LEFT !!</b>\n🗨️<b>From: {group_name}</b>{group_link_part}\n\n👤 <b>User:</b> {user_name}\n🔗 <b>Username:</b> {username}\n🔗 <b>Profile:</b> {profile_link}\n\n⏰ <b>Time:</b> {time_str}\n🗓️ <b>Date:</b> {date_str}"
    
    return leave_message

def send_emergency_stop_notification(reason="Unknown"):
    """Send stop notification via direct API call - works even when client is disconnected"""
    global my_id_global, group_entity_global, stop_notification_sent, login_completed
    
    # Don't send notification if login wasn't completed
    if not login_completed:
        return True
    
    # Check if notification already sent
    if stop_notification_sent:
        return True
    
    try:
        if my_id_global and group_entity_global and USE_BOT:
            # Get invite link for consistent formatting
            invite_link = None
            try:
                # Try to get invite link if group has username
                if hasattr(group_entity_global, 'username') and group_entity_global.username:
                    invite_link = f"https://t.me/{group_entity_global.username}"
            except:
                pass  # If we can't get link, continue without it
            
            # Use the same formatting function for consistency
            if reason == "crash":
                stop_message = format_group_message(group_entity_global, invite_link, "crashed")
            else:
                stop_message = format_group_message(group_entity_global, invite_link, "stopped")
            
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": my_id_global.id,
                "text": stop_message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True  # Disable link preview
            }
            
            response = requests.post(url, data=payload, timeout=5)  # Reduced timeout
            if response.status_code == 200:
                stop_notification_sent = True  # Mark as sent
                print(f"✅ Stop notification sent! (Reason: {reason})")
                return True
            else:
                stop_notification_sent = True  # Mark as sent even if failed to prevent retries
                return False
    except Exception:
        # Suppress error messages during signal handling, just mark as sent
        stop_notification_sent = True
        return False

def signal_handler(signum, frame):
    """Handle system signals like SIGTERM, SIGINT"""
    global stop_notification_sent, login_completed
    
    # Show the exact message format requested
    print("^C")
    print(f"🛑 Received signal {signum}. Sending stop notification...")
    
    # Don't send notification if login wasn't completed
    if not login_completed:
        print("🛑 Login process interrupted!")
        print("Exiting...")
        sys.exit(0)
    
    if not stop_notification_sent:
        # Use a more robust notification method and suppress error messages
        try:
            success = send_emergency_stop_notification("signal")
            if not success:
                # If notification fails, still mark as sent to prevent duplicate attempts
                stop_notification_sent = True
        except:
            # Suppress any errors during notification
            stop_notification_sent = True
    
    print("Exiting...")
    sys.exit(0)

def exit_handler():
    """Handle normal program exit - only if signal handler didn't run"""
    global stop_notification_sent, login_completed
    
    # Don't run if signal handler already processed the exit
    if stop_notification_sent or not login_completed:
        return
    
    # This should only run for normal program exits, not signal interrupts
    try:
        send_emergency_stop_notification("exit")
    except:
        pass  # Suppress errors during exit

# Register signal handlers for various termination signals
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
if hasattr(signal, 'SIGHUP'):
    signal.signal(signal.SIGHUP, signal_handler)  # Hangup signal (terminal closed)
if hasattr(signal, 'SIGQUIT'):
    signal.signal(signal.SIGQUIT, signal_handler)  # Quit signal

# Register exit handler
atexit.register(exit_handler)

def send_bot_message(chat_id, text):
    """Send a message using the Telegram Bot API"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True  # Disable link preview
        }
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            logger.error(f"Failed to send bot message: {response.status_code} - {response.text}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error sending bot message: {e}")
        return False

def get_user_profile_link(username):
    """Generate a profile link for a user"""
    if username and username != "No username":
        # Remove @ if present and create t.me link as hyperlink
        clean_username = username.replace("@", "")
        return f"<a href='http://t.me/{clean_username}'>LINK</a>"
    else:
        return "No profile link available"

async def get_all_participants(client, channel):
    """Get all participants from a channel/group"""
    all_participants = []
    
    # Get initial list of participants
    try:
        participants = await client(GetParticipantsRequest(
            channel, ChannelParticipantsRecent(), 0, 200, hash=0
        ))
        
        # Add the participants to our list
        all_participants.extend(participants.users)
        
        # Get more participants
        logger.info(f"Retrieved {len(all_participants)} participants")
        
        return all_participants
    except Exception as e:
        logger.error(f"Error getting participants: {e}")
        return []

async def save_current_members(client, channel):
    """Save current channel members to a file for comparison"""
    try:
        # Get all participants
        participants = await get_all_participants(client, channel)
        
        # Create a dictionary with user IDs and names
        members_dict = {}
        for user in participants:
            full_name = f"{user.first_name} {user.last_name if user.last_name else ''}"
            username = f"@{user.username}" if user.username else "No username"
            members_dict[str(user.id)] = {"name": full_name, "username": username}
        
        # Save to file
        with open(MEMBERS_CACHE_FILE, 'w') as f:
            json.dump(members_dict, f)
        
        logger.info(f"Saved {len(members_dict)} members to cache file")
        return members_dict
    except Exception as e:
        logger.error(f"Error saving members: {e}")
        return {}

async def load_cached_members():
    """Load cached member list from file"""
    try:
        if os.path.exists(MEMBERS_CACHE_FILE):
            with open(MEMBERS_CACHE_FILE, 'r') as f:
                members = json.load(f)
            logger.info(f"Loaded {len(members)} members from cache file")
            return members
        else:
            logger.info("No members cache file found")
            return {}
    except Exception as e:
        logger.error(f"Error loading members cache: {e}")
        return {}

async def check_for_left_members(client, channel, old_members, current_members, my_user_id):
    """Compare old and current member lists to find who left"""
    try:
        left_members = []
        
        # Check for members in old list but not in current list
        for user_id, user_data in old_members.items():
            if user_id not in current_members:
                left_members.append((user_id, user_data))
        
        # Send notifications for left members
        for user_id, user_data in left_members:
            # Get invite link for the leave message
            invite_link = None
            try:
                invite_link = await get_group_invite_link(client, channel)
            except:
                pass
            
            # Use the new formatting function for leave messages
            leave_message = format_leave_message(
                user_data['name'], 
                user_data['username'], 
                channel, 
                invite_link
            )
            
            time_str, date_str = get_formatted_time_and_date()
            logger.info(f"User {user_data['name']} ({user_data['username']}) left the group at {time_str} on {date_str}")
            
            if not NOTIFICATIONS_ONLY_TO_BOT:
                print(leave_message)
            
            # Send notification
            if USE_BOT:
                send_bot_message(my_user_id, leave_message)
            else:
                await client.send_message('me', leave_message, link_preview=False)
        
        return left_members
    except Exception as e:
        logger.error(f"Error checking for left members: {e}")
        return []

async def send_stop_notification():
    """Send stop notification when monitoring stops"""
    global my_id_global, group_entity_global, client_instance, stop_notification_sent, login_completed
    
    # Don't send notification if login wasn't completed
    if not login_completed:
        print("⚠️  Login not completed, skipping stop notification")
        return
    
    # Check if notification already sent
    if stop_notification_sent:
        print("⚠️  Stop notification already sent, skipping duplicate")
        return
    
    try:
        if my_id_global and group_entity_global:
            # Get invite link
            invite_link = None
            try:
                invite_link = await get_group_invite_link(client_instance, group_entity_global)
            except:
                pass
            
            # Format the stop message using the same function as start message
            stop_message = format_group_message(group_entity_global, invite_link, "stopped")
            
            print("Sending stop notification...")
            
            if USE_BOT:
                success = send_bot_message(my_id_global.id, stop_message)
                if success:
                    stop_notification_sent = True  # Mark as sent
                    print("✅ Stop notification sent via bot.")
                else:
                    print("❌ Failed to send stop notification via bot.")
            
            # Also try to send via client if available
            if client_instance and not client_instance.is_connected():
                try:
                    await client_instance.connect()
                except:
                    pass
            
            if client_instance and client_instance.is_connected():
                try:
                    await client_instance.send_message('me', stop_message, link_preview=False)
                    if not stop_notification_sent:  # Only mark if not already sent via bot
                        stop_notification_sent = True
                    print("✅ Stop notification sent via client.")
                except Exception as e:
                    print(f"❌ Failed to send via client: {e}")
            
    except Exception as e:
        logger.error(f"Error sending stop notification: {e}")
        print(f"❌ Error sending stop notification: {e}")

async def main():
    global client_instance, my_id_global, group_entity_global, login_completed
    
    # Connect to Telegram
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    client_instance = client
    
    try:
        print("🔄 Connecting to Telegram...")
        await client.start(phone=lambda: input("Please enter phone number to login Telegram: "))
        
        if not await client.is_user_authorized():
            logger.info("You need to log in first!")
            phone = input("Please enter phone number to login Telegram: ")
            await client.send_code_request(phone)
            await client.sign_in(phone, input("Enter the code: "))
        
        # Login completed successfully
        login_completed = True
        
        my_id = await client.get_me()
        my_id_global = my_id
        logger.info(f"Successfully logged in as {my_id.first_name} (ID: {my_id.id})")
        
    except KeyboardInterrupt:
        # Handle Ctrl+C during login phase
        print("^C")
        print("🛑 Received signal 2. Sending stop notification...")
        print("🛑 Login process interrupted!")
        print("Exiting...")
        await client.disconnect()
        return
    except Exception as e:
        logger.error(f"Login error: {e}")
        print(f"❌ Login error: {e}")
        await client.disconnect()
        return
    
    try:
        group_entity = await client.get_entity(GROUP_ID)
        group_entity_global = group_entity
        logger.info(f"Monitoring group: {group_entity.title}")
        
        # Get invite link for startup message
        invite_link = await get_group_invite_link(client, group_entity)
        
        # Send startup notification with formatted message
        startup_message = format_group_message(group_entity, invite_link, "started")
        
        if USE_BOT:
            send_bot_message(my_id.id, startup_message)
        else:
            await client.send_message('me', startup_message, link_preview=False)
        
        # Initial member list
        initial_members = await save_current_members(client, group_entity)
        
        # Register event handlers
        @client.on(events.ChatAction)
        async def handle_chat_action(event):
            if event.user_left and event.chat_id == GROUP_ID:
                try:
                    user = await client.get_entity(event.user_id)
                    username = f"@{user.username}" if user.username else "No username"
                    user_name = f"{user.first_name} {user.last_name if user.last_name else ''}"
                    
                    # Get invite link for the leave message
                    invite_link = None
                    try:
                        invite_link = await get_group_invite_link(client, group_entity)
                    except:
                        pass
                    
                    # Use the new formatting function for leave messages
                    leave_message = format_leave_message(user_name, username, group_entity, invite_link)
                    
                    time_str, date_str = get_formatted_time_and_date()
                    logger.info(f"User {user.first_name} left the group at {time_str} on {date_str}")
                    
                    if not NOTIFICATIONS_ONLY_TO_BOT:
                        print(leave_message)
                    
                    # Send notification
                    if USE_BOT:
                        send_bot_message(my_id.id, leave_message)
                    else:
                        await client.send_message('me', leave_message, link_preview=False)
                    
                except Exception as e:
                    logger.error(f"Error processing leave event: {e}")
        
        @client.on(events.Raw)
        async def raw_update_handler(event):
            if isinstance(event, UpdateChannelParticipant):
                if event.channel_id == abs(GROUP_ID) % 10**10:  # Remove the -100 prefix for comparison
                    try:
                        if event.prev_participant and not event.new_participant:
                            # User left or was removed
                            user_id = event.prev_participant.user_id
                            user = await client.get_entity(user_id)
                            username = f"@{user.username}" if user.username else "No username"
                            user_name = f"{user.first_name} {user.last_name if user.last_name else ''}"
                            
                            # Get invite link for the leave message
                            invite_link = None
                            try:
                                invite_link = await get_group_invite_link(client, group_entity)
                            except:
                                pass
                            
                            # Use the new formatting function for leave messages
                            leave_message = format_leave_message(user_name, username, group_entity, invite_link)
                            
                            time_str, date_str = get_formatted_time_and_date()
                            logger.info(f"User {user.first_name} left the group at {time_str} on {date_str}")
                            
                            if not NOTIFICATIONS_ONLY_TO_BOT:
                                print(leave_message)
                            
                            # Send notification
                            if USE_BOT:
                                send_bot_message(my_id.id, leave_message)
                            else:
                                await client.send_message('me', leave_message, link_preview=False)
                    except Exception as e:
                        logger.error(f"Error in raw update handler: {e}")
        
        # Keep the script running and periodically check for member changes
        logger.info("Monitoring has started. Press Ctrl+C to stop.")
        
        # SHOW STATUS IN TERMUX - Always show basic status regardless of NOTIFICATIONS_ONLY_TO_BOT
        print("=" * 60)
        print("🔄 TELEGRAM GROUP MONITOR ACTIVE")
        print("=" * 60)
        print(f"👥 Group: {group_entity.title}")
        print(f"👤 Logged in as: {my_id.first_name}")
        print(f"📊 Monitoring {len(initial_members)} members")
        time_str, date_str = get_formatted_time_and_date()
        print(f"⏰ Started at: {time_str} on {date_str}")
        print(f"🤖 Bot notifications: {'Enabled' if USE_BOT else 'Disabled'}")
        print("=" * 60)
        print("✅ Monitoring is now ACTIVE and RUNNING!")
        print("🔍 Watching for members leaving the group...")
        print("📱 You will receive notifications when someone leaves")
        print("⚠️  Press Ctrl+C to stop monitoring")
        print("=" * 60)
        
        check_interval = 15  # Reduced from 45 to 15 seconds for faster detection
        last_check_time = time.time()
        status_update_interval = 180  # Reduced from 300 to 180 seconds (3 minutes)
        last_status_time = time.time()
        
        try:
            # Main monitoring loop
            while True:
                await asyncio.sleep(2)  # Reduced from 5 to 2 seconds for faster event processing
                
                current_time = time.time()
                
                # Periodic status update - show that script is still running
                if current_time - last_status_time >= status_update_interval:
                    current_time_str, current_date_str = get_formatted_time_and_date()
                    print(f"📊 Status Update: {current_time_str} - Monitoring active, watching {group_entity.title}")
                    last_status_time = current_time
                
                # Periodic full member check
                if current_time - last_check_time >= check_interval:
                    logger.info("Performing periodic member check...")
                    print(f"🔄 Checking member list... ({get_formatted_time_and_date()[0]})")
                    last_check_time = current_time
                    
                    # Load previous members
                    old_members = await load_cached_members()
                    
                    # Get current members
                    current_members = await save_current_members(client, group_entity)
                    
                    # Compare and find who left
                    left_members = await check_for_left_members(client, group_entity, old_members, current_members, my_id.id)
                    
                    if left_members:
                        logger.info(f"Periodic check found {len(left_members)} members who left")
                        print(f"⚠️  Periodic check found {len(left_members)} members who left")
                    else:
                        logger.info("Periodic check completed, no members left")
                        print("✅ Member check completed - no changes detected")
                
        except KeyboardInterrupt:
            # Show the exact message format for Ctrl+C
            print("^C")
            print("🛑 Received signal 2. Sending stop notification...")
            
            # Send stop notification with better error handling
            try:
                if not stop_notification_sent:
                    success = send_emergency_stop_notification("signal")
                    if not success:
                        stop_notification_sent = True  # Prevent duplicate attempts
            except Exception:
                stop_notification_sent = True  # Suppress errors and prevent duplicates
            
            print("Exiting...")
            return  # Exit the function cleanly
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            print(f"❌ Unexpected error: {e}")
            
            # Send stop notification on unexpected error too
            try:
                await send_stop_notification()
                await asyncio.sleep(2)
            except Exception as stop_error:
                print(f"❌ Error sending stop notification: {stop_error}")
                # Try emergency notification as backup
                send_emergency_stop_notification("crash")
            
            if isinstance(e, FloodWaitError):
                print(f"Telegram rate limit hit. Please wait {e.seconds} seconds.")
                # Wait and then restart
                time.sleep(e.seconds)
                await main()
    except ValueError as e:
        logger.error(f"Error getting group: {e}")
        print("\nThere was an error finding your group. Let's try to list your groups to find the correct ID:")
        
        # List the user's groups and channels
        dialogs = await client.get_dialogs()
        print("\nYour available groups/channels:")
        for i, dialog in enumerate(dialogs):
            if dialog.is_group or dialog.is_channel:
                print(f"{i+1}. {dialog.name} (ID: {dialog.id})")
        
        print("\nPlease update the GROUP_ID in the script with the correct ID from the list above.")
        print("For supergroups/channels, the ID should be negative and start with -100...")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("^C")
        print("🛑 Received signal 2. Sending stop notification...")
        print("🛑 Program interrupted by user")
        print("Exiting...")
    except SystemExit:
        pass
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        
        # Send crash notification only if login was completed
        if login_completed and not stop_notification_sent:
            try:
                send_emergency_stop_notification("crash")
            except:
                pass  # Suppress errors during crash notification
        
        print("Restarting in 10 seconds...")
        time.sleep(10)
        os.execv(sys.executable, [sys.executable] + sys.argv)
