import os
import io
import json
import logging
import gspread
from pathlib import Path
from textwrap import wrap
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

load_dotenv(Path(__file__).parent / '.env', encoding='utf-8-sig')
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_IDENT"))

STATE_ASK, STATE_FB, STATE_REV, STATE_UNIVERSAL, STATE_DATA_1, STATE_DATA_2, STATE_DATA_3, STATE_DATA_4, STATE_DATA_5, STATE_DATA_6, STATE_DATA_7, STATE_DATA_8, STATE_DATA_9, STATE_DATA_10, STATE_DATA_11, STATE_DATA_12 = range(1, 17)
OTHER_BENEFIT, OTHER_INFO_SOURCE, STATE_SUDO_EDIT, = range(101, 104)
DATA = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
SYMBOL = DATA["SYMBOL"]
DATA_PATH = DATA


def up_date():
    global SYMBOL
    global DATA, DATA_PATH
    DATA = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
    SYMBOL = DATA["SYMBOL"]
    DATA_PATH = DATA

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("❓ Часті запитання", callback_data="menu_faq"),
         InlineKeyboardButton("🌟 Про Star for Life Ukraine", callback_data="menu_about")],
        [InlineKeyboardButton("✉️ Задати своє запитання", callback_data="menu_ask"),
         InlineKeyboardButton("📱 Соціальні мережі", callback_data="menu_social")],
        [InlineKeyboardButton("🧾Заповнити свої дані", callback_data="menu_userdata"),
         InlineKeyboardButton("💻 Курси", callback_data="menu_courses")],
        [InlineKeyboardButton("💬 Зворотній зв'язок", callback_data="menu_feedback"),
         InlineKeyboardButton("⭐️ Відгуки", callback_data="menu_reviews")]
    ]
    await update.message.reply_text(DATA["Hello"], reply_markup=InlineKeyboardMarkup(kb))
    with open('id_users.json', 'r', encoding='utf-8') as f:
        ud = json.load(f)
    users = ud.get("Id_users", [])
    if update.effective_chat.type == "private":
        uid = str(update.effective_user.id)
    else:
        uid = str(update.effective_chat.id)
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
            kb = [[InlineKeyboardButton("✉️ Написати своє запитання", callback_data="from_client_to_admin|question")],
                  [InlineKeyboardButton("← Головне меню", callback_data="menu_main")]
                  ]
            await q.edit_message_text("Напишіть своє питання, і я передам адміністратору.", reply_markup=InlineKeyboardMarkup(kb))
            return STATE_ASK
        case "menu_feedback":
           kb = [[InlineKeyboardButton("💬 Зворотній зв'язок", callback_data="from_client_to_admin|feedback")],
                  [InlineKeyboardButton("← Головне меню", callback_data="menu_main")]
                  ]
           await q.edit_message_text("🔔 Нам дуже важлива ваша думка!\nПоділіться своїми враженнями, ідеями або зауваженнями, щоб ми ставали кращими 💬", reply_markup=InlineKeyboardMarkup(kb))
           return STATE_FB
        case "menu_reviews":
            kb = [[InlineKeyboardButton("⭐️ Відгуки", callback_data="from_client_to_admin|reviews")],
                  [InlineKeyboardButton("← Головне меню", callback_data="menu_main")]
                  ]
            await q.edit_message_text("🌟 Поділіться своїм досвідом!\nЩо сподобалось у курсі або роботі бота? Що можемо покращити?", reply_markup=InlineKeyboardMarkup(kb))
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
            kb = [[InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]
            if update.effective_chat.type != "private":
                
                await q.edit_message_text("Будь ласка, пройдіть реєстрацію, перейшовши до особистих повідомлень з ботом.", reply_markup=InlineKeyboardMarkup(kb))
                return ConversationHandler.END
            await q.edit_message_text("Введіть ваш ПІБ:\nприклад -> Северюк Лариса Іванівна", reply_markup=InlineKeyboardMarkup(kb))
            return STATE_DATA_1
        case "menu_main":
            kb = [
                [InlineKeyboardButton("❓ Часті запитання", callback_data="menu_faq"),
                 InlineKeyboardButton("🌟 Про Star for Life Ukraine", callback_data="menu_about")],
                [InlineKeyboardButton("✉️ Задати своє запитання", callback_data="menu_ask"),
                 InlineKeyboardButton("📱 Соціальні мережі", callback_data="menu_social")],
                [InlineKeyboardButton("🧾Заповнити свої дані", callback_data="menu_userdata"),
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
    kb = [[InlineKeyboardButton(f"{i}", callback_data=f"class|{i}")] for i in range(5, 12)] + [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|1")]]
    await update.message.reply_text("Напишіть у якому ви класі:", reply_markup=InlineKeyboardMarkup(kb))
    return STATE_DATA_2

async def collect_data_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.strip().isdigit():
        kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|2")]]
        await update.message.reply_text("Введіть ваш вік:\nприклад -> 13", reply_markup=InlineKeyboardMarkup(kb))
        return STATE_DATA_3
    
    context.user_data["age"] = update.message.text
    kb = [[InlineKeyboardButton(f"{i}", callback_data=f"region|{i}")] for i in DATA["Regions"]] + [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|3")]]
    await update.message.reply_text("Вкажіть область проживання:", reply_markup=InlineKeyboardMarkup(kb))
    return STATE_DATA_4


async def collect_data_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text[-10:] != "@gmail.com":
        kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|4")]]
        await update.message.reply_text("Введіть, будь ласка, ваш E-mail (електронну адресу типу ***@gmail.com). Це дуже важливо для приєднання до Google-класу.", reply_markup=InlineKeyboardMarkup(kb))
        return STATE_DATA_5

    context.user_data["email"] = text
    kb = [[InlineKeyboardButton(f"Так", callback_data=f"havepc|YES")], [InlineKeyboardButton(f"Ні", callback_data=f"havepc|NO")]] + [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|5")]]
    await update.message.reply_text("Чи є у вас ПК або ноутбук, на якому ви зможете навчатись? (ОС Windows або Linux. Вимоги до процесора та оперативної пам'яті мінімальні.)", reply_markup=InlineKeyboardMarkup(kb))
    return STATE_DATA_6


async def collect_data_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["school"] = update.message.text.strip()
    kb = [
        [InlineKeyboardButton("♂ Чоловіча", callback_data="gender|men")],
        [InlineKeyboardButton("♀ Жіноча", callback_data="gender|women")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|7")]
    ]
    await update.message.reply_text("Вкажіть стать:", reply_markup=InlineKeyboardMarkup(kb))
    return STATE_DATA_8


async def collect_data_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not(text[:4] == "+380" and len(text) == 13 and text[1:].isdigit()):
        kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|8")]]
        await update.message.reply_text("Вкажіть ваш номер телефону (+380...):", reply_markup=InlineKeyboardMarkup(kb))
        return STATE_DATA_9
    context.user_data["namberphone"] = update.message.text.strip()
    kb = [
        [InlineKeyboardButton("Не маю пільг", callback_data="benefit|no_benefits")],
        [InlineKeyboardButton("ВПО", callback_data="benefit|idp")],
        [InlineKeyboardButton("Багатодітна сім'я", callback_data="benefit|large_family")],
        [InlineKeyboardButton("Малозабезпечена сім'я", callback_data="benefit|low_income")],
        [InlineKeyboardButton("Сім’я, що виховує дитину з інвалідністю", callback_data="benefit|disabled_child")],
        [InlineKeyboardButton("Сім’я загиблого (померлого) військовослужбовця", callback_data="benefit|fallen_soldier")],
        [InlineKeyboardButton("Сім’я військовослужбовця (учасника бойових дій)", callback_data="benefit|military_family")],
        [InlineKeyboardButton("Прийомна сім’я / дитячий будинок сімейного типу", callback_data="benefit|foster_family")],
        [InlineKeyboardButton("Інше (вкажіть)", callback_data="benefit|other")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|9")]
    ]
    await update.message.reply_text("Чи є у вас пільги? (якщо маєте інші пільги, вкажіть їх у 'Інше')", reply_markup=InlineKeyboardMarkup(kb))
    return STATE_DATA_10


async def other_benefit_text(update, context):
    text = update.message.text.strip()
    context.user_data["benefit"] = text

    kb = [
        [InlineKeyboardButton("Соціальні мережі SfL", callback_data="info_source|social_networks")],
        [InlineKeyboardButton("Розказали у школі, в якій навчаюсь", callback_data="info_source|from_school")],
        [InlineKeyboardButton("Інше (вкажіть)", callback_data="info_source|other")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|9")]
    ]
    await update.message.reply_text("Вкажіть, звідки ви дізнались про дану школу?", reply_markup=InlineKeyboardMarkup(kb))
    return STATE_DATA_11


async def other_info_source_text(update, context):
    text = update.message.text.strip()
    context.user_data["info_source"] = text

    kb = [
        [InlineKeyboardButton("Так", callback_data="consent|yes")],
        [InlineKeyboardButton("Ні", callback_data="consent|no")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|10")]
    ]
    await update.message.reply_text("Я даю згоду Star for Life Ukraine на обробку моїх персональних даних в рамках цього курсу", reply_markup=InlineKeyboardMarkup(kb))
    return STATE_DATA_12


async def HelpAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    text = f"""
        <b>Команди адміністратора (детальний опис)</b>

        ────────────────────────────
        <b>1. Зміна символу розділювача</b>
        <b>Команда:</b>
        /sb <i>символ</i>
        <b>Пояснення:</b>
        Команді передається один символ, який буде використаний як розділювач.
        Цей символ не повинен зустрічатися в інших аргументах(зараз {SYMBOL}).
        <b>Приклад:</b>
        /sb $
        
        ────────────────────────────
        <b>2. Повідомлення про помилки</b>
        Якщо у команді буде допущена помилка, бот вкаже, де саме вона виникла. 
        Перевірте ще раз команду та правильність використання спецсимволів.

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
    
    elif cmd == "from_client_to_admin":
        match arg:
            case "question":
                await q.edit_message_text("Напишіть Ваше повідомлення нижче та відправте")
                return STATE_UNIVERSAL
            case "feedback":
                await q.edit_message_text("Напишіть Ваше повідомлення нижче та відправте")
                return STATE_UNIVERSAL
            case "reviews":
                await q.edit_message_text("Напишіть Ваше повідомлення нижче та відправте")
                return STATE_UNIVERSAL

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
                await q.edit_message_text("Реєстрацію закрито.\nПеревірте дату реєстрації", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]))
                return
            data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))
            id = str(update.effective_chat.id)
            if id not in data["User_data"]:
                await q.edit_message_text("📋 Щоб зареєструватися, спочатку заповніть свої дані.", reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📝 Заповнити дані", callback_data="menu_userdata")],
                        [InlineKeyboardButton("← Головне меню", callback_data="menu_main")]
                    ]))
                return
            user_data = data["User_data"][id]
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            client = gspread.authorize(creds)
            spreadsheet = client.open(course["table"])
            sheet = spreadsheet.get_worksheet(int(course["sheet"]) - 1)
            existing_ids = sheet.col_values(1)  
            if id not in existing_ids:
                sheet.append_row([
                    id,
                    user_data.get("User_name", ""),
                    user_data.get("Name", ""),
                    user_data.get("Age", ""),
                    user_data.get("namberphone", ""),
                    user_data.get("apparatus", ""),
                    user_data.get("class", ""),
                    user_data.get("regions", ""),
                    user_data.get("school", ""),
                    user_data.get("gender", ""),
                    user_data.get("E-mail", ""),
                    user_data.get("benefit", ""),
                    user_data.get("info_source", "")
                ])
            msg = (
                f"📥 Заява про реєстрацію на курс: {arg}\n\n"
                f"👤 ID: {id}\n"
                f"👤 Користувач: {user_data['User_name']}\n"
                f"🔹 Ім'я: {user_data['Name']}\n"
                f"🔹 Вік: {user_data['Age']}\n"
                f"📱 Номер телефону: {user_data['namberphone']}\n"
                f"💻 Наявність пристрою: {user_data['apparatus']}\n"
                f"📘 Клас: {user_data['class']}\n"
                f"🌆 Область / ВПО: {user_data['regions']}\n"
                f"🏫 Навчальний заклад: {user_data['school']}\n"
                f"⚧ Стать: {user_data['gender']}\n"
                f"📧 E-mail: {user_data['E-mail']}\n"
                f"🎓 Пільги: {user_data['benefit']}\n"
                f"📣 Джерело інформації: {user_data['info_source']}"
            )

            await context.bot.send_message(ADMIN_ID, msg, message_thread_id=1125)
            kb = [[InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]
            await q.edit_message_text(f"Заява відправлена, перейдіть {course["url"]}", reply_markup=InlineKeyboardMarkup(kb))
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
    elif cmd == "back_to_":
        num = int(arg)
        match num:
            case 1:
                kb = [[InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]
                await q.edit_message_text("Введіть ваш ПІБ:\nприклад -> Северюк Лариса Іванівна", reply_markup=InlineKeyboardMarkup(kb))
                return STATE_DATA_1

            case 2:
                kb = [[InlineKeyboardButton(f"{i}", callback_data=f"class|{i}")] for i in range(5, 12)] + [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|1")]]
                await q.edit_message_text("Напишіть у якому ви класі:", reply_markup=InlineKeyboardMarkup(kb))
                return STATE_DATA_2

            case 3:
                kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|2")]]
                await q.edit_message_text("Введіть ваш вік:\nприклад -> 13", reply_markup=InlineKeyboardMarkup(kb))
                return STATE_DATA_3

            case 4:
                kb = [[InlineKeyboardButton(f"{i}", callback_data=f"region|{i}")] for i in DATA["Regions"]] + [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|3")]]
                await q.edit_message_text("Вкажіть область проживання:", reply_markup=InlineKeyboardMarkup(kb))
                return STATE_DATA_4

            case 5:
                kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|4")]]
                await q.edit_message_text("Введіть, будь ласка, ваш E-mail (електронну адресу типу ***@gmail.com). Це дуже важливо для приєднання до Google-класу.", reply_markup=InlineKeyboardMarkup(kb))
                return STATE_DATA_5

            case 6:
                kb = [[InlineKeyboardButton(f"Так", callback_data=f"havepc|YES")], [InlineKeyboardButton(f"Ні", callback_data=f"havepc|NO")]] + [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|5")]]
                await q.edit_message_text("Чи є у вас ПК або ноутбук, на якому ви зможете навчатись? (ОС Windows або Linux. Вимоги до процесора та оперативної пам'яті мінімальні.)", reply_markup=InlineKeyboardMarkup(kb))
                return STATE_DATA_6

            case 7:
                kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|6")]]
                await q.edit_message_text("Вкажіть назву школи, у якій ви навчаєтесь:", reply_markup=InlineKeyboardMarkup(kb))
                return STATE_DATA_7

            case 8:
                kb = [
                    [InlineKeyboardButton("♂ Чоловіча", callback_data="gender|men")],
                    [InlineKeyboardButton("♀ Жіноча", callback_data="gender|women")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|7")]
                ]
                await q.edit_message_text("Вкажіть стать:", reply_markup=InlineKeyboardMarkup(kb))
                return STATE_DATA_8

            case 9:
                kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|8")]]
                await q.edit_message_text("Вкажіть ваш номер телефону (+380...):", reply_markup=InlineKeyboardMarkup(kb))
                return STATE_DATA_9

            case 10:
                kb = [
                    [InlineKeyboardButton("Не маю пільг", callback_data="benefit|no_benefits")],
                    [InlineKeyboardButton("ВПО", callback_data="benefit|idp")],
                    [InlineKeyboardButton("Багатодітна сім'я", callback_data="benefit|large_family")],
                    [InlineKeyboardButton("Малозабезпечена сім'я", callback_data="benefit|low_income")],
                    [InlineKeyboardButton("Сім’я, що виховує дитину з інвалідністю", callback_data="benefit|disabled_child")],
                    [InlineKeyboardButton("Сім’я загиблого (померлого) військовослужбовця", callback_data="benefit|fallen_soldier")],
                    [InlineKeyboardButton("Сім’я військовослужбовця (учасника бойових дій)", callback_data="benefit|military_family")],
                    [InlineKeyboardButton("Прийомна сім’я / дитячий будинок сімейного типу", callback_data="benefit|foster_family")],
                    [InlineKeyboardButton("Інше (вкажіть)", callback_data="benefit|other")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|9")]
                ]
                await q.edit_message_text("Чи є у вас пільги? (якщо маєте інші пільги, вкажіть їх у 'Інше')", reply_markup=InlineKeyboardMarkup(kb))
                return STATE_DATA_10

            case 11:
                kb = [
                    [InlineKeyboardButton("Соціальні мережі SFL", callback_data="info_source|social_networks")],
                    [InlineKeyboardButton("Розказали у школі, в якій навчаюсь", callback_data="info_source|from_school")],
                    [InlineKeyboardButton("Інше (вкажіть)", callback_data="info_source|other")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|10")]
                ]
                await q.edit_message_text("Вкажіть, звідки ви дізнались про дану школу?", reply_markup=InlineKeyboardMarkup(kb))
                return STATE_DATA_11
            

    elif cmd == "class":
        context.user_data["class"] = arg
        kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|2")]]
        await q.edit_message_text("Введіть ваш вік:\nприклад -> 13", reply_markup=InlineKeyboardMarkup(kb))
        return STATE_DATA_3
    
    elif cmd == "region":
        context.user_data["regions"] = arg
        kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|4")]]
        await q.edit_message_text("Введіть, будь ласка, ваш E-mail (електронну адресу типу ***@gmail.com). Це дуже важливо для приєднання до Google-класу.", reply_markup=InlineKeyboardMarkup(kb))
        return STATE_DATA_5
    
    elif cmd == "havepc":
        context.user_data["havepc"] = "Так" if arg == "YES" else "Ні"
        kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|6")]]
        await q.edit_message_text("Вкажіть назву школи, у якій ви навчаєтесь:", reply_markup=InlineKeyboardMarkup(kb))
        return STATE_DATA_7
    
    elif cmd == "gender":
        if arg == "men":
            context.user_data["gender"] = "Чоловіча"
        elif arg == "women":
            context.user_data["gender"] = "Жіноча"
        kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|8")]]
        await q.edit_message_text("Вкажіть ваш номер телефону (+380...):", reply_markup=InlineKeyboardMarkup(kb))
        return STATE_DATA_9
    
    elif cmd == "benefit":
        if arg == "other":
            await q.edit_message_text("📝 Введіть, будь ласка, вашу пільгу:")
            return OTHER_BENEFIT
        else:
            benefit_map = {
                "no_benefits": "Не маю пільг",
                "idp": "Сім’я внутрішньо переміщених осіб (ВПО)",
                "large_family": "Багатодітна сім'я",
                "low_income": "Малозабезпечена сім'я",
                "disabled_child":"Сім’я, що виховує дитину з інвалідністю",
                "fallen_soldier":"Сім’я загиблого (померлого) військовослужбовця",
                "military_family":"Сім’я військовослужбовця (учасника бойових дій)",
                "foster_family":"Прийомна сім’я / дитячий будинок сімейного типу"
            }
            context.user_data["benefit"] = benefit_map.get(arg, arg)
            kb = [
                [InlineKeyboardButton("Соціальні мережі SFL", callback_data="info_source|social_networks")],
                [InlineKeyboardButton("Розказали у школі, в якій навчаюсь", callback_data="info_source|from_school")],
                [InlineKeyboardButton("Інше", callback_data="info_source|other")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|10")]
            ]
            await q.edit_message_text("Вкажіть, звідки ви дізнались про дану школу?", reply_markup=InlineKeyboardMarkup(kb))
            return STATE_DATA_11
        
    elif cmd == "info_source":
        if arg == "other":
            await q.edit_message_text("📝 Введіть, будь ласка, звідки ви дізнались про SFL ua:")
            return OTHER_INFO_SOURCE
        else:
            info_map = {
                "social_networks": "Соціальні мережі SFL",
                "from_school": "Розказали у школі, в якій навчаюсь"
            }
            context.user_data["info_source"] = info_map.get(arg, arg)
            kb = [
                [InlineKeyboardButton("Так", callback_data="consent|yes")],
                [InlineKeyboardButton("Ні", callback_data="consent|no")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_|11")]
            ]
            await q.edit_message_text("Я даю згоду Star for Life Ukraine на обробку моїх персональних даних в рамках цього курсу", reply_markup=InlineKeyboardMarkup(kb))
            return STATE_DATA_12
    
    elif cmd == "consent":
        if arg == "no":
            context.user_data["consent"] = "Ні"
            kb = [
                [InlineKeyboardButton("Так", callback_data="consent|yes")],
                [InlineKeyboardButton("Ні", callback_data="consent|no")],
                [InlineKeyboardButton("Зтерти дані", callback_data="consent|del")]
            ]
            await q.edit_message_text("На жаль, без цього неможливо зареєструватися.\nЯ даю згоду Star for Life Ukraine на обробку моїх персональних даних у межах цього курсу.", reply_markup=InlineKeyboardMarkup(kb))
            return STATE_DATA_12
        elif arg == "del":
            kb = [[InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]
            await q.edit_message_text("Дані зтерто", reply_markup=InlineKeyboardMarkup(kb))
            return ConversationHandler.END
        else:
            context.user_data["consent"] = "Так"
        
        user_id = str(context.user_data.get("id", "—"))
        username = context.user_data.get("User_name", "—")
        name = context.user_data.get("name", "—")
        age = context.user_data.get("age", "—")
        email = context.user_data.get("email", "—")
        user_class = context.user_data.get("class", "—")
        regions = context.user_data.get("regions", "—")
        school = context.user_data.get("school", "—")
        gender = context.user_data.get("gender", "—")
        namberphone = context.user_data.get("namberphone", "—")
        benefit = context.user_data.get("benefit", "—")
        info_source = context.user_data.get("info_source", "—")
        havepc =context.user_data.get("havepc", "—")

        data = json.loads((Path(__file__).parent / 'id_users.json').read_text(encoding='utf-8'))

        data["User_data"][user_id] = {
            "User_name": f"@{username}",
            "Name": name,
            "Age": age,
            "namberphone": namberphone,
            "apparatus": havepc,
            "class": user_class,
            "regions": regions,
            "school": school,
            "gender": gender,
            "E-mail": email,
            "benefit": benefit,
            "info_source": info_source
        }

        with open(Path(__file__).parent / "id_users.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        user_data = data["User_data"][user_id]
        
        kb = [[InlineKeyboardButton("💻 Курси", callback_data="menu_courses")], [InlineKeyboardButton("📱 Соціальні мережі", callback_data="menu_social")], [InlineKeyboardButton("← Головне меню", callback_data="menu_main")]]
        await update.callback_query.edit_message_text(
                f"📥 Якщо дані зміняться знов пройдіть реєстрацію\n\n"
                f"👤 ID: {user_id}\n"
                f"👤 Користувач: {user_data['User_name']}\n"
                f"🔹 Ім'я: {user_data['Name']}\n"
                f"🔹 Вік: {user_data['Age']}\n"
                f"📱 Номер телефону: {user_data['namberphone']}\n"
                f"💻 Наявність пристрою: {user_data['apparatus']}\n"
                f"📘 Клас: {user_data['class']}\n"
                f"🌆 Область / ВПО: {user_data['regions']}\n"
                f"🏫 Навчальний заклад: {user_data['school']}\n"
                f"⚧ Стать: {user_data['gender']}\n"
                f"📧 E-mail: {user_data['E-mail']}\n"
                f"🎓 Пільги: {user_data['benefit']}\n"
                f"📣 Джерело інформації: {user_data['info_source']}\n"
                f"РЕЄСТРУЙСЯ НА КУРСИ\n📲 Долучайся до наших соцмереж — саме там з’являються анонси нових подій:",
                reply_markup=InlineKeyboardMarkup(kb)
        )
        return ConversationHandler.END
    
    elif cmd == "sudo":
        global DATA_PATH
        if "sudo_path" not in context.user_data:
            context.user_data["sudo_path"] = []
        if arg == "back":
            if context.user_data["sudo_path"]:
                context.user_data["sudo_path"].pop()
        elif arg == "edit":
            path = context.user_data["sudo_path"].copy()
            if not path:  
                context.user_data["sudo_parent_path"] = []
                context.user_data["sudo_edit_key"] = None
            else:
                context.user_data["sudo_parent_path"] = path[:-1]
                context.user_data["sudo_edit_key"] = path[-1]
            await q.edit_message_text("✏️ Введіть нове значення:")
            return STATE_SUDO_EDIT
        elif arg not in ("back", "edit"):
            d = int(arg) if arg.isdigit() else arg
            context.user_data["sudo_path"].append(d)
        data = DATA_PATH
        try:
            for key in context.user_data["sudo_path"]:
                data = data[key]
        except (KeyError, IndexError, TypeError):
            await q.answer("❌ Невірний ключ")
            return
        kb = []
        if isinstance(data, dict):
            kb = [[InlineKeyboardButton(str(k), callback_data=f"sudo|{k}")] for k in data.keys()]
            text = "🔸 Виберіть поле:"
        elif isinstance(data, list):
            kb = [[InlineKeyboardButton(str(i+1), callback_data=f"sudo|{i}")] for i in range(len(data))]
            text = "🔸 Виберіть елемент:"
        else:
            text = f"📄 Значення:\n\n<pre>{data}</pre>"
            kb = [[InlineKeyboardButton("📄Редагувати", callback_data=f"sudo|edit")]]
        if context.user_data["sudo_path"]:
            kb.append([InlineKeyboardButton("← Назад", callback_data="sudo|back")])
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb) if kb else None)


        
    elif cmd == "helpadmin":

        ADMIN_PAGES = [
            f"""
        <b>Команди адміністратора (детальний опис)</b>

        ────────────────────────────
        <b>1. Зміна символу розділювача</b>
        <b>Команда:</b>
        /sb <i>символ</i>
        <b>Пояснення:</b>
        Команді передається один символ, який буде використаний як розділювач.
        Цей символ не повинен зустрічатися в інших аргументах(зараз {SYMBOL}).
        <b>Приклад:</b>
        /sb $
        
        ────────────────────────────
        <b>2. Повідомлення про помилки</b>
        Якщо у команді буде допущена помилка, бот вкаже, де саме вона виникла. 
        Перевірте ще раз команду та правильність використання спецсимволів.
            """,

            f"""
        <b>3. Відповідь користувачу</b>
        <b>Формати:</b>
        1) <code>ID{SYMBOL}Відповідь</code> – особиста відповідь користувачу  
        2) <code>ID{SYMBOL}ThreadID{SYMBOL}Відповідь</code> – відповідь у тему групи  

        <b>Пояснення:</b>  
        ID – Telegram ID користувача або чату  
        ThreadID – ID теми  
        Відповідь – текст відповіді  

        <b>Приклади:</b>  
        <code>123456789{SYMBOL}Дякуємо за ваше питання!</code>  
        <code>-1002222333444{SYMBOL}1106{SYMBOL}Відповідь у тему</code>
            """,

            f"""
        <b>4. Додавання питання (FAQ)</b>
        <b>Команда:</b>
        /add child|adult{SYMBOL}питання{SYMBOL}відповідь
        <b>Приклад:</b>
        /add child{SYMBOL}Що таке SFL?{SYMBOL}Це міжнародний проєкт...

        ────────────────────────────
        <b>5. Видалення питання</b>
        <b>Команда:</b>
        /delete child|adult{SYMBOL}номер
        <b>Пояснення:</b>
        Номер рахується зверху донизу, починаючи з 1.
        <b>Приклад:</b>
        /delete adult{SYMBOL}2
            """,

            f"""
        <b>6. Додавання курсу</b>
        <b>Команда:</b>
        /addcourse назва{SYMBOL}опис{SYMBOL}on|off
        <b>Приклад:</b>
        /addcourse Python Basic{SYMBOL}Курс для початківців...{SYMBOL}on

        ────────────────────────────
        <b>7. Видалення курсу</b>
        <b>Команда:</b>
        /deletecourse номер
        <b>Приклад:</b>
        /deletecourse 1
            """,

            f"""
        <b>8. Зміна стану реєстрації курсу</b>
        <b>Команда:</b>
        /state номер{SYMBOL}on|off

        <b>Пояснення:</b>
        Дозволяє вмикати або вимикати реєстрацію на курс.  
        Номер курсу вказується зверху донизу, починаючи з 1.  

        <b>Приклади:</b>
        /state 1{SYMBOL}off — вимикає перший курс  
        /state 2{SYMBOL}on — вмикає другий курс  

        <b>Розширений формат:</b>  
        /state номер{SYMBOL}on|off{SYMBOL}TableName{SYMBOL}номер_листа  
        <b>Приклад:</b>  
        /state 1{SYMBOL}on{SYMBOL}Таблиця з даними{SYMBOL}2

        ────────────────────────────
        <b>9. Зміна URL курсу</b>
        <b>Команда:</b>
        /url номер{SYMBOL}посилання
        <b>Пояснення:</b>
        Номер — це номер курсу у списку.  
        Посилання — повна URL-адреса (Telegram-група, контактні дані).  
        <b>Приклад:</b>
        /url 1{SYMBOL}https://example.com
            """,

            f"""
        <b>10. Розсилка</b>
        <b>Формати:</b>
        1) /ad текст  
        2) /ad текст{SYMBOL}посилання  
        3) /ad <i>Фото + підпис</i>  
        4) /ad текст{SYMBOL}посилання + фото  
        5) /ad Фото + посилання

        <b>Пояснення:</b>
        – Фото повинно бути у стислому форматі Telegram (не файлом).  
        – Замість посилання буде кнопка для переходу.  
        – Якщо хоча б 1 користувачу доставлено — розсилка вважається успішною.  

        <b>Приклади:</b>
        /ad Привіт, друзі!  
        /ad Новий курс!{SYMBOL}https://example.com
            """,

            f"""
        <b>11. Блокування користувачів</b>
        <b>Команди:</b>
        /ban ID – заблокувати користувача  
        /deleteban ID – розблокувати користувача  
        /alldeleteban – зняти всі блокування  

        <b>Приклади:</b>  
        /ban 123456789  
        /deleteban 123456789  
        /alldeleteban
            """,

            f"""
        <b>12. Найвищі можливості SUDO</b>
        1) <code>/json sudo</code> – перегляд та редагування будь-якого значення (курси, питання, тексти тощо).  
        2) Заміна файлу: можна відправити файл у Telegram (question.json або credentials.json).  
        ⚠ Будьте обережні: старий файл заміниться новим.  
        3) Запитати актуальний <code>question.json</code> – команда: <code>/json sudor</code>
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
    try:
        parts = update.message.text.split(SYMBOL)
        if  1 >= len(parts) or len(parts) >=4:
            await update.message.reply_text("Формат: ID$Відповідь або ID$ThreadID$Відповідь")
            return
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


