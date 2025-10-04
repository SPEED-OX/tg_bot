# 🚀 Controller Bot - Railway Deployment Guide

## Quick Deploy (5 Minutes)

### Step 1: Get Required Information
1. **Bot Token**: Message [@BotFather](https://t.me/BotFather) → `/newbot` → copy token
2. **Your User ID**: Message [@userinfobot](https://t.me/userinfobot) → copy ID number

### Step 2: Prepare Repository
```bash
# Upload to GitHub (if not already)
git init
git add .
git commit -m "Initial Controller Bot commit"  
git remote add origin https://github.com/yourusername/controller-bot.git
git push -u origin main
```

### Step 3: Deploy to Railway
1. Go to [Railway.app](https://railway.app) and sign up
2. Click **"New Project"** → **"Deploy from GitHub repo"**  
3. Connect your GitHub account if needed
4. Select your repository
5. Railway will auto-detect Python and start building

### Step 4: Set Environment Variables
In Railway dashboard → **Variables** tab, add:

```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_OWNER_ID=987654321  
SECRET_KEY=my-super-secret-key-123
```

### Step 5: Get Your App URL
1. Go to **Settings** → **Domains** in Railway
2. Click **"Generate Domain"**
3. Copy the URL (e.g., `https://controller-bot-production-abc123.railway.app`)
4. Add this variable:
```
WEBAPP_URL=https://your-generated-domain.railway.app
```

### Step 6: Test Your Bot
1. Find your bot on Telegram by username
2. Send `/start` - should show main menu
3. Try `/help` for full guide
4. Add a channel with `/addchannel @yourchannel`

**🎉 Your bot is now live!**

## Local Testing (Termux/Linux)

### Setup Environment
```bash
# Navigate to project
cd controller_bot

# Install Python dependencies
pip install -r requirements.txt

# Setup environment file
cp .env.example .env

# Edit environment variables
nano .env
```

### Edit .env File
```env
BOT_TOKEN=your-actual-bot-token
BOT_OWNER_ID=your-user-id-number
WEBAPP_URL=http://localhost:5000
PORT=5000
SECRET_KEY=test-secret-key
```

### Run Bot Locally
```bash
# Start bot
python main.py

# In another terminal (optional) - start web dashboard  
python webapp.py
```

### Test Locally
- Bot should show "Controller Bot Started!" message
- Send `/start` to your bot
- Web dashboard: `http://localhost:5000/dashboard`

## Railway Configuration Details

### railway.json Explained
```json
{
  "build": {
    "builder": "NIXPACKS"  // Auto-detects Python, installs deps
  },
  "deploy": {
    "numReplicas": 1,      // Single instance (free tier)
    "restartPolicyType": "ON_FAILURE",  // Auto-restart on crash
    "restartPolicyMaxRetries": 10       // Max restart attempts
  },
  "services": {
    "web": {
      "startCommand": "gunicorn webapp:app --workers 2 --bind 0.0.0.0:$PORT",
      "healthcheckPath": "/health"       // Health monitoring
    },
    "worker": {
      "startCommand": "python main.py"  // Bot process
    }
  }
}
```

### Why Gunicorn?
- **Production Ready**: Handles multiple users simultaneously
- **Stable**: Won't crash under load
- **Railway Optimized**: Recommended by Railway docs
- **Auto-restart**: Recovers from worker crashes

## Environment Variables Guide

### Required Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | From @BotFather | `123:ABCdef...` |
| `BOT_OWNER_ID` | Your Telegram user ID | `987654321` |

### Optional Variables  
| Variable | Default | Description |
|----------|---------|-------------|
| `WEBAPP_URL` | Railway domain | Dashboard URL |
| `PORT` | `5000` | Web server port |
| `SECRET_KEY` | Generated | Flask session key |
| `GUNICORN_WORKERS` | `2` | Web server workers |

### Database Variables (Future)
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | MySQL connection string |

## Channel Setup Guide

### 1. Prepare Your Channel
1. Create Telegram channel (public or private)
2. Make sure you're the owner/admin

### 2. Add Bot as Admin
1. Go to your channel
2. Channel Info → Administrators → Add Administrator
3. Search for your bot username
4. Grant these permissions:
   - ✅ **Post Messages** (required)
   - ✅ **Edit Messages** (required)
   - ✅ **Delete Messages** (required)  
   - ❌ Other permissions (optional)

### 3. Register Channel with Bot
```
/addchannel @yourchannel
```

Bot will:
- ✅ Verify it exists
- ✅ Check admin permissions  
- ✅ Add to your channel list
- ❌ Show error if issues

### 4. Test Posting
1. Open bot main menu → **New Post**
2. Select your channel
3. Send test message: "Hello from Controller Bot! 🤖"
4. Choose **Post Now**
5. Check your channel for the message

## Troubleshooting

### Common Railway Issues

**Build Fails with Python Error**
```bash
# Solution: Check requirements.txt format
pyTelegramBotAPI==4.21.0
Flask==3.0.3
# No trailing spaces or empty lines
```

**App Starts But Bot Doesn't Respond**  
- ✅ Check `BOT_TOKEN` is correct (no spaces)
- ✅ Verify `BOT_OWNER_ID` is your user ID  
- ✅ Check Railway logs for errors

**Web Dashboard Shows 404**
- ✅ Ensure `WEBAPP_URL` matches Railway domain
- ✅ Check web service is running in Railway
- ✅ Visit `/health` endpoint to test

### Common Bot Issues

**Permission Denied Errors**
```
❌ I'm not an admin in @yourchannel
```
**Solution**: Add bot as admin with post permissions

**Bot Commands Not Working**
```
❌ You're not authorized to use this bot
```  
**Solution**: Check `BOT_OWNER_ID` matches your user ID

**Scheduling Not Working**
- Bot creates schedule but doesn't post
- **Solution**: Restart bot in Railway (resets scheduler)

### Railway Logs

**View Logs:**
1. Railway dashboard → Your project
2. **Deployments** tab → Click latest deployment  
3. **Logs** section shows real-time output

**Common Log Messages:**
```bash
✅ Controller Bot initialized successfully
🤖 Controller Bot Started!  
📞 Received signal 15, shutting down gracefully...
❌ Bot error (attempt 1/5): [error details]
```

## Advanced Configuration

### Custom Domain (Pro Plan)
1. Railway Pro plan required
2. Settings → Domains → **Custom Domain**
3. Update `WEBAPP_URL` environment variable

### Database Scaling  
```env
# Future MySQL support
DATABASE_URL=mysql://user:pass@host:port/db
```

### Multiple Bots
1. Create separate Railway projects
2. Use different `BOT_TOKEN` for each
3. Share same codebase

### Monitoring
- Railway provides built-in monitoring
- Health checks at `/health` endpoint
- View metrics in Railway dashboard

## Performance Optimization

### Railway Free Tier Limits
- **RAM**: 512MB (bot uses ~100MB)
- **Hours**: 500/month (always-on needs Pro)  
- **Storage**: 1GB (SQLite uses minimal space)

### Optimization Features
- ✅ **Owner Bypass** - No DB queries for owner
- ✅ **Smart Scheduling** - Hourly checks, not constant polling
- ✅ **Minimal Storage** - No message content in database
- ✅ **Efficient Queries** - Optimized for container limits

### Scaling Tips
- Use Railway Pro for 24/7 uptime
- Consider MySQL for high user counts  
- Monitor memory usage in Railway dashboard
- Schedule posts during off-peak hours

## Security Best Practices

### Environment Security
- ❌ **Never commit .env to git**
- ✅ Use Railway environment variables
- ✅ Set strong `SECRET_KEY`
- ✅ Rotate tokens periodically

### Bot Security  
- ✅ Only whitelist trusted users
- ✅ Owner has full access (be careful)
- ✅ Monitor Railway logs for suspicious activity
- ✅ Use private channels when possible

### Database Security
- ✅ SQLite file protected by Railway
- ✅ No sensitive data stored (messages not saved)
- ✅ Auto-cleanup of old data
- ✅ Backup capability through Railway

## Next Steps

### After Successful Deployment
1. ✅ Add your main channels
2. ✅ Whitelist trusted team members  
3. ✅ Test all features (posting, scheduling, self-destruct)
4. ✅ Bookmark web dashboard
5. ✅ Schedule your first post!

### Growing Your Setup  
- Add multiple channels for different purposes
- Use scheduling for consistent posting
- Set self-destruct for temporary announcements
- Monitor usage via web dashboard
- Consider Railway Pro for 24/7 operation

---

**🎯 Your Controller Bot is now production-ready on Railway!**

**Need help?** Check the main README.md for detailed usage instructions.
