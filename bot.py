from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, OWNER_ID, WEBAPP_URL
import database

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (
        "👋 Welcome! I can help you schedule & post to channels like ControllerBot.\n\n"
        "Use /help to see available commands."
    )
    keyboard = [[InlineKeyboardButton("📊 Dashboard", web_app={"url": f"{WEBAPP_URL}/dashboard"})]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/permit <user_id> - Allow user (owner only)\n"
        "/remove <user_id> - Remove user (owner only)\n"
        "/users - Show whitelisted users\n"
    )
    await update.message.reply_text(text)

# /permit
async def permit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Only owner can use this command.")
    if not context.args:
        return await update.message.reply_text("Usage: /permit <user_id>")
    uid = int(context.args[0])
    database.add_user(uid)
    await update.message.reply_text(f"✅ User {uid} permitted.")

# /remove
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Only owner can use this command.")
    if not context.args:
        return await update.message.reply_text("Usage: /remove <user_id>")
    uid = int(context.args[0])
    database.remove_user(uid)
    await update.message.reply_text(f"❌ User {uid} removed.")

# /users
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_ids = database.get_users()
    if not user_ids:
        return await update.message.reply_text("No permitted users yet.")
    await update.message.reply_text("👥 Permitted users:\n" + "\n".join(map(str, user_ids)))

def run_bot():
    database.init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("permit", permit))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("users", users))
    app.run_polling()