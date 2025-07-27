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

STATE_ASK, STATE_FB, STATE_REV, STATE_DATA_1, STATE_DATA_2, STATE_DATA_3 = range(1, 7)
DATA = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
SYMBOL = DATA["SYMBOL"]

def up_date():
    global SYMBOL
    global DATA
    DATA = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
    SYMBOL = DATA["SYMBOL"]

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("❓ Часті запитання", callback_data="menu_faq"),
         InlineKeyboardButton("🌟 Про Star for Life Ukraine", callback_data="menu_about")],
        [InlineKeyboardButton("✉️ Задати своє запитання", callback_data="menu_ask"),
         InlineKeyboardButton("📱 Соціальні мережі", callback_data="menu_social")],
        [InlineKeyboardButton("🧾Заповнити свої данні", callback_data="menu_userdata"),
         InlineKeyboardButton("💻 Курси", callback_data="menu_courses")],
        [InlineKeyboardButton("💬 Зворотній зв'язок", callback_data="menu_feedback"),
         InlineKeyboardButton("⭐️ Відгуки", callback_data="menu_reviews")]
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
           await q.edit_message_text("🔔 Нам дуже важлива ваша думка!\nПоділіться своїми враженнями, ідеями або зауваженнями, щоб ми ставали кращими 💬\nНапишіть Ваше повідомлення нижче та відправте")
           return STATE_FB
        case "menu_reviews":
            await q.edit_message_text("🌟 Поділіться своїм досвідом!\nЩо сподобалось у курсі або роботі бота? Що можемо покращити?\nНапишіть Ваше повідомлення нижче та відправте")
            return STATE_REV
        case "menu_social":
            kb = [[InlineKeyboardButton(n, url=u)] for n, u in DATA["Social"].items()]
            kb.append([InlineKeyboardButton("← Головне меню", callback_data="menu_main")])
            await q.edit_message_text("Наші соцмережі:", reply_markup=InlineKeyboardMarkup(kb))
        case "menu_courses":
            txt = DATA["ActiveCourse"]["Hello"]
            kb = [[InlineKeyboardButton(c["title"], callback_data=f"course|{c['title']}")] for c in DATA["ActiveCourse"]["Course"]]
            kb.append([InlineKeyboardButton("← Головне меню", callback_data="menu_main")])
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        case "menu_userdata":
            await q.edit_message_text("Введіть ваш ПІБ:\nприклад -> Северюк Лариса Іванівна")
            return STATE_DATA_1
        case "menu_main":
            kb = [
                [InlineKeyboardButton("❓ Часті запитання", callback_data="menu_faq"),
                 InlineKeyboardButton("🌟 Про Star for Life Ukraine", callback_data="menu_about")],
                [InlineKeyboardButton("✉️ Задати своє запитання", callback_data="menu_ask"),
                 InlineKeyboardButton("📱 Соціальні мережі", callback_data="menu_social")],
                [InlineKeyboardButton("🧾Заповнити свої данні", callback_data="menu_userdata"),
                 InlineKeyboardButton("💻 Курси", callback_data="menu_courses")],
                [InlineKeyboardButton("💬 Зворотній зв'язок", callback_data="menu_feedback"),
                 InlineKeyboardButton("⭐️ Відгуки", callback_data="menu_reviews")]
            ]
            await q.edit_message_text(DATA["Hello"], reply_markup=InlineKeyboardMarkup(kb))


