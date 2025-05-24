import logging, json, os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)

load_dotenv(Path(__file__).parent / '.env', encoding='utf-8-sig')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_IDENT"))
STATE_Q = 1
DATA = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cats = list(DATA["Categories"].keys())
    kb = [
        [InlineKeyboardButton(cat, callback_data=f"cat|{i}")]
        for i, cat in enumerate(cats)
    ]
    await update.message.reply_text(
        "Оберіть категорію:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cats = list(DATA["Categories"].keys())
    parts = q.data.split("|")
    cmd = parts[0]

    if cmd == "cat":
        i = int(parts[1])
        cat = cats[i]
        items = DATA["Categories"][cat]
        kb = []
        if cat == "Додатково":
            kb.append([InlineKeyboardButton("Додати своє питання", callback_data="add")])
        for j, txt in enumerate(items):
            kb.append([InlineKeyboardButton(txt, callback_data=f"q|{i}|{j}")])
        kb.append([InlineKeyboardButton("← Назад", callback_data="back")])
        await q.edit_message_text(cat, reply_markup=InlineKeyboardMarkup(kb))

    elif cmd == "q":
        i, j = int(parts[1]), int(parts[2])
        cat = cats[i]
        ques = DATA["Categories"][cat][j]
        ans = dict(DATA["Questions"]).get(ques, "Відповідь ще не додана.")
        text = f"❓ {ques}\n\n💬 {ans}"
        kb = [[InlineKeyboardButton("← Назад", callback_data=f"cat|{i}")]]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif cmd == "add":
        await q.edit_message_text("Напишіть своє питання у відповідь на це повідомлення:")
        return STATE_Q

    elif cmd == "back":
        cats = list(DATA["Categories"].keys())
        kb = [
            [InlineKeyboardButton(cat, callback_data=f"cat|{i}")]
            for i, cat in enumerate(cats)
        ]
        await q.edit_message_text(
            "Оберіть категорію:",
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    u = update.effective_user
    context.bot_data['last_user'] = u.id
    msg = f"Нове питання від @{u.username or 'невідомий'} (ID: {u.id}):\n\n{text}"
    await context.bot.send_message(ADMIN_ID, msg)
    await update.message.reply_text("Дякую! Питання надіслано адміністратору.")
    return ConversationHandler.END

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = context.bot_data.pop('last_user', None)
    if uid:
        await context.bot.send_message(uid, f"Відповідь адміністратора:\n\n{text}")
        await update.message.reply_text("Відповідь відправлено користувачу.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_callback, pattern="^add$")],
        states={ STATE_Q: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)
        ]},
        fallbacks=[]
    )
    app.add_handler(conv)

    app.add_handler(CommandHandler("start", start_cmd))

    app.add_handler(CallbackQueryHandler(
        on_callback,
        pattern=r'^(cat|q|back)(?:\|.*)?$'
    ))

    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(ADMIN_ID), admin_reply))

    app.run_polling(drop_pending_updates=True)