async def set_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    try:
        data = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
        msg = (update.message.text or "").replace("/url", "").strip()
        parts = msg.split(SYMBOL)
        index = int(parts[0].strip()) - 1
        if index < 0 or index >= len(data["ActiveCourse"]):
            await update.message.reply_text("❌ Неправильний номер курсу")
            return
        data["ActiveCourse"]["Course"][index]["url"] = str(parts[1].strip())
        with open(Path(__file__).parent / 'question.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        await update.message.reply_text(f"✅Посилання додано")
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
            "state": state,
            "url": None,
            "table": None,
            "sheet": None
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
        data = json.loads((Path(__file__).parent / 'question.json').read_text(encoding='utf-8'))
        match len(parts):
            case 2:
                if parts[1].strip() not in ["on", "off"]:
                    await update.message.reply_text("Введіть on або off")
                    return
                if not parts[0].strip().isdigit():
                    await update.message.reply_text("Не вказан номер курсу")
                    return
                index = int(parts[0].strip()) - 1
                if not (0 <= index < len(data["ActiveCourse"]["Course"])):
                    await update.message.reply_text("Невірний номер курсу")
                    return
                data["ActiveCourse"]["Course"][index]["state"] = parts[1].strip()
            case 4:
                if parts[1].strip() not in ["on", "off"]:
                    await update.message.reply_text("Введіть on або off")
                    return
                if not parts[0].strip().isdigit():
                    await update.message.reply_text("Не вказан номер курсу")
                    return
                if not parts[3].strip().isdigit():
                    await update.message.reply_text("Не вказан номер листа")
                    return
                index = int(parts[0].strip()) - 1
                if not (0 <= index < len(data["ActiveCourse"]["Course"])):
                    await update.message.reply_text("Невірний номер курсу")
                    return
                data["ActiveCourse"]["Course"][index]["state"] = parts[1].strip()
                data["ActiveCourse"]["Course"][index]["table"] = parts[2].strip()
                data["ActiveCourse"]["Course"][index]["sheet"] = parts[3].strip()
        
        with open(Path(__file__).parent / 'question.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        up_date()
        await update.message.reply_text("✅ Статус курсу змінено")
    except Exception as e:
        await update.message.reply_text(f"⚠ Помилка: {e}")


async def json_rwx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    global DATA
    msg = (update.message.text or "").replace("/json", "").strip()

    if msg == "sudor":
        if isinstance(DATA, (dict, list)):
            text = json.dumps(DATA, ensure_ascii=False, indent=4)
        else:
            text = str(DATA)
        file = io.BytesIO(text.encode("utf-8"))
        file.name = "question.json"
        await update.message.reply_document(document=file, filename="question.json")
        return
    
    if msg != "sudo":
        return
    context.user_data["sudo_path"] = []
    DATA_PATH = DATA
    context.user_data["chat_id"] = update.effective_chat.id
    context.user_data["thread_id"] = update.message.message_thread_id
    kb = [[InlineKeyboardButton(str(k), callback_data=f"sudo|{k}")]for k in DATA_PATH]
    await update.message.reply_text( "🔍 Виберіть ключ/елемент:", reply_markup=InlineKeyboardMarkup(kb))
    return ConversationHandler.END


def smart_parse(value: str):
    lower = value.strip().lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower == "null":
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def get_by_path(data, path):
    for key in path:
        data = data[key]
    return data



async def sudo_edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text
    global DATA
    parent_path = context.user_data.get("sudo_parent_path", [])
    edit_key = context.user_data.get("sudo_edit_key")
    try:
        parsed_value = smart_parse(new_value)
        if edit_key is None:
            DATA = parsed_value
        else:
            parent = get_by_path(DATA, parent_path)
            if not isinstance(parent, (dict, list)):
                await update.message.reply_text("❌ Неможливо змінити це значення.")
                return ConversationHandler.END
            parent[edit_key] = parsed_value
        with open(Path(__file__).parent / 'question.json', 'w', encoding='utf-8') as f:
            json.dump(DATA, f, ensure_ascii=False, indent=4)
        up_date()

        await update.message.reply_text("✅ Значення оновлено та збережено.")
        return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text(f"⚠️ Помилка при оновленні: {e}")
        return ConversationHandler.END



async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return
    document = update.message.document
    file_name = document.file_name
    if file_name != "question.json" and file_name != "credentials.json":
        await update.message.reply_text("Можно заменить только файл question.json або credentials.json")
        return
    
    new_file = await document.get_file()
    file_path = os.path.join(os.getcwd(), file_name)  
    if os.path.exists(file_path):
        os.remove(file_path)
    await new_file.download_to_drive(file_path)
    await update.message.reply_text(f"Файл {file_name} успешно заменён.")
    up_date()




if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    conv_ask = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_ask$")],
        states={
            STATE_UNIVERSAL: [CallbackQueryHandler(ClikButton, pattern="^(faq|from_client_to_admin|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent|sudo)\|")],
            STATE_ASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)]
            },
        fallbacks=[]
    )
    conv_fb = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_feedback$")],
        states={
            STATE_UNIVERSAL: [CallbackQueryHandler(ClikButton, pattern="^(faq|from_client_to_admin|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent|sudo)\|")],
            STATE_FB: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_feedback)]
            },
        fallbacks=[]
    )
    conv_rev = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_reviews$")],
        states={
            STATE_UNIVERSAL: [CallbackQueryHandler(ClikButton, pattern="^(faq|from_client_to_admin|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent|sudo)\|")],
            STATE_REV: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_review)]
            },
        fallbacks=[]
    )

    conv_userdata = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_userdata$")],
        states={
            STATE_DATA_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_1)],
            STATE_DATA_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_2)],
            STATE_DATA_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_3)],
            STATE_DATA_4: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            STATE_DATA_5: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            STATE_DATA_6: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_4)],
            STATE_DATA_7: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_5)],
            STATE_DATA_8: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            STATE_DATA_9: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            STATE_DATA_10: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            OTHER_BENEFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, other_benefit_text)],
            STATE_DATA_11: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            OTHER_INFO_SOURCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, other_info_source_text)],
            STATE_DATA_12: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
        },
        fallbacks=[],
    )

    conv_userdata = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_userdata$")],
        states={
            STATE_DATA_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_1)],
            STATE_DATA_2: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            STATE_DATA_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_2)],
            STATE_DATA_4: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            STATE_DATA_5: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_3)],
            STATE_DATA_6: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            STATE_DATA_7: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_4)],
            STATE_DATA_8: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            STATE_DATA_9: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data_5)],
            STATE_DATA_10: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            OTHER_BENEFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, other_benefit_text)],
            STATE_DATA_11: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
            OTHER_INFO_SOURCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, other_info_source_text)],
            STATE_DATA_12: [CallbackQueryHandler(ClikButton, pattern="^(faq|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent)\|")],
        },
        fallbacks=[],
    )

    conv_sudo = ConversationHandler(
        entry_points=[CallbackQueryHandler(ClikButton, pattern="^sudo\|")],
        states={
            STATE_SUDO_EDIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sudo_edit_handler)
            ]
        },
        fallbacks=[],
    )


    app.add_handler(conv_ask)
    app.add_handler(conv_fb)
    app.add_handler(conv_rev)
    app.add_handler(conv_userdata)
    app.add_handler(conv_sudo)
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("json", json_rwx))
    app.add_handler(CommandHandler("state", state))
    app.add_handler(CommandHandler("url", set_url))
    app.add_handler(CommandHandler("ban", Ban))
    app.add_handler(CommandHandler("deleteban", delete_Ban))
    app.add_handler(CommandHandler("alldeleteban", all_delete_Ban))
    app.add_handler(CommandHandler("help", HelpAdmin))
    app.add_handler(CommandHandler("sb", set_symbol))
    app.add_handler(CommandHandler("add", add_question))
    app.add_handler(CommandHandler("delete", delete_question))
    app.add_handler(CommandHandler("addcourse", add_course))
    app.add_handler(CommandHandler("deletecourse", delete_course))
    app.add_handler(MessageHandler(filters.Document.FileExtension("json"), handle_file))
    app.add_handler(MessageHandler((filters.Regex(r"^/ad") | filters.CaptionRegex(r"^/ad")) & filters.Chat(ADMIN_ID), ad))
    app.add_handler(CallbackQueryHandler(on_main_menu_pressed, pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(ClikButton, pattern="^(faq|from_client_to_admin|course|showfaq|myQ|back_to_|registration|helpadmin|class|region|havepc|gender|benefit|info_source|consent|sudo)\|"))
    app.add_handler(MessageHandler(filters.Chat(ADMIN_ID) & filters.TEXT, admin_reply))

    app.run_polling(drop_pending_updates=True)

#YaroBot
#IlyaBot