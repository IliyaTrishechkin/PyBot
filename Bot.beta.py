import logging
import json
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

DATA_PATH = Path(__file__).parent / 'question.json'

def load_data():
    if not DATA_PATH.exists():
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump({"Questions": []}, f, ensure_ascii=False, indent=4)
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Привіт! Я FAQ-бот. Просто напиши питання — і я спробую відповісти."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = update.message.text.strip()
    data = load_data().get("Questions", [])
    for q, a in data:
        if q.strip().lower() == user_question.lower():
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=a
            )
            return
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Вибач, я ще не знаю відповіді на це питання."
    )

if __name__ == '__main__':
    app = ApplicationBuilder().token('ВАШ_TOKEN_ТУТ').build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
