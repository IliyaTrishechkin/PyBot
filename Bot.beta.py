import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

load_dotenv(Path(__file__).parent / '.env', encoding='utf-8-sig')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_IDENT"))

STATE_ASK, STATE_FB, STATE_REV = range(1, 4)
DATA = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
SYMBOL = DATA["SYMBOL"]

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("❓ Часті запитання", callback_data="menu_faq"),
         InlineKeyboardButton("🌟 Про Star for Life Ukraine", callback_data="menu_about")],
        [InlineKeyboardButton("✉️ Задати своє запитання", callback_data="menu_ask"),
         InlineKeyboardButton("📱 Соціальні мережі", callback_data="menu_social")],
        [InlineKeyboardButton("💬 Зворотній зв'язок", callback_data="menu_feedback"),
         InlineKeyboardButton("💻 Курси", callback_data="menu_courses")],
        [InlineKeyboardButton("⭐️ Відгуки", callback_data="menu_reviews")]
    ]
    await update.message.reply_text(DATA["Hello"], reply_markup=InlineKeyboardMarkup(kb))
    with open('id_users.json', 'r', encoding='utf-8') as f:
        ud = json.load(f)
    users = ud.get("Id_users", [])
    uid = str(update.effective_user.id)
    if uid not in users:
        users.append(uid)
        ud["Id_users"] = users
        with open('id_users.json', 'w', encoding='utf-8') as f:
            json.dump(ud, f, ensure_ascii=False, indent=4)

async def on_main_menu_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    match q.data:
        case "menu_faq":
            kb = [
                [InlineKeyboardButton("Від дитини", callback_data="faq|child")],
                [InlineKeyboardButton("Від дорослого", callback_data="faq|adult")],
                [InlineKeyboardButton("← Головне меню", callback_data="menu_main")]
            ]
            await q.edit_message_text("Від кого питання?", reply_markup=InlineKeyboardMarkup(kb))
        case "menu_about":
            txt = DATA["SchoolInfo"]["text"]
            kb = [
                [InlineKeyboardButton("Дізнатися більше", url=DATA["SchoolInfo"]["url"])],
                [InlineKeyboardButton("← Головне меню", callback_data="menu_main")]
            ]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        case "menu_ask":
            await q.edit_message_text("Напишіть своє питання, і я передам адміністратору.")
            return STATE_ASK
        case "menu_feedback":
            await q.edit_message_text("Надішліть ваш зворотній зв'язок:")
            return STATE_FB
        case "menu_reviews":
            await q.edit_message_text("Залиште відгук про курс чи бота:")
            return STATE_REV
        case "menu_social":
            kb = [[InlineKeyboardButton(n, url=u)] for n, u in DATA["Social"].items()]
            kb.append([InlineKeyboardButton("← Головне меню", callback_data="menu_main")])
            await q.edit_message_text("Наші соцмережі:", reply_markup=InlineKeyboardMarkup(kb))
        case "menu_courses":
            txt = DATA["ActiveCourse"]["Hello"]
            kb = [[InlineKeyboardButton(n, callback_data=f"course|{n}")] for n in DATA["ActiveCourse"]["Course"]]
            kb.append([InlineKeyboardButton("← Головне меню", callback_data="menu_main")])
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        case "menu_main":
            kb = [
                [InlineKeyboardButton("❓ Часті запитання", callback_data="menu_faq"),
                 InlineKeyboardButton("🌟 Про Star for Life Ukraine", callback_data="menu_about")],
                [InlineKeyboardButton("✉️ Задати своє запитання", callback_data="menu_ask"),
                 InlineKeyboardButton("📱 Соціальні мережі", callback_data="menu_social")],
                [InlineKeyboardButton("💬 Зворотній зв'язок", callback_data="menu_feedback"),
                 InlineKeyboardButton("💻 Курси", callback_data="menu_courses")],
                [InlineKeyboardButton("⭐️ Відгуки", callback_data="menu_reviews")]
            ]
            await q.edit_message_text(DATA["Hello"], reply_markup=InlineKeyboardMarkup(kb))

async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    context.bot_data['last_user'] = u.id
    msg = f"Нове питання від @{u.username or 'невідомий'} (ID: {u.id}):\n\n{update.message.text}"
    await context.bot.send_message(ADMIN_ID, msg)
    await update.message.reply_text("Дякую! Питання надіслано адміністратору.")
    return ConversationHandler.END

async def receive_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    msg = f"Зворотній зв'язок від @{u.username or 'невідомий'} (ID: {u.id}):\n\n{update.message.text}"
    await context.bot.send_message(ADMIN_ID, msg)
    await update.message.reply_text("Дякую за ваш зворотній зв'язок!")
    return ConversationHandler.END

async def receive_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    msg = f"Відгук від @{u.username or 'невідомий'} (ID: {u.id}):\n\n{update.message.text}"
    await context.bot.send_message(ADMIN_ID, msg)
    await update.message.reply_text("Дякую за ваш відгук!")
    return ConversationHandler.END

