# 🤖 Controller Bot - Advanced Telegram Channel Manager

A powerful Telegram bot similar to @ControllerBot with advanced features, optimized scheduling, and Railway deployment support.

## ✨ Key Features

### 🎯 Core Functionality (Just like @ControllerBot)
- ✅ **Channel Posting** - Post to multiple channels with admin rights
- ✅ **Rich Formatting** - Markdown/HTML text formatting support
- ✅ **Media Support** - Photos, videos, documents with captions
- ✅ **Inline Buttons** - URL buttons with custom text
- ✅ **Link Preview Control** - Enable/disable link previews
- ✅ **Self-Destruct Messages** - Auto-delete after specified time
- ✅ **Scheduled Posts** - Post at specific date/time
- ✅ **Permission System** - Whitelist users (owner bypass)

### 🚀 Advanced Features (Beyond @ControllerBot)  
- ✅ **Smart Scheduling** - Optimized timing (no constant database polling)
- ✅ **IST Timezone Support** - dd/mm hh:mm and hh:mm formats
- ✅ **Hierarchical Menu System** - Organized inline keyboards
- ✅ **Web Dashboard** - Telegram WebApp integration
- ✅ **Railway Deployment** - Production-ready with Gunicorn
- ✅ **Database Optimization** - Minimal storage, owner bypass
- ✅ **Error Recovery** - Automatic restart on failures

## 🎛️ Menu Structure

### Main Menu (Inline Keyboard)
```
🏠 Start - Welcome and getting started
👥 User Management - Manage whitelist (owner only)  
📝 New Post - Create and send posts
📅 Schedules - View and manage scheduled tasks
📊 Dashboard - Web interface (Telegram WebApp)
```

### User Management (Button Menu)
```
👥 Users - List whitelisted users
➕ Permit <user_id> - Add user (ignores - signs)  
➖ Remove <user_id> - Remove user (ignores - signs)
⬅️ Back - Return to main menu
```

### New Post Flow
```
1. Select Channel - Choose from added channels
2. Post Editor (Button Menu):
   📤 Send - Send options
   ├── 📅 Schedule Post - Set date/time (dd/mm hh:mm)
   ├── 💣 Self-Destruct - Auto-delete timer  
   ├── 🚀 Post Now - Send immediately
   └── ⬅️ Back
   ❌ Cancel - Cancel current post
   👀 Preview - Show post preview
   🗑️ Delete All - Clear current post
   ⬅️ Back - Return to channel selection
```

### Schedules Management (Button Menu)
```
📋 Scheduled Posts - View upcoming posts
💣 Self-Destruct Timings - View auto-delete tasks
❌ Cancel - Cancel options
├── 💣 Cancel Self-Destruct - Stop auto-delete
├── 📅 Cancel Scheduled Post - Remove scheduled post  
└── ⬅️ Back
⬅️ Back - Return to main menu
```

## 📝 Commands

### Universal Commands
- `/start` - Open main menu
- `/help` - Complete help guide  
- `/addchannel @channel` - Add channel to manage
- `/channels` - View your channels

### Owner Only (via menu or direct)
- `Permit <user_id>` - Add user to whitelist
- `Remove <user_id>` - Remove user from whitelist
- `Users` - List whitelisted users

## ⏰ Time Format Support

**Full Format (with date):**
- `5/10 15:00` - October 5th at 3:00 PM IST
- `25/12 09:30` - December 25th at 9:30 AM IST

**Time Only (today/tomorrow):**  
- `15:00` - Today at 3:00 PM (or tomorrow if past)
- `09:30` - Today at 9:30 AM (or tomorrow if past)

**Notes:**
- All times in IST (Indian Standard Time)
- 24-hour format (00:00 to 23:59)
- Automatic date detection if not specified

## 🚀 Quick Start

### 1. Get Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create bot with `/newbot`
3. Save the token

