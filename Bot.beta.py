import os, json, logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

load_dotenv(Path(__file__).parent / '.env', encoding='utf-8-sig')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_IDENT"))

STATE_Q = 1
DATA = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
SYMBOL = DATA["SYMBOL"]

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kd = [[InlineKeyboardButton("Розпочати", callback_data=f"smain")]]
    text = DATA["Hello"]
    await update.message.reply_text(text, reply_markup=(InlineKeyboardMarkup(kd)))
    # запис id користувачів
    with open('id_users.json', "r", encoding="utf-8") as f:
        data = json.load(f)
    
    users_list = data.get("Id_users", [])
    user_id_str = str(update.effective_user.id)

    if user_id_str not in users_list:
        users_list.append(user_id_str)   
        data["Id_users"] = users_list
        with open('id_users.json', "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


async def HelpAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return 0
    await update.message.reply_text(f"Я розповім про можливості адмінів:\n\n🔹/sb команда задає спец. символ. Зараз символ {SYMBOL}\n\n🔹/ad зозсилання сповіщень фото, тест, фото та текст. Починати треба з /ad далі текст або нічго. Якщо після текста вставити спец. символ та посилання, то свориться кнопка з посиланням. Приклад: /ad <текст>{SYMBOL}<посилання>\n\n🔹/add додає нове питання <child/adult>{SYMBOL}<питання>{SYMBOL}<відповідь>\n\n🔹Коли прийшло питання вставте id користувача, спец. символ '{SYMBOL}', відповідь")


async def set_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        await update.message.reply_text("Цю команду можна використовувати лише адмінам.")
        return 0
    DATA = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
    text = (update.message.text or "").replace("/sb", "").strip()
    if text == "" or len(text) > 1:
        await update.message.reply_text("НЕ вказан символ або більше одного знака")
        return 0
    try: 
        SYMBOL = text
        DATA["SYMBOL"] = SYMBOL
        with open(Path(__file__).parent / 'question.json', "w", encoding="utf-8") as f:
                json.dump(DATA, f, ensure_ascii=False, indent=4)
        DATA = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
        await update.message.reply_text(f"Знак змінено на {DATA["SYMBOL"]}✅")
    except Exception as e:
        logging.warning(f"Не вдалося надіслати {e}")
        await update.message.reply_text("Помилка❌")


async def start_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    await q.answer()
    if data == "smain":
        kd = [[KeyboardButton(item)] for item in DATA["MainMenu"]]
        await q.message.reply_text("Обери тему зі списку нижче, щоб дізнатися більше.", reply_markup=ReplyKeyboardMarkup(kd, resize_keyboard=True))


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    match text:
        case "Про Star for Life Ukraine🌟":
            text = DATA["SchoolInfo"]["text"]
            kb = [[InlineKeyboardButton("Дізнатися більше", url=DATA["SchoolInfo"]["url"])]]
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        case "❓Поширені питання":
            kd = [
                [InlineKeyboardButton("Від дитини", callback_data="faq|child")],
                [InlineKeyboardButton("Від дорослого", callback_data="faq|adult")]
                ]
            await update.message.reply_text("Від кого питання", reply_markup=InlineKeyboardMarkup(kd))
        case "Соціальні мережі📱":
            kb = [[InlineKeyboardButton(name, url=url)] for name, url in DATA["Social"].items()]
            await update.message.reply_text("Наші соціальні мережі:", reply_markup=InlineKeyboardMarkup(kb))
        case "Курси💻":
            text = DATA["ActiveCourse"]["Hello"]
            kd = [[InlineKeyboardButton(name, callback_data=f"course|{name}")] for name in DATA["ActiveCourse"]["Course"]]
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kd))


async def ClikButton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.split("|")
    cmd, arg = parts[0], parts[-1]
    match cmd:
        case "faq":
            group = arg
            questions = list(DATA["FAQs"][group].keys())
            kd = [[InlineKeyboardButton(q_text, callback_data=f"showfaq|{group}|{i}")] for i, q_text in enumerate(questions)] + [[InlineKeyboardButton("У мене є своє питання", callback_data=f"myQ")]] + [[InlineKeyboardButton("← Назад", callback_data=f"back|FAQs")]]
            await q.edit_message_text("Оберіть запитання:", reply_markup=InlineKeyboardMarkup(kd))
        case "course":
            text = DATA["ActiveCourse"]["Course"][arg][0]
            url = DATA["ActiveCourse"]["Course"][arg][1]
            kd = [[InlineKeyboardButton("Реєстрація", url=url)]] + [[InlineKeyboardButton("← Назад", callback_data=f"back|curses")]]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kd))
        case "showfaq":
            group, idx = parts[1], int(parts[2])
            question = list(DATA["FAQs"][group].keys())[idx]
            answer = DATA["FAQs"][group][question]
            text = f"❓ {question}\n\n💬 {answer}"
            kd = [[InlineKeyboardButton("← Назад", callback_data=f"faq|{group}")]]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kd))
        case "back":
            match arg:
                case "curses":
                    text = DATA["ActiveCourse"]["Hello"]
                    kd = [[InlineKeyboardButton(name, callback_data=f"course|{name}")] for name in DATA["ActiveCourse"]["Course"]]
                    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kd))
                case "FAQs":
                    kd = [[InlineKeyboardButton("Від дитини", callback_data="faq|child")], [InlineKeyboardButton("Від дорослого", callback_data="faq|adult")]]
                    await q.edit_message_text("Від кого питання", reply_markup=InlineKeyboardMarkup(kd))  
        case "myQ":
            await update.callback_query.message.reply_text("Добре, напиши своє питання. Я передам його нашій команді.")
            return STATE_Q


