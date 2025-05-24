import logging
import json
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

load_dotenv(dotenv_path=Path(__file__).parent/'.env', encoding='utf-8-sig')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_PHONE"))
WAITING_FOR_QUESTION = 1
DATA_PATH = Path(__file__).parent/'question.json'

def load_data():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    categories = list(data["Categories"].keys())
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat|{i}")] for i, cat in enumerate(categories)]
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Оберіть категорію:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("|")
    action = parts[0]
    data = load_data()
    categories = list(data["Categories"].keys())
    if action == "cat":
        idx = int(parts[1])
        category = categories[idx]
        questions = data["Categories"][category]
        keyboard = []
        if idx == len(categories) - 1:
            keyboard.append([InlineKeyboardButton("Додати своє питання", callback_data="add_question")])
        for j, q in enumerate(questions):
            keyboard.append([InlineKeyboardButton(q, callback_data=f"q|{idx}|{j}")])
        keyboard.append([InlineKeyboardButton("← Назад", callback_data="back|categories")])
        await query.edit_message_text(text=category, reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "q":
        ci, qi = int(parts[1]), int(parts[2])
        category = categories[ci]
        question = data["Categories"][category][qi]
        answer = {q: a for q, a in data["Questions"]}.get(question, "Відповідь ще не додана.")
        text = f"❓ {question}\n\n💬 {answer}"
        keyboard = [[InlineKeyboardButton("← Назад", callback_data=f"back|questions|{ci}")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "back":
        tgt = parts[1]
        if tgt == "categories":
            keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat|{i}")] for i, cat in enumerate(categories)]
            await query.edit_message_text(text="Оберіть категорію:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            ci = int(parts[2])
            category = categories[ci]
            questions = data["Categories"][category]
            keyboard = []
            if ci == len(categories) - 1:
                keyboard.append([InlineKeyboardButton("Додати своє питання", callback_data="add_question")])
            for j, q in enumerate(questions):
                keyboard.append([InlineKeyboardButton(q, callback_data=f"q|{ci}|{j}")])
            keyboard.append([InlineKeyboardButton("← Назад", callback_data="back|categories")])
            await query.edit_message_text(text=category, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_add_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Напишіть своє питання у наступному повідомленні:")
    return WAITING_FOR_QUESTION

async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user = update.effective_user
    context.bot_data['last_user_id'] = user.id
    admin_msg = f"Нове питання від @{user.username or 'невідомий'} (ID: {user.id}):\n\n{user_text}"
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg)
    await update.message.reply_text("Дякуємо! Ваше питання надіслано адміністратору.")
    await start(update, context)
    return ConversationHandler.END

async def handle_admin_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer_text = update.message.text
    user_id = context.bot_data.get('last_user_id')
    if user_id:
        await context.bot.send_message(chat_id=user_id, text=f"Відповідь адміністратора:\n\n{answer_text}")
        await update.message.reply_text("Відповідь надіслано користувачу.")
        context.bot_data.pop('last_user_id', None)
    else:
        await update.message.reply_text("Немає нових питань для відповіді.")

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    bot = Bot(token=TOKEN)
    asyncio.run(bot.delete_webhook())
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_add_question, pattern="^add_question$")],
        states={WAITING_FOR_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)]},
        fallbacks=[]
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(handle_callback, pattern=r'^(cat|q|back)\|'))
    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(ADMIN_CHAT_ID), handle_admin_answer))
    app.run_polling(drop_pending_updates=True)
