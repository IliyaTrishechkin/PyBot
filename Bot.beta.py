import logging
import json
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CallbackQueryHandler, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

DATA_PATH = Path(__file__).parent / 'question.json'

def load_data():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    categories = list(data["Categories"].keys())
    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"cat|{i}")]
        for i, cat in enumerate(categories)
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    action = data[0]
    json_data = load_data()
    categories = list(json_data["Categories"].keys())

    if action == "cat":
        cat_idx = int(data[1])
        cat = categories[cat_idx]
        questions = json_data["Categories"][cat]
        keyboard = [
            [InlineKeyboardButton(q, callback_data=f"q|{cat_idx}|{j}")]
            for j, q in enumerate(questions)
        ]
        keyboard.append([InlineKeyboardButton("← Назад", callback_data="back|categories")])
        await query.edit_message_text(text=cat, reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == "q":
        cat_idx = int(data[1])
        q_idx = int(data[2])
        cat = categories[cat_idx]
        question = json_data["Categories"][cat][q_idx]
        qa_map = {q: a for q, a in json_data["Questions"]}
        answer = qa_map.get(question, "Ответ ещё не добавлен.")
        text = f"❓ {question}\n\n💬 {answer}"
        keyboard = [
            [InlineKeyboardButton("← Назад", callback_data=f"back|questions|{cat_idx}")]
        ]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif action == "back":
        target = data[1]
        if target == "categories":
            keyboard = [
                [InlineKeyboardButton(cat, callback_data=f"cat|{i}")]
                for i, cat in enumerate(categories)
            ]
            await query.edit_message_text(
                text="Выберите категорию:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif target == "questions":
            cat_idx = int(data[2])
            cat = categories[cat_idx]
            questions = json_data["Categories"][cat]
            keyboard = [
                [InlineKeyboardButton(q, callback_data=f"q|{cat_idx}|{j}")]
                for j, q in enumerate(questions)
            ]
            keyboard.append([InlineKeyboardButton("← Назад", callback_data="back|categories")])
            await query.edit_message_text(text=cat, reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == '__main__':
    app = ApplicationBuilder().token('7311053326:AAES8JRhk--Nz3fA_LcMjeMvMG5Pr5FfDys').build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_callback, pattern='^(cat|q|back)\|'))
    app.run_polling()