async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    u = update.effective_user
    context.bot_data['last_user'] = u.id
    msg = f"Нове питання від @{u.username or 'невідомий'} (ID: {u.id}):\n\n{text}"
    await context.bot.send_message(chat_id=ADMIN_ID, text = msg)
    await context.bot.send_message(ADMIN_ID, f"Напишіть спочатку id користувача якому відповідаєте, потім {SYMBOL} і саму відповідь.\nЯкщо id не вказати, то відповідь відправится останньому користувачю який задав питання.\n Приклад: 12345678{SYMBOL}текст або просто текст.")
    await update.message.reply_text("Дякую! Питання надіслано адміністратору.")
    return ConversationHandler.END


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return 0 
    chat = update.effective_chat
    user = update.effective_user
    message = update.message.text
    data_answer = message.split(SYMBOL)

    if len(data_answer) == 1:
        uid = context.bot_data.pop('last_user', None)
        if uid:
            await context.bot.send_message(uid, f"Відповідь адміністратора:\n\n{message}")
            await update.message.reply_text("Відповідь надіслано користувачу.")
    else:
        uid = int(data_answer[0])
        await context.bot.send_message(uid, f"Відповідь адміністратора:\n\n{data_answer[1]}")
        await update.message.reply_text("Відповідь надіслано користувачу.")


async def add_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        if not context.args:
            await update.message.reply_text("Невірний формат. Використовуйте:\n<child/adult>/<питання>/<відповідь>")
            return
        message = " ".join(context.args)  
        parts = message.split(SYMBOL)

        if len(parts) != 3:
            await update.message.reply_text("Невірний формат. Використовуйте:\n<child/adult>/<питання>/<відповідь>")
            return
        group, question, answer = parts
        group = group.strip().lower()
        question = question.strip()
        answer = answer.strip()

        if group not in ["child", "adult"]:
            await update.message.reply_text("Перша частина має бути 'child' або 'adult'")
            return

        if question in DATA["FAQs"][group]:
            await update.message.reply_text("Це питання вже існує.")
            return

        DATA["FAQs"][group][question] = answer
        with open(Path(__file__).parent / 'question.json', "w", encoding="utf-8") as f:
            json.dump(DATA, f, ensure_ascii=False, indent=4)

        await update.message.reply_text(f"Питання додано до '{group}'.")
    else:
        await update.message.reply_text("Цю команду можна використовувати лише адмінам.")


async def ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ex, no = 0, 0

    if update.effective_chat.id != ADMIN_ID:
        await update.message.reply_text("Цю команду можна використовувати лише адмінам.")
        return 0
    
    if not update.message.photo:
        text = (update.message.text or "").replace("/ad", "").strip()
        if not text:
            await update.message.reply_text("Текст розсилки порожній. Повідомлення не надіслано.")
            return 0
        data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))
        user_ids = data.get("Id_users", [])
        user_ids = "|".join(user_ids)
        user_ids = user_ids.split("|")
        text = text.split(SYMBOL)
        if len(text)>1:
            kd = [[InlineKeyboardButton("Реєстрація", url=text[-1])]]
            texts = "".join(text[:(len(text)-1)])
        else:
            kd = []
            texts = text[0]
        for i in user_ids:
            try:
                await context.bot.send_message(i, text = texts, reply_markup=InlineKeyboardMarkup(kd) if kd else None)
                ex+=1
            except Exception as e:
                logging.warning(f"Не вдалося надіслати {e}")
                no+=1
        await update.message.reply_text(f"Розсилка завершена.\n✅ Успішно: {ex}\n❌ Помилки: {no}")
        return 0
    
    photo = update.message.photo[-1].file_id
    captiond = (update.message.caption or "").replace("/ad", "").strip()
    data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))
    user_ids = data.get("Id_users", [])
    user_ids = "|".join(user_ids)
    user_ids = user_ids.split("|")
    text = captiond.split(SYMBOL)
    if len(text)==2:
        kd = [[InlineKeyboardButton("Реєстрація", url=text[-1])]]
    else:
        kd = []
    if photo and captiond:
        text = captiond.split(SYMBOL)
        for i in user_ids:
            try:
                await context.bot.send_photo(chat_id=int(i), photo=photo, caption = text[0], reply_markup=InlineKeyboardMarkup(kd) if kd else None)
                ex+=1
            except Exception as e:
                logging.warning(f"Не вдалося надіслати {e}")
                no+=1
    elif photo:
        for i in user_ids:
            try:
                await context.bot.send_photo(chat_id=int(i), photo=photo, reply_markup=InlineKeyboardMarkup(kd) if kd else None)
                ex+=1
            except Exception as e:
                logging.warning(f"Не вдалося надіслати {e}")
                no+=1
    
    await update.message.reply_text(f"Розсилка завершена.\n✅ Успішно: {ex}\n❌ Помилки: {no}")




if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ClikButton, pattern="^(myQ)$")],
        states={STATE_Q: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)]},
        fallbacks=[],
    )

    app.add_handler(conv) 
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler( "sb", set_symbol))
    app.add_handler(CommandHandler("add" , add_question))
    app.add_handler(CommandHandler("help" , HelpAdmin))
    app.add_handler(MessageHandler((filters.Regex(r"^/ad") | filters.CaptionRegex(r"^/ad")) & filters.Chat(ADMIN_ID), ad))

    app.add_handler(CallbackQueryHandler(start_categories, pattern="^(smain)\|?.*$"))
    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(ADMIN_ID), admin_reply))

    app.add_handler(MessageHandler(filters.TEXT, on_callback))
    app.add_handler(CallbackQueryHandler(ClikButton, pattern="^(main|faq|course|showfaq|back)\|?.*$"))
    app.run_polling(drop_pending_updates=True)