async def HelpAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    await update.message.reply_text(f"🔹/sb змінити символ (зараз {SYMBOL})\n🔹/ad розсилка (/ad текст{SYMBOL}посилання)\n🔹/add додати питання (/add child{SYMBOL}питання{SYMBOL}відповідь)\n🔹Відповіді: id{SYMBOL}текст або просто текст")

async def set_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        await update.message.reply_text("Тільки адмін.")
        return
    d = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
    sym = (update.message.text or "").replace("/sb", "").strip()
    if len(sym) != 1:
        await update.message.reply_text("Вкажіть один символ.")
        return
    d["SYMBOL"] = sym
    with open(Path(__file__).parent / 'question.json', 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)
    await update.message.reply_text(f"Символ змінено на {sym}")

async def add_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        if not context.args:
            return
        msg = " ".join(context.args)
        parts = msg.split(SYMBOL)
        if len(parts) != 3:
            return
        grp, qt, ans = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if grp in ["child", "adult"] and qt not in DATA["FAQs"][grp]:
            DATA["FAQs"][grp][qt] = ans
            with open(Path(__file__).parent / 'question.json', 'w', encoding='utf-8') as f:
                json.dump(DATA, f, ensure_ascii=False, indent=4)

async def ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    ex = no = 0
    ids = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))["Id_users"]
    if update.message.photo:
        photo = update.message.photo[-1].file_id
        cap = (update.message.caption or "").replace("/ad", "").strip().split(SYMBOL)
        body, kb = (cap[0], [[InlineKeyboardButton("Реєстрація", url=cap[1])]]) if len(cap) == 2 else ("", [])
        for uid in ids:
            try:
                if body:
                    await context.bot.send_photo(int(uid), photo=photo, caption=body, reply_markup=InlineKeyboardMarkup(kb))
                else:
                    await context.bot.send_photo(int(uid), photo=photo)
                ex += 1
            except:
                no += 1
    else:
        txt = (update.message.text or "").replace("/ad", "").strip().split(SYMBOL)
        body, kb = ("".join(txt[:-1]), [[InlineKeyboardButton("Реєстрація", url=txt[-1])]]) if len(txt) > 1 else (txt[0], [])
        for uid in ids:
            try:
                await context.bot.send_message(int(uid), text=body, reply_markup=InlineKeyboardMarkup(kb))
                ex += 1
            except:
                no += 1
    await update.message.reply_text(f"✅ Успішно: {ex}\n❌ Помилки: {no}")

async def ClikButton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.split("|")
    cmd, arg = parts[0], parts[-1]
    if cmd == "faq":
        qs = list(DATA["FAQs"][arg].keys())
        kb = [[InlineKeyboardButton(q, callback_data=f"showfaq|{arg}|{i}")] for i, q in enumerate(qs)]
        kb.append([InlineKeyboardButton("← Головне меню", callback_data="menu_main")])
        await q.edit_message_text("Оберіть запитання:", reply_markup=InlineKeyboardMarkup(kb))
    elif cmd == "course":
        txt, url = DATA["ActiveCourse"]["Course"][arg]
        kb = [[InlineKeyboardButton("Реєстрація", url=url)], [InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    elif cmd == "showfaq":
        grp, idx = parts[1], int(parts[2])
        key = list(DATA["FAQs"][grp].keys())[idx]
        ans = DATA["FAQs"][grp][key]
        txt = f"❓ {key}\n\n💬 {ans}"
        kb = [[InlineKeyboardButton("← Назад", callback_data=f"faq|{grp}")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    elif cmd == "myQ":
        await q.message.reply_text("Напишіть своє питання.")
        return STATE_ASK

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    parts = update.message.text.split(SYMBOL)
    if len(parts) == 1:
        uid = context.bot_data.pop('last_user', None)
        if uid:
            await context.bot.send_message(uid, f"Відповідь адміністратора:\n\n{parts[0]}")
    else:
        uid = int(parts[0])
        await context.bot.send_message(uid, f"Відповідь адміністратора:\n\n{parts[1]}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    conv_ask = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_ask$")],
        states={STATE_ASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)]},
        fallbacks=[]
    )
    conv_fb = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_feedback$")],
        states={STATE_FB: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_feedback)]},
        fallbacks=[]
    )
    conv_rev = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_reviews$")],
        states={STATE_REV: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_review)]},
        fallbacks=[]
    )

    app.add_handler(conv_ask)
    app.add_handler(conv_fb)
    app.add_handler(conv_rev)
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", HelpAdmin))
    app.add_handler(CommandHandler("sb", set_symbol))
    app.add_handler(CommandHandler("add", add_question))
    app.add_handler(MessageHandler((filters.Regex(r"^/ad") | filters.CaptionRegex(r"^/ad")) & filters.Chat(ADMIN_ID), ad))
    app.add_handler(CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ)\|"))
    app.add_handler(MessageHandler(filters.Chat(ADMIN_ID) & filters.TEXT, admin_reply))

    app.run_polling(drop_pending_updates=True)

#YaroBot