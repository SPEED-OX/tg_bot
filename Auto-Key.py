import logging
import qrcode
import io
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

BOT_TOKEN = "8235792024:AAEkJYtbbid8RupgHNJdhF1Dnqif3pEP4gQ"
ADMIN_ID = 5686136730
UPI_ID = "@omni"
UPI_NAME = "Prince Kaushik"
Channel_File_Name = "@KaushikCracking"
# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

wait_Kaushik_pay = {}
Kaushik = set()
Kaushik_input_admin = {}
admin_Kaushik_user = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    Kaushik.add(update.message.from_user.id)

    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.first_name

    msg = f"Hey 👋, {username}! \n\nUpi: {UPI_ID}\nName: ({UPI_NAME})\n/buy to purchase a plan."

    keyboard = [
        [KeyboardButton("Contact Us")]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        msg,
        reply_markup=reply_markup
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    Kaushik.add(update.message.from_user.id)
    if not context.args:
        keyboard = [
            [InlineKeyboardButton("User", callback_data="buy_user"),
             InlineKeyboardButton("Reseller", callback_data="buy_reseller")]
        ]
        await update.message.reply_text("Are you a User or Reseller?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    duration = context.args[0]
    plans = {"1": 200, "3": 300, "7": 600, "30": 1300}
    user_id = update.message.from_user.id

    if duration not in plans:
        await update.message.reply_text("Invalid duration. Use: /buy 1 | /buy 3 | /buy 7 | /buy 30")
        return

    if user_id in wait_Kaushik_pay:
        await update.message.reply_text("⚠️ You already have a pending payment. Wait for it to expire or complete it.")
        return

    amount = plans[duration]
    upi_link = f"upi://pay?pa={UPI_ID}&am={amount}&cu=INR"
    img = qrcode.make(upi_link)
    bio = io.BytesIO()
    bio.name = "qr.png"
    img.save(bio, "PNG")
    bio.seek(0)

    msg = await update.message.reply_photo(
        photo=bio,
        caption=f"Pay ₹{amount}\nSend transaction ID within 3 minutes.\nUPI: {UPI_ID} ({UPI_NAME})\n\nSend in format: <transaction_id> <amount> <user/reseller>"
    )

    wait_Kaushik_pay[user_id] = {"amount": amount, "type": "user", "msg_id": msg.message_id, "duration": duration}

    async def expire_qr(uid, message):
        await asyncio.sleep(180)
        if uid in wait_Kaushik_pay:
            await message.edit_caption("⚠️ Payment expired after 3 minutes.")
            del wait_Kaushik_pay[uid]

    asyncio.create_task(expire_qr(user_id, msg))

async def reseller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    Kaushik.add(update.message.from_user.id)
    msg = f"""You selected Reseller.
👑 Reseller Panel
💰 Balance: ₹0

Available Packs:
Pay ₹2000 → Get ₹5000 Balance
Pay ₹3000 → Get ₹7000 Balance
Pay ₹4000 → Get ₹10000 Balance
Pay ₹5000 → Get ₹15000 Balance

Use /buybalance <amount> to purchase a pack."""
    await update.message.reply_text(msg)

async def buybalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    Kaushik.add(update.message.from_user.id)
    if not context.args:
        await update.message.reply_text("Usage: /buybalance <amount>\nExample: /buybalance 2000")
        return

    try:
        amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Amount must be a number.\nExample: /buybalance 2000")
        return

    if amount not in [2000, 3000, 4000, 5000]:
        await update.message.reply_text("Invalid pack. Available: 2000, 3000, 4000, 5000")
        return

    user_id = update.message.from_user.id
    if user_id in wait_Kaushik_pay:
        await update.message.reply_text("⚠️ You already have a pending payment. Wait for it to expire or complete it.")
        return

    upi_link = f"upi://pay?pa={UPI_ID}&am={amount}&cu=INR"
    img = qrcode.make(upi_link)
    bio = io.BytesIO()
    bio.name = "qr.png"
    img.save(bio, "PNG")
    bio.seek(0)

    msg = await update.message.reply_photo(
        photo=bio,
        caption=f"Pay ₹{amount} via UPI and send transaction ID within 3 minutes.\nUPI: {UPI_ID} ({UPI_NAME})"
    )

    wait_Kaushik_pay[user_id] = {"amount": amount, "type": "reseller", "msg_id": msg.message_id, "duration": "reseller"}

    async def expire_qr(uid, message):
        await asyncio.sleep(180)
        if uid in wait_Kaushik_pay:
            await message.edit_caption("⚠️ Payment expired after 3 minutes.")
            del wait_Kaushik_pay[uid]

    asyncio.create_task(expire_qr(user_id, msg))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "buy_user":
        msg = f"""You selected User.
Plans:
1 day(s) → ₹200
3 day(s) → ₹300
7 day(s) → ₹600
30 day(s) → ₹1300

Pay via UPI: {UPI_ID} ({UPI_NAME})
\nSend /buy <duration> to proceed."""
        await query.edit_message_text(msg)

    elif data == "buy_reseller":
        msg = f"""You selected Reseller.
Reseller Packs (pay → get balance):
Pay ₹2000 → Get ₹5000
Pay ₹3000 → Get ₹7000
Pay ₹4000 → Get ₹10000
Pay ₹5000 → Get ₹15000

Pay via UPI: {UPI_ID} ({UPI_NAME})
\nThen use /buybalance <amount> and send transaction ID."""
        await query.edit_message_text(msg)

async def handle_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        return

    text = update.message.text.strip().split()
    if len(text) != 3:
        await update.message.reply_text("Send in format: <transaction_id> <amount> <user/reseller>")
        return

    txn_id, amount, user_type = text
    if user_id not in wait_Kaushik_pay:
        await update.message.reply_text("No pending payment found or payment expired.")
        return

    Kaushik_input_admin[user_id] = {"txn_id": txn_id, "amount": amount, "type": user_type}
    keyboard = [
        [InlineKeyboardButton("Approve", callback_data=f"approve_{user_id}_{txn_id}"),
         InlineKeyboardButton("Decline", callback_data=f"decline_{user_id}_{txn_id}")]
    ]
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"User @{update.message.from_user.username} paid ₹{amount} ({user_type}). Transaction ID: {txn_id}\nPlease approve and provide license key.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("✅ Transaction submitted for admin approval.")

async def admin_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global admin_Kaushik_user
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    action, user_id, txn_id = parts[0], int(parts[1]), parts[2]

    if action == "approve":
        admin_Kaushik_user = user_id
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"Send LICENSE KEY for user {user_id}).")
        await query.edit_message_text(f"✅ Approved transaction {txn_id}. Waiting for license input...")

    elif action == "decline":
        await context.bot.send_message(chat_id=user_id, text=f"❌ Payment declined. Transaction ID: {txn_id}")
        await query.edit_message_text(f"❌ Declined Transaction {txn_id} for user {user_id}")
        if user_id in wait_Kaushik_pay:
            del wait_Kaushik_pay[user_id]

async def admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global admin_Kaushik_user
    if update.message.from_user.id != ADMIN_ID or admin_Kaushik_user is None:
        return

    license_key = update.message.text.strip()
    user_id = admin_Kaushik_user
    if user_id not in Kaushik_input_admin:
        await update.message.reply_text("*❌ ERROR: No pending transaction found for this user.*", parse_mode="MarkdownV2")
        admin_Kaushik_user = None
        return

    payment_info = wait_Kaushik_pay.get(user_id, {})
    txn_id = Kaushik_input_admin[user_id]['txn_id']
    duration = payment_info.get("duration", "N/A")
    apk_link = Channel_File_Name

    def esc(text):
        text = str(text)
        reserved_chars = r'_*[]()~`>#+-=|{}.!'
        for char in reserved_chars:
            text = text.replace(char, f"\\{char}")
        return text

    msg_text = (
        f"*Hey 👋: {esc(user_id)}*\n\n"
        f"*License: {esc(license_key)}*\n"
        f"*Payment Id: {esc(txn_id)}*\n"
        f"*License Time: {esc(duration)} Day*\n"
        f"*Apk Link: {esc(apk_link)}*"
    )

    await context.bot.send_message(chat_id=user_id, text=msg_text, parse_mode="MarkdownV2")
    await update.message.reply_text(f"*✅ License sent to user {esc(user_id)}*", parse_mode="MarkdownV2")

    wait_Kaushik_pay.pop(user_id, None)
    Kaushik_input_admin.pop(user_id, None)
    admin_Kaushik_user = None

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /all <message>")
        return
    text = " ".join(context.args)
    for uid in Kaushik:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
        except:
            pass
    await update.message.reply_text("✅ Broadcast sent.")

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not allowed to use this command.")
        return
    if len(context.args) < 3 or context.args[1].lower() != "to":
        await update.message.reply_text("Usage: /update <old_text> to <new_text>")
        return

    old_text = context.args[0]
    new_text = " ".join(context.args[2:])
    file_path = os.path.realpath(__file__)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_text not in content:
            await update.message.reply_text(f"❌ '{old_text}' not found in bot file.")
            return

        content_new = content.replace(old_text, new_text)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_new)

        await update.message.reply_text(f"✅ Updated '{old_text}' → '{new_text}' in bot file.\nRestart bot to apply changes.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error updating file: {e}")

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("reseller", reseller))
    app.add_handler(CommandHandler("buybalance", buybalance))
    app.add_handler(CommandHandler("all", broadcast))
    app.add_handler(CommandHandler("update", update_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & (~filters.User(ADMIN_ID)), handle_transaction))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID), admin_input))
    app.add_handler(CallbackQueryHandler(button_click, pattern="^(buy_user|buy_reseller)$"))
    app.add_handler(CallbackQueryHandler(admin_button, pattern="^(approve_|decline_).*"))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()