async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    chat_id = update.message.chat.id  
    thread_id = getattr(update.message, "message_thread_id", None)
    data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))
    if str(u.id) in data.get("Id_ban", []):
        await update.message.reply_text("Нажаль ви були забанені")
        return
    context.bot_data['last_user'] = u.id
    source_id = u.id if update.message.chat.type == "private" else chat_id
    msg = (f"📩 Нове питання від @{u.username or 'невідомий'} (ID: {source_id})(thread_id: {thread_id}):\n\n"f"{update.message.text}")
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg, message_thread_id=1106)
    kb = [[InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]
    await update.message.reply_text("Дякую! Питання надіслано адміністратору.", reply_markup=InlineKeyboardMarkup(kb))
    return ConversationHandler.END


async def receive_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))
    if str(u.id) in data["Id_ban"]:
        await update.message.reply_text("Нажаль ви були забанені")
        return
    msg = f"Зворотній зв'язок від @{u.username or 'невідомий'} (ID: {u.id}):\n\n{update.message.text}"
    await context.bot.send_message(ADMIN_ID, msg, message_thread_id=1236)
    kb = [[InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]
    await update.message.reply_text("Дякую за ваш зворотній зв'язок!", reply_markup=InlineKeyboardMarkup(kb))
    return ConversationHandler.END

async def receive_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))
    if str(u.id) in data["Id_ban"]:
        await update.message.reply_text("Нажаль ви були забанені")
        return
    msg = f"Відгук від @{u.username or 'невідомий'} (ID: {u.id}):\n\n{update.message.text}"
    await context.bot.send_message(ADMIN_ID, msg, message_thread_id=1120)
    kb = [[InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]
    await update.message.reply_text("Дякую за ваш відгук!", reply_markup=InlineKeyboardMarkup(kb))
    return ConversationHandler.END


async def collect_data_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["id"] = update.effective_chat.id
    context.user_data["User_name"] = update.effective_user.username
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введіть ваш вік:")
    return STATE_DATA_2

async def collect_data_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text
    await update.message.reply_text("Введіть ваш e-mail:")
    return STATE_DATA_3

async def collect_data_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    user_id = str(user.id)
    username = user.username or "невідомий"
    context.user_data["email"] = update.message.text
    name = context.user_data.get("name", "—")
    age = context.user_data.get("age", "—")
    email = context.user_data.get("email", "—")

    data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))

    data["User_data"][user_id] = {
        "User_name": f"@{username}",
        "Name": name,
        "Age": age,
        "E-mail": email
    }
    with open(Path(__file__).parent / "id_users.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    await update.message.reply_text(f"✅ Дякуємо!\nВаші дані збережено:\n\n👤 ID: @{username}\n🔹 Ім'я: {name}\n🔹 Вік: {age}\n📧 E-mail: {email}")
    return ConversationHandler.END


async def HelpAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    text = f"""
            <b>Команди адміністратора (детальний опис)</b>

            ────────────────────────────
            <b>1. Зміна символу розділювача</b>
            <b>Команда:</b>
            /sb <i>символ</i>
            <b>Параметри:</b>
            символ – будь-який 1 символ
            <b>Приклад:</b>
            /sb |

            ────────────────────────────
            <b>2. Відповідь користувачу</b>
            <b>Формати:</b>
            1) <code>ID{SYMBOL}Відповідь</code>
            – особиста відповідь користувачу
            2) <code>ID{SYMBOL}ThreadID{SYMBOL}Відповідь</code>
            – відповідь в тему групи
            <b>Пояснення:</b>
            ID – Telegram ID користувача або чату
            ThreadID – ID теми
            Відповідь – текст відповіді
            <b>Приклади:</b>
            <code>123456789{SYMBOL}Дякуємо за ваше питання!</code>
            <code>-1002222333444{SYMBOL}1106{SYMBOL}Відповідь у тему</code>

            <b>Службова інформація</b>
            ID групи: <code>{update.effective_chat.id}</code>
            ID теми: <code>{update.message.message_thread_id}</code>
            """
    page = 0
    kb = [
        [InlineKeyboardButton("➡", callback_data=f"helpadmin|{page+1}")]
    ]
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


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


async def ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    ex = no = 0
    ids = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))["Id_users"]
    if update.message.photo:
        photo = update.message.photo[-1].file_id
        cap = (update.message.caption or "").replace("/ad", "").strip().split(SYMBOL)
        body = cap[0] if cap else ""
        kb = [[InlineKeyboardButton("Реєстрація", url=cap[1])]] if len(cap) == 2 else []
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
        body, kb = ("".join(txt[:-1]), [[InlineKeyboardButton("Детальніше", url=txt[-1])]]) if len(txt) > 1 else (txt[0], [])
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
        qs = [item["question"] for item in DATA["FAQs"][arg]]
        kb = [[InlineKeyboardButton(q, callback_data=f"showfaq|{arg}|{i}")] for i, q in enumerate(qs)]
        kb.append([InlineKeyboardButton("← Головне меню", callback_data="menu_main")])
        await q.edit_message_text("Оберіть запитання:", reply_markup=InlineKeyboardMarkup(kb))

    elif cmd == "course":
        course = next((c for c in DATA["ActiveCourse"]["Course"] if c["title"] == arg), None)
        if course:
            txt = course["description"]
            kb = [
                [InlineKeyboardButton("Реєстрація", callback_data=f"registration|{arg}")],
                [InlineKeyboardButton("← Головне меню", callback_data="menu_main")]
            ]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await q.edit_message_text("Курс не знайдено 😕", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Головне меню", callback_data="menu_main")]
            ]))
    
    elif cmd == "registration":
        course = next((c for c in DATA["ActiveCourse"]["Course"] if c["title"] == arg), None)
        if course:
            if course["state"] != "on":
                await q.edit_message_text("Реєстрацію закрито", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]))
                return
            data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))
            id = str(update.effective_chat.id)
            if id not in data["User_data"]:
                await q.edit_message_text("Заповніть свої данні", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]))
                return
            msg = f"    Заява про реєстрацію на курс:\n{arg}\nКористувач: {data["User_data"][id]["User_name"]}\nІм'я: {data["User_data"][id]["Name"]}\nВік: {data["User_data"][id]["Age"]}\nE-mail: {data["User_data"][id]["E-mail"]}"
            await context.bot.send_message(ADMIN_ID, msg, message_thread_id=1125)
            kb = [[InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]
            await q.edit_message_text("Заява відправлена", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await q.edit_message_text("Курс не знайдено 😕", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Головне меню", callback_data="menu_main")]
            ]))

    elif cmd == "showfaq":
        grp, idx = parts[1], int(parts[2])
        qa = DATA["FAQs"][grp][idx]
        key = qa["question"]
        ans = qa["answer"]
        txt = f"❓ {key}\n\n💬 {ans}"
        kb = [[InlineKeyboardButton("← Назад", callback_data=f"faq|{grp}")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    elif cmd == "myQ":
        await q.message.reply_text("Напишіть своє питання.")
        return STATE_ASK
    
    elif cmd == "helpadmin":

        ADMIN_PAGES = [
                f"""
            <b>Команди адміністратора (детальний опис)</b>

            ────────────────────────────
            <b>1. Зміна символу розділювача</b>
            <b>Команда:</b>
            /sb <i>символ</i>
            <b>Параметри:</b>
            символ – будь-який 1 символ
            <b>Приклад:</b>
            /sb |

            ────────────────────────────
            <b>2. Відповідь користувачу</b>
            <b>Формати:</b>
            1) <code>ID{SYMBOL}Відповідь</code>
            – особиста відповідь користувачу
            2) <code>ID{SYMBOL}ThreadID{SYMBOL}Відповідь</code>
            – відповідь в тему групи
            <b>Пояснення:</b>
            ID – Telegram ID користувача або чату
            ThreadID – ID теми
            Відповідь – текст відповіді
            <b>Приклади:</b>
            <code>123456789{SYMBOL}Дякуємо за ваше питання!</code>
            <code>-1002222333444{SYMBOL}1106{SYMBOL}Відповідь у тему</code>
            """,

                f"""
            <b>3. Додавання питання (FAQ)</b>
            <b>Команда:</b>
            /add child|adult{SYMBOL}питання{SYMBOL}відповідь
            <b>Приклад:</b>
            /add child{SYMBOL}Що таке SFL?{SYMBOL}Це міжнародний проєкт...

            ────────────────────────────
            <b>4. Видалення питання</b>
            <b>Команда:</b>
            /delete child|adult{SYMBOL}номер рахуючи зверху до низу з 1
            <b>Приклад:</b>
            /delete adult{SYMBOL}2
            """,

                f"""
            <b>5. Додавання курсу</b>
            <b>Команда:</b>
            /addcourse назва{SYMBOL}опис{SYMBOL}on|off
            <b>Приклад:</b>
            /addcourse Python Basic{SYMBOL}Курс для початківців...{SYMBOL}on

            ────────────────────────────
            <b>6. Видалення курсу</b>
            <b>Команда:</b>
            /deletecourse номер рахуючи зверху до низу з 1
            <b>Приклад:</b>
            /deletecourse 1
            """,

                f"""
            <b>7. Зміна стану реєстрації курсу</b>
            <b>Команда:</b>
            /state номер{SYMBOL}on|off (номер рахуючи зверху до низу з 1)
            <b>Приклад:</b>
            /state 1{SYMBOL}off

            ────────────────────────────
            <b>8. Розсилка користувачам</b>
            Формати:
            1) /ad текст
            2) /ad текст{SYMBOL}посилання
            3) Фото + підпис:
            /ad текст{SYMBOL}посилання
            <b>Приклади:</b>
            /ad Привіт, друзі!
            /ad Новий курс!{SYMBOL}https://example.com
            """,

                f"""
            <b>9. Блокування користувачів</b>
            <b>Команди:</b>
            /ban ID – заблокувати користувача
            /deleteban ID – розблокувати
            /alldeleteban – зняти всі блокування
            <b>Приклади:</b>
            /ban 123456789
            /deleteban 123456789
            /alldeleteban
            """
        ]

        page = int(arg)
        text = ADMIN_PAGES[page]
        kb = []
        if page > 0:
            kb.append(InlineKeyboardButton("⬅", callback_data=f"helpadmin|{page-1}"))
        if page < len(ADMIN_PAGES)-1:
            kb.append(InlineKeyboardButton("➡", callback_data=f"helpadmin|{page+1}"))
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([kb]))


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    if update.message.message_thread_id != 1143:
        return
    if  1 >= len(parts) >=4:
        await update.message.reply_text("Формат: ID$Відповідь або ID$ThreadID$Відповідь")
        return
    try:
        parts = update.message.text.split(SYMBOL)
        if len(parts) == 2:
            uid = int(parts[0].strip())
            await context.bot.send_message(uid, f"Відповідь адміністратора:\n\n{parts[1]}")
            await update.message.reply_text(f"✅ Відповідь надіслана користувачу")
            return
        if len(parts) == 3:
            chat_id = int(parts[0].strip())
            thread_id = int(parts[1].strip())
            answer = parts[2]
            params = {
                "chat_id": chat_id,
                "text": f"Відповідь адміністратора:\n\n{answer}"
            }
            if thread_id:
                params["message_thread_id"] = thread_id
            await context.bot.send_message(**params)
            await update.message.reply_text(f"✅ Відповідь надіслана користувачу")
    except Exception as e:
        await update.message.reply_text(f"⚠ Помилка: {e}")


async def add_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    if not context.args:
        return
    try:
        msg = " ".join(context.args)
        parts = msg.split(SYMBOL)
        if len(parts) != 3:
            await update.message.reply_text("❗ Формат: /add child$питання$відповідь")
            return
        grp, qt, ans = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if grp not in ["child", "adult"]:
            await update.message.reply_text("❗ Вкажіть 'child' або 'adult' як перший параметр.")
            return
        data = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
        data["FAQs"][grp].append({
            "question": qt,
            "answer": ans
        })
        with open(Path(__file__).parent / 'question.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        up_date()
        await update.message.reply_text(f"✅ Питання додано до '{grp}'.")
    except Exception as e:
        await update.message.reply_text(f"⚠ Помилка при додаванні: {e}")


async def delete_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    try:
        args = (update.message.text or "").replace("/delete", "").strip().split(SYMBOL)
        section, question = args
        question = question.strip()
        index = int(question) - 1
        section = section.strip()
        data = json.loads((Path(__file__).parent / "question.json").read_text(encoding="utf-8"))
        if section not in data["FAQs"]:
            await update.message.reply_text(f"❗ Невірний розділ. Вкажіть: child або adult.{section}")
            return
        if 0 > index or index > len(data["FAQs"][section]):
            return
        data["FAQs"][section].pop(index)
        with open(Path(__file__).parent / 'question.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        await update.message.reply_text(f"✅ Питання видалено з розділу '{section}'.")
    except Exception as e:
        await update.message.reply_text(f"⚠ Помилка: {e}")
    up_date()


async def add_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    try:
        msg = (update.message.text or "").replace("/addcourse", "").strip()
        parts = msg.split(SYMBOL)
        if len(parts) != 3:
            await update.message.reply_text(f"❗ Формат: /addcourse Назва{SYMBOL}Опис{SYMBOL}Статус on/off")
            return
        title, description, state = [p.strip() for p in parts]
        data = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
        new_course = {
            "title": title,
            "description": description,
            "state": state
        }
        data["ActiveCourse"]["Course"].append(new_course)
        with open(Path(__file__).parent / 'question.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        up_date()
        await update.message.reply_text(f"✅ Курс '{title}' додано.")
    except Exception as e:
        await update.message.reply_text(f"⚠ Помилка: {e}")


async def delete_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    try:
        msg = (update.message.text or "").replace("/deletecourse", "").strip()
        if not msg.isdigit():
            await update.message.reply_text("❗ Вкажіть номер курсу для видалення, наприклад:\n`/deletecourse 2`", parse_mode='Markdown')
            return

        index = int(msg) - 1
        data = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
        courses = data["ActiveCourse"]["Course"]
        if 0 <= index < len(courses):
            removed_course = courses.pop(index)
            with open(Path(__file__).parent / 'question.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            up_date()
            await update.message.reply_text(f"✅ Курс '{removed_course['title']}' видалено.")
        else:
            await update.message.reply_text("❗ Невірний номер курсу.")
    except Exception as e:
        await update.message.reply_text(f"⚠ Помилка: {e}")


async def Ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    msg = (update.message.text or "").replace("/ban", "").strip()
    try:
        if not msg.isdigit():
                await update.message.reply_text("❗ невірний id", parse_mode='Markdown')
                return
        data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))
        if msg not in data["Id_ban"]:
            data["Id_ban"].append(msg)
        with open(Path(__file__).parent / 'id_users.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        await update.message.reply_text(f"✅ Користувача з ID {msg} заблоковано.")
    except Exception as e:
        await update.message.reply_text(f"⚠ Помилка: {e}")


async def delete_Ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    msg = (update.message.text or "").replace("/deleteban", "").strip()
    try:
        if not msg.isdigit():
                await update.message.reply_text("❗ невірний id", parse_mode='Markdown')
                return
        data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))
        if msg in data["Id_ban"]:
            data["Id_ban"].remove(msg)
        with open(Path(__file__).parent / 'id_users.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        await update.message.reply_text(f"✅ Користувача з ID {msg} заблоковано.")
    except Exception as e:
        await update.message.reply_text(f"⚠ Помилка: {e}")


async def all_delete_Ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))
    data["Id_ban"] = ["0000000000"]
    with open(Path(__file__).parent / 'id_users.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    await update.message.reply_text("✅ Бани знято")


async def state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    try:
        msg = (update.message.text or "").replace("/state", "").strip()
        parts = msg.split(SYMBOL)

        if len(parts) != 2:
            await update.message.reply_text("Не вказані елементи")
            return
        if parts[1].strip() not in ["on", "off"]:
            await update.message.reply_text("Введіть on або off")
            return
        if not parts[0].strip().isdigit():
            await update.message.reply_text("Не вказан номер курсу")
            return
        
        data = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
        index = int(parts[0].strip()) - 1
        if not (0 <= index < len(data["ActiveCourse"]["Course"])):
            await update.message.reply_text("Невірний номер курсу")
            return
        
        data["ActiveCourse"]["Course"][index]["state"] = parts[1].strip()
        with open(Path(__file__).parent / 'question.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        up_date()
        await update.message.reply_text("✅ Статус курсу змінено")
    except Exception as e:
        await update.message.reply_text(f"⚠ Помилка: {e}")


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

    conv_userdata = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_userdata$")],
        states={
            STATE_DATA_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_1)],
            STATE_DATA_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_2)],
            STATE_DATA_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_3)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_ask)
    app.add_handler(conv_fb)
    app.add_handler(conv_rev)
    app.add_handler(conv_userdata)
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("state", state))
    app.add_handler(CommandHandler("ban", Ban))
    app.add_handler(CommandHandler("deleteban", delete_Ban))
    app.add_handler(CommandHandler("alldeleteban", all_delete_Ban))
    app.add_handler(CommandHandler("help", HelpAdmin))
    app.add_handler(CommandHandler("sb", set_symbol))
    app.add_handler(CommandHandler("add", add_question))
    app.add_handler(CommandHandler("delete", delete_question))
    app.add_handler(CommandHandler("addcourse", add_course))
    app.add_handler(CommandHandler("deletecourse", delete_course))
    app.add_handler(MessageHandler((filters.Regex(r"^/ad") | filters.CaptionRegex(r"^/ad")) & filters.Chat(ADMIN_ID), ad))
    app.add_handler(CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|registration|helpadmin)\|"))
    app.add_handler(MessageHandler(filters.Chat(ADMIN_ID) & filters.TEXT, admin_reply))

    app.run_polling(drop_pending_updates=True)

#YaroBot
#IlyaBot