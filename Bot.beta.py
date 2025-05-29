import os, json, logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

load_dotenv(Path(__file__).parent / '.env', encoding='utf-8-sig')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_IDENT"))

STATE_Q = 1
DATA = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(item, callback_data=f"main|{i}")] for i, item in enumerate(DATA["MainMenu"])]
    await update.message.reply_text("Привіт! Оберіть пункт меню:", reply_markup=InlineKeyboardMarkup(kb))

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.split("|")
    cmd, arg = parts[0], parts[-1]

    if cmd == "main":
        idx = int(arg)
        choice = DATA["MainMenu"][idx]
        if choice == "Про Star for Life Ukraine":
            text = DATA["SchoolInfo"]["text"]
            kb = [
                [InlineKeyboardButton("Дізнатися більше", url=DATA["SchoolInfo"]["url"])],
                [InlineKeyboardButton("← Назад", callback_data="main|back")]
            ]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
        elif choice == "Поширені питання":
            kb = [
                [InlineKeyboardButton("Від дитини", callback_data="faq|child")],
                [InlineKeyboardButton("Від дорослого", callback_data="faq|adult")],
                [InlineKeyboardButton("← Назад", callback_data="main|back")]
            ]
            await q.edit_message_text("Оберіть категорію запитань:", reply_markup=InlineKeyboardMarkup(kb))
        elif choice == "Соціальні мережі":
            kb = [[InlineKeyboardButton(name, url=url)] for name, url in DATA["Social"].items()] + [[InlineKeyboardButton("← Назад", callback_data="main|back")]]
            await q.edit_message_text("Наші соціальні мережі:", reply_markup=InlineKeyboardMarkup(kb))
        elif choice == "Курси":
            kb = [[InlineKeyboardButton(name, callback_data=f"course|{name}")] for name in DATA["Courses"].keys()] + [[InlineKeyboardButton("← Назад", callback_data="main|back")]]
            await q.edit_message_text("Оберіть курс:", reply_markup=InlineKeyboardMarkup(kb))
        elif arg == "back":
            await start_cmd(update, context)

    elif cmd == "faq":
        group = arg
        questions = list(DATA["FAQs"][group].keys())
        kb = [[InlineKeyboardButton(q_text, callback_data=f"showfaq|{group}|{i}")] for i, q_text in enumerate(questions)] + [[InlineKeyboardButton("← Назад", callback_data="main|1")]]
        await q.edit_message_text("Оберіть запитання:", reply_markup=InlineKeyboardMarkup(kb))

    elif cmd == "showfaq":
        group, idx = parts[1], int(parts[2])
        question = list(DATA["FAQs"][group].keys())[idx]
        answer = DATA["FAQs"][group][question]
        text = f"❓ {question}\n\n💬 {answer}"
        kb = [[InlineKeyboardButton("← Назад", callback_data=f"faq|{group}")]]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif cmd == "course":
        name = arg
        desc = DATA["Courses"][name]
        text = f"💻 <b>{name}</b>\n\n{desc}"
        kb = [[InlineKeyboardButton("← Назад", callback_data="main|3")]]
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

    elif cmd == "back":
        await start_cmd(update, context)

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
        await update.message.reply_text("Відповідь надіслано користувачу.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_callback, pattern="^add$")],
        states={STATE_Q: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)]},
        fallbacks=[]
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(on_callback, pattern="^(main|faq|showfaq|course|back)\|?.*$"))
    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(ADMIN_ID), admin_reply))
    app.run_polling(drop_pending_updates=True)
