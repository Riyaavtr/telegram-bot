
import json
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# --- CONFIGURATION ---
BOT_API_TOKEN = "7914659787:AAHi7txDmnRP7PdVu1OQpmz8QLf1Oxvjs84"
ADMIN_ID = 1718434162
DATA_FILE = "data.json"

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load & Save JSON ---
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"source_channel_ids": [], "channels": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Conversation States ---
ADD_TARGET, ADD_CROWN, ADD_JEETNA = range(3)
EDIT_SELECT_CHANNEL, EDIT_SELECT_PLATFORM, EDIT_ENTER_CODE = range(3, 6)
ADD_SOURCE = 6

# --- /start Admin Panel ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = [
        [InlineKeyboardButton("âž• Add Target Channel", callback_data="add_target")],
        [InlineKeyboardButton("âž– Remove Target Channel", callback_data="remove_target")],
        [InlineKeyboardButton("ðŸ“ Edit Referral Code", callback_data="edit_referral")],
        [InlineKeyboardButton("ðŸ“‹ View All Channels", callback_data="view_targets")],
        [InlineKeyboardButton("âž• Add Source Channel", callback_data="add_source")],
        [InlineKeyboardButton("âž– Remove Source Channel", callback_data="remove_source")],
        [InlineKeyboardButton("ðŸ“‹ View Source Channels", callback_data="view_sources")]
    ]
    await update.message.reply_text("ðŸ›  Admin Panel:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- Button Handling ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    context.user_data.clear()

    if data == "add_target":
        await query.message.reply_text("Send the Target Channel ID to add:")
        return ADD_TARGET
    elif data == "remove_target":
        d = load_data()
        buttons = [[InlineKeyboardButton(str(ch["id"]), callback_data=f"remove_target_{ch['id']}")] for ch in d["channels"]]
        await query.message.reply_text("Select channel to remove:", reply_markup=InlineKeyboardMarkup(buttons))
    elif data == "edit_referral":
        d = load_data()
        buttons = [[InlineKeyboardButton(str(ch["id"]), callback_data=f"edit_channel_{ch['id']}")] for ch in d["channels"]]
        await query.message.reply_text("Select channel to edit:", reply_markup=InlineKeyboardMarkup(buttons))
    elif data == "view_targets":
        d = load_data()
        msg = "\n".join([f"{ch['id']}: Crown11={ch['referral_codes'].get('crown11', 'N/A')}, Jeetna={ch['referral_codes'].get('jeetna', 'N/A')}" for c>
        await query.message.reply_text(msg or "No target channels.")
    elif data == "add_source":
        await query.message.reply_text("Send Source Channel ID to add:")
        return ADD_SOURCE
    elif data == "remove_source":
        d = load_data()
        buttons = [[InlineKeyboardButton(str(cid), callback_data=f"remove_source_{cid}")] for cid in d["source_channel_ids"]]
        await query.message.reply_text("Select source channel to remove:", reply_markup=InlineKeyboardMarkup(buttons))
    elif data == "view_sources":
        d = load_data()
        msg = "\n".join([str(cid) for cid in d["source_channel_ids"]])
        await query.message.reply_text(msg or "No source channels.")

# --- Add Target Channel Flow ---
async def add_target_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = int(update.message.text)
    context.user_data['new_channel_id'] = cid
    await update.message.reply_text("Enter Crown11 referral code:")
    return ADD_CROWN

async def add_crown_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['crown11'] = update.message.text.strip()
    await update.message.reply_text("Enter Jeetna referral code:")
    return ADD_JEETNA

async def add_jeetna_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jeetna = update.message.text.strip()
    cid = context.user_data['new_channel_id']
    crown = context.user_data['crown11']
    d = load_data()
    d['channels'].append({"id": cid, "referral_codes": {"crown11": crown, "jeetna": jeetna}})
    save_data(d)
    await update.message.reply_text("âœ… Channel added with both referral codes.")
    return ConversationHandler.END

# --- Add Source Channel ---
async def add_source_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = int(update.message.text.strip())
    d = load_data()
    if cid not in d['source_channel_ids']:
        d['source_channel_ids'].append(cid)
        save_data(d)
    await update.message.reply_text("âœ… Source channel added.")
    return ConversationHandler.END

# --- Handle Deletions & Edits ---
async def callback_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = load_data()
    data = query.data

    if data.startswith("remove_target_"):
        cid = int(data.split("_")[-1])
        d['channels'] = [ch for ch in d['channels'] if ch['id'] != cid]
        save_data(d)
        await query.message.reply_text(f"âœ… Removed target channel {cid}.")
    elif data.startswith("remove_source_"):
        cid = int(data.split("_")[-1])
        d['source_channel_ids'].remove(cid)
        save_data(d)
        await query.message.reply_text(f"âœ… Removed source channel {cid}.")
elif data.startswith("edit_channel_"):
        cid = int(data.split("_")[-1])
        context.user_data['edit_channel_id'] = cid
        keyboard = [
            [InlineKeyboardButton("Crown11", callback_data="edit_platform_crown11")],
            [InlineKeyboardButton("Jeetna", callback_data="edit_platform_jeetna")]
        ]
        await query.message.reply_text("Choose platform:", reply_markup=InlineKeyboardMarkup(keyboard))
        return EDIT_SELECT_PLATFORM
    elif data.startswith("edit_platform_"):
        platform = data.split("_")[-1]
        context.user_data['edit_platform'] = platform
        await query.message.reply_text(f"Enter new code for {platform}:")
        return EDIT_ENTER_CODE

async def save_edited_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    d = load_data()
    cid = context.user_data['edit_channel_id']
    platform = context.user_data['edit_platform']
    for ch in d['channels']:
        if ch['id'] == cid:
            ch['referral_codes'][platform] = code
            break
    save_data(d)
    await update.message.reply_text("âœ… Updated referral code.")
    return ConversationHandler.END

# --- Message Forwarder ---
async def forward_and_replace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post
    if not message:
        return

    d = load_data()
    if message.chat.id not in d['source_channel_ids']:
        return

    original_text = message.text or message.caption or ""
    PLATFORM_PATTERNS = {
        "crown11": r"https://h5\.crown11\.club\?root=[a-zA-Z0-9]+",
        "jeetna": r"https://h5\.jeetna\.club\?root=[a-zA-Z0-9]+"
    }

    for target in d['channels']:
        modified_text = original_text
        for platform, pattern in PLATFORM_PATTERNS.items():
            new_code = target['referral_codes'].get(platform)
            if new_code:
                modified_text = re.sub(
                    pattern,
                    f"https://h5.{platform}.club?root={new_code}",
                    modified_text
                )

        try:
            if message.text:
                await context.bot.send_message(chat_id=target['id'], text=modified_text, disable_web_page_preview=True)
            elif message.caption and message.photo:
                await context.bot.send_photo(chat_id=target['id'], photo=message.photo[-1].file_id, caption=modified_text)
            elif message.video:
                await context.bot.send_video(chat_id=target['id'], video=message.video.file_id, caption=modified_text)
            elif message.document:
                await context.bot.send_document(chat_id=target['id'], document=message.document.file_id, caption=modified_text)
        except Exception as e:
            logger.error(f"Error sending to {target['id']}: {e}")

# --- Main Entry Point ---
def main():
    app = Application.builder().token(BOT_API_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            ADD_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_target_id)],
            ADD_CROWN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_crown_code)],
            ADD_JEETNA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_jeetna_code)],
            ADD_SOURCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_source_channel)],
            EDIT_SELECT_PLATFORM: [CallbackQueryHandler(callback_delete)],
            EDIT_ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_code)]
        },
        fallbacks=[]
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(callback_delete))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, forward_and_replace))
    logger.info("Bot started...")
    app.run_polling()

if __name__ == '__main__':
    main()