### 2. Get User ID  
1. Message [@userinfobot](https://t.me/userinfobot)
2. Save your user ID number

### 3. Local Testing (Termux)
```bash
# Download project files
cd controller_bot

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env  # Edit with your settings

# Run bot
python main.py
```

### 4. Railway Deployment
1. Push code to GitHub repository
2. Connect Railway to your GitHub repo  
3. Set environment variables in Railway:
   ```
   BOT_TOKEN=your-bot-token
   BOT_OWNER_ID=your-user-id
   SECRET_KEY=random-secret-key
   WEBAPP_URL=https://your-app.railway.app
   ```
4. Deploy automatically with Railway

## ⚙️ Environment Variables

### Required
```env
BOT_TOKEN=your-bot-token-from-botfather
BOT_OWNER_ID=your-telegram-user-id
```

### Optional  
```env
WEBAPP_URL=https://your-app.railway.app
PORT=5000
SECRET_KEY=change-this-secret-key
GUNICORN_WORKERS=2
DATABASE_URL=sqlite:///controller_bot.db
```

## 📺 Channel Setup

### 1. Add Bot to Channel
1. Add bot to your Telegram channel
2. Make bot administrator with permissions:
   - ✅ Post messages
   - ✅ Edit messages  
   - ✅ Delete messages

### 2. Register Channel
1. Use `/addchannel @yourchannel`  
2. Bot validates admin status
3. Channel added to your list

### 3. Create Posts
1. Open main menu → New Post
2. Select channel
3. Send content (text, media, buttons)
4. Choose send option (now, schedule, self-destruct)

## 📊 Web Dashboard

Access: `https://your-railway-app.railway.app/dashboard`

**Features:**
- 👥 **User Management** - Add/remove whitelist users
- 📊 **Statistics** - View bot usage stats
- 🔄 **Real-time Updates** - Live data refresh
- 📱 **Telegram Integration** - Native WebApp experience

## 🛠️ Technical Architecture

### Smart Scheduling System
- **Hourly Checks** - Scans for tasks every 60 minutes
- **Near-time Mode** - Switches to 15-minute checks when tasks are close
- **Daily Scan** - 00:00 IST check for day's tasks
- **Single Timer** - No constant database polling

### Database Optimization  
- **Minimal Storage** - No message/media content stored
- **Owner Bypass** - No DB check for owner permissions
- **Efficient Queries** - Optimized for Railway container limits

### Railway Deployment
- **Nixpacks Builder** - Zero-config deployment
- **Gunicorn WSGI** - Production-grade web server
- **Health Checks** - Automatic monitoring
- **Multi-service** - Separate web and worker processes

## 📁 Project Structure

```
controller_bot/
├── main.py                    # Main bot application
├── webapp.py                  # Flask dashboard
├── config.py                  # Configuration settings
├── requirements.txt           # Dependencies
├── railway.json               # Railway deployment config
├── gunicorn_config.py         # Gunicorn settings
├── .env.example               # Environment template
├── database/
│   ├── __init__.py
│   └── models.py              # Database operations
├── handlers/  
│   ├── __init__.py
│   ├── bot_handlers.py        # Command processing
│   └── menu_handlers.py       # Menu system
├── utils/
│   ├── __init__.py
│   ├── scheduler.py           # Smart scheduling
│   └── time_parser.py         # Time parsing utilities
└── templates/
    └── dashboard.html         # Web dashboard
```

## 🎯 Usage Examples

### Create Post with Buttons
```
🎉 Welcome to our channel!

Check out these amazing resources:

Visit Website | https://example.com
Download App | https://app.com/download  
Join Community | https://t.me/community
```

### Schedule a Post
1. Create post content
2. Select "Schedule Post"  
3. Enter: `25/12 09:00` (Christmas morning)
4. Confirm - post will be sent automatically

### Self-Destruct Message  
1. Create post content
2. Select "Self-Destruct"
3. Enter: `15:30` (delete at 3:30 PM today)
4. Post sends and deletes automatically

## 🔧 Troubleshooting

### Bot Issues
- **Not responding?** Check BOT_TOKEN is correct
- **Permission errors?** Ensure bot is admin in channel
- **Commands not working?** Verify BOT_OWNER_ID is set

### Railway Issues
- **Build failing?** Check requirements.txt is present  
- **App not starting?** Verify environment variables
- **Web dashboard down?** Check health endpoint /health

### Database Issues  
- **Users not saving?** Check database permissions
- **Scheduling broken?** Restart bot to reset scheduler

## 📈 Performance

### Optimizations Implemented
- ✅ **Owner Bypass** - No DB queries for bot owner
- ✅ **Smart Scheduling** - Check only when needed (hourly → 15min)
- ✅ **Minimal Storage** - No message content in database
- ✅ **Single Timer** - One scheduler instead of constant polling
- ✅ **Railway Optimized** - Gunicorn + health checks

### Resource Usage
- **Memory** - ~50MB baseline, ~100MB under load
- **Database** - Minimal footprint, automatic cleanup
- **Network** - Efficient polling, no webhooks needed
- **CPU** - Low usage except during high posting volumes

## 🚨 Important Notes

### Security
- Never share your BOT_TOKEN publicly
- Set strong SECRET_KEY for web dashboard  
- Only whitelist trusted users
- Owner has full access bypass

### Limitations
- Railway free tier: 500 hours/month, 1GB RAM
- Telegram API: 30 messages/second limit
- SQLite: Single file database (MySQL ready for scaling)

### Best Practices  
- Test locally before deploying
- Use meaningful channel names
- Schedule posts during optimal hours
- Monitor Railway logs for errors
- Keep bot updated with latest features

## 📞 Support

### Getting Help
1. Read this complete README first
2. Check Railway deployment logs  
3. Test commands in Termux locally
4. Verify environment variables are correct

### Feature Requests
This bot replicates @ControllerBot functionality with enhancements. All core features are implemented and optimized for Railway deployment.

---

**Made with ❤️ for the Telegram community**
**Railway-optimized • Production-ready • Feature-complete**

🎯 **Your advanced channel management companion is ready!**
