import logging, json, os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)

load_dotenv(Path(__file__).parent/'.env', encoding='utf-8-sig')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_PHONE"))
WAITING = 1
DATA = Path(__file__).parent/'question.json'

def load_data():
    return json.loads(DATA.read_text(encoding='utf-8'))

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cats = list(load_data()["Categories"].keys())
    kb = [[InlineKeyboardButton(c, callback_data=f"cat|{i}")] for i,c in enumerate(cats)]
    await context.bot.send_message(update.effective_chat.id, "Оберіть категорію:", reply_markup=InlineKeyboardMarkup(kb))

async def callback_q(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    data = load_data()
    cats = list(data["Categories"].keys())
    parts = q.data.split("|")
    if parts[0]=="cat":
        i=int(parts[1]); cat=cats[i]; qs=data["Categories"][cat]
        kb=[]
        if cat=="🔹 Додатково": kb.append([InlineKeyboardButton("Додати своє питання", callback_data="add")])
        for j,t in enumerate(qs): kb.append([InlineKeyboardButton(t, callback_data=f"q|{i}|{j}")])
        kb.append([InlineKeyboardButton("← Назад", callback_data="back")])
        await q.edit_message_text(cat, reply_markup=InlineKeyboardMarkup(kb))
    elif parts[0]=="q":
        i,j=int(parts[1]),int(parts[2])
        cat=cats[i]; ques=data["Categories"][cat][j]
        ans={q:a for q,a in data["Questions"]}.get(ques,"Відповідь ще не додана.")
        txt=f"❓ {ques}\n\n💬 {ans}"
        kb=[[InlineKeyboardButton("← Назад", callback_data=f"cat|{i}")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    elif parts[0]=="back":
        await start_cmd(update, context)

async def add_q(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text("Напишіть своє питання:")
    return WAITING

async def receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt=update.message.text; u=update.effective_user
    context.bot_data['uid']=u.id
    msg=f"Нове питання від @{u.username or 'невідомий'} (ID:{u.id}):\n\n{txt}"
    await context.bot.send_message(ADMIN_CHAT_ID, msg)
    await update.message.reply_text("Дякую! Питання надіслано.")
    return ConversationHandler.END

async def admin_ans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt=update.message.text; uid=context.bot_data.get('uid')
    if uid:
        await context.bot.send_message(uid, f"Відповідь адміністратора:\n\n{txt}")
        await update.message.reply_text("Відповідь надіслано.")
        context.bot_data.pop('uid',None)

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    Bot(token=TOKEN).delete_webhook()
    app=ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(add_q, pattern="^add$"))
    app.add_handler(CallbackQueryHandler(callback_q, pattern="^(cat|q|back|add)"))
    conv=ConversationHandler(
        entry_points=[CallbackQueryHandler(add_q, pattern="^add$")],
        states={WAITING:[MessageHandler(filters.TEXT&~filters.COMMAND, receive)]},
        fallbacks=[]
    )
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT&filters.Chat(ADMIN_CHAT_ID), admin_ans))
    app.run_polling(drop_pending_updates=True)
