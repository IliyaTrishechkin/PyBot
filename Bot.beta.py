import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

load_dotenv(Path(__file__).parent / '.env', encoding='utf-8-sig')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_IDENT"))

DATA = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(item, callback_data=f"main|{i}")] for i, item in enumerate(DATA["MainMenu"])]
    await update.message.reply_text("Привіт! Оберіть пункт меню:", reply_markup=InlineKeyboardMarkup(kb))

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.split("|")
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    if cmd == "main":
        arg = args[0]
        if arg == "back":
            kb = [[InlineKeyboardButton(item, callback_data=f"main|{i}")] for i, item in enumerate(DATA["MainMenu"])]
            return await q.edit_message_text("Привіт! Оберіть пункт меню:", reply_markup=InlineKeyboardMarkup(kb))
        idx = int(arg)
        choice = DATA["MainMenu"][idx]
        if choice == "Про Star for Life Ukraine":
            text = DATA["SchoolInfo"]["text"]
            kb = [
                [InlineKeyboardButton("Дізнатися більше", url=DATA["SchoolInfo"]["url"])],
                [InlineKeyboardButton("← Назад", callback_data="main|back")]
            ]
            return await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
        if choice == "Поширені питання":
            kb = [
                [InlineKeyboardButton("Від дитини", callback_data="faq|child")],
                [InlineKeyboardButton("Від дорослого", callback_data="faq|adult")],
                [InlineKeyboardButton("← Назад", callback_data="main|back")]
            ]
            return await q.edit_message_text("Оберіть категорію запитань:", reply_markup=InlineKeyboardMarkup(kb))
        if choice == "Соціальні мережі":
            kb = [[InlineKeyboardButton(name, url=url)] for name, url in DATA["Social"].items()]
            kb.append([InlineKeyboardButton("← Назад", callback_data="main|back")])
            return await q.edit_message_text("Наші соціальні мережі:", reply_markup=InlineKeyboardMarkup(kb))
        if choice == "Курси":
            kb = [[InlineKeyboardButton(name, callback_data=f"course|{name}")] for name in DATA["Courses"].keys()]
            kb.append([InlineKeyboardButton("← Назад", callback_data="main|back")])
            return await q.edit_message_text("Оберіть курс:", reply_markup=InlineKeyboardMarkup(kb))

    if cmd == "faq":
        group = args[0]
        questions = list(DATA["FAQs"][group].keys())
        kb = [[InlineKeyboardButton(q_text, callback_data=f"showfaq|{group}|{i}")] for i, q_text in enumerate(questions)]
        kb.append([InlineKeyboardButton("← Назад", callback_data="main|back")])
        return await q.edit_message_text("Оберіть запитання:", reply_markup=InlineKeyboardMarkup(kb))

    if cmd == "showfaq":
        group, idx = args[0], int(args[1])
        question = list(DATA["FAQs"][group].keys())[idx]
        answer = DATA["FAQs"][group][question]
        text = f"❓ {question}\n\n💬 {answer}"
        kb = [[InlineKeyboardButton("← Назад", callback_data=f"faq|{group}")]]
        return await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

    if cmd == "course":
        name = args[0]
        desc = DATA["Courses"][name]
        text = f"💻 <b>{name}</b>\n\n{desc}"
        kb = [[InlineKeyboardButton("← Назад", callback_data="main|back")]]
        return await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    u = update.effective_user
    context.bot_data['last_user'] = u.id
    msg = f"Нове питання від @{u.username or 'невідомий'} (ID: {u.id}):\n\n{text}"
    await context.bot.send_message(ADMIN_ID, msg)
    await update.message.reply_text("Дякую! Питання надіслано адміністратору.")
    return

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = context.bot_data.pop('last_user', None)
    if uid:
        await context.bot.send_message(uid, f"Відповідь адміністратора:\n\n{text}")
        await update.message.reply_text("Відповідь надіслано користувачу.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(ADMIN_ID), admin_reply))
    app.run_polling(drop_pending_updates=True)
