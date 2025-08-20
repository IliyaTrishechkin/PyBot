from dotenv import load_dotenv
load_dotenv()

import os, asyncio, json, re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from telegram import Bot

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_IDENT", "0"))
QUESTION_JSON_PATH = os.getenv("QUESTION_JSON_PATH", "question.json")
USERS_DB_PATH = os.getenv("USERS_DB_PATH", "users_web.json")
REG_DB_PATH = os.getenv("REG_DB_PATH", "registrations.jsonl")

bot = Bot(token=BOT_TOKEN)

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

ALLOWED_ORIGINS = [
    "https://www.sflua.org",
    "https://sflua.org",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,
    max_age=3600,
)
app.mount("/static", StaticFiles(directory="static"), name="static")

chat_store = defaultdict(list)
menu_state = defaultdict(lambda: {"stack": [], "mode": None, "ctx": {}})

GENDER_OPTS = ["Хлопець", "Дівчина", "Інше"]
BENEFIT_OPTS = ["Немає", "Багатодітна", "Малозабезпечена", "Інше"]
SOURCE_OPTS = ["Друзі/знайомі", "Школа/вчитель", "Соцмережі", "Інше"]
CONSENT_OPTS = ["Так, даю згоду", "Ні"]

Q_CACHE = {"path": QUESTION_JSON_PATH, "mtime": None, "data": {}}

def get_Q():
    p = Path(Q_CACHE["path"])
    if p.exists():
        m = p.stat().st_mtime
        if m != Q_CACHE["mtime"]:
            try:
                Q_CACHE["data"] = json.loads(p.read_text(encoding="utf-8"))
                Q_CACHE["mtime"] = m
            except Exception:
                pass
    return Q_CACHE["data"] or {}

def main_map(Q: dict) -> dict:
    labels = Q.get("MainMenu", []) or []
    m = {}
    for lab in labels:
        low = lab.lower()
        if "star for life" in low or "про star" in low:
            m["about"] = lab
        elif "faq" in low or "пошир" in low or "част" in low or "питан" in low:
            m["faq"] = lab
        elif "соц" in low or "мереж" in low:
            m["social"] = lab
        elif "курс" in low:
            m["courses"] = lab
        elif "дан" in low or "анкета" in low:
            m["userdata"] = lab
        elif "задати" in low or "питання" in low:
            m["ask"] = lab
        elif "зворот" in low:
            m["feedback"] = lab
        elif "відгук" in low:
            m["reviews"] = lab
    return m

def valid_age(v: str) -> bool:
    return v.isdigit() and 5 <= int(v) <= 99

def valid_email(v: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v))

def valid_phone_ua(v: str) -> bool:
    return bool(re.match(r"^\+380\d{9}$", v))

def _load_users_db() -> dict:
    p = Path(USERS_DB_PATH)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_users_db(db: dict):
    Path(USERS_DB_PATH).write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

def store_user_data(sess: str, form: dict):
    db = _load_users_db()
    db[sess] = {**form, "session_id": sess, "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z"}
    _save_users_db(db)

def get_user_data(sess: str) -> dict | None:
    return _load_users_db().get(sess)

def append_registration_local(course: dict, form: dict, sess: str):
    rec = {
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "session_id": sess,
        "course_title": course.get("title", ""),
        "course_url": course.get("url"),
        "user": form,
    }
    with open(REG_DB_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def push(sess, ctx): menu_state[sess]["stack"].append(ctx)
def pop(sess):
    st = menu_state[sess]["stack"]
    if st: st.pop()
def peek(sess):
    st = menu_state[sess]["stack"]
    return st[-1] if st else None

def root_screen():
    Q = get_Q()
    hello = Q.get("Hello") or "Вітаємо! Що б ви хотіли дізнатися?"
    options = Q.get("MainMenu") or []
    if not options:
        options = ["Про Star for Life", "❓Поширені питання", "Соціальні мережі", "Курси"]
    return {"message": hello, "options": options}

def screen_for_context(sess, ctx):
    Q = get_Q()
    t = ctx["type"]
    if t == "faq_root":
        return {"message": "Від кого питання?", "options": ["Від дитини", "Від дорослого", "На головну"], "forwarded": False}
    if t == "faq_child":
        questions = [x.get("question") for x in (Q.get("FAQs", {}).get("child") or []) if x.get("question")]
        return {"message": "Оберіть запитання:", "options": questions + ["Назад", "На головну"], "forwarded": False}
    if t == "faq_adult":
        questions = [x.get("question") for x in (Q.get("FAQs", {}).get("adult") or []) if x.get("question")]
        return {"message": "Оберіть запитання:", "options": questions + ["Назад", "На головну"], "forwarded": False}
    if t == "social":
        socials = list((Q.get("Social") or {}).keys())
        return {"message": "Наші соцмережі:", "options": socials + ["Назад", "На головну"], "forwarded": False}
    if t == "courses":
        act = Q.get("ActiveCourse", {}) or {}
        hello = act.get("Hello") or "Актуальні курси:"
        titles = [c.get("title") for c in (act.get("Course") or []) if c.get("title")]
        return {"message": hello, "options": titles + ["Назад", "На головну"], "forwarded": False}
    if t == "course_one":
        c = ctx["course"]
        msg = f"{c.get('title','')}\n\n{c.get('description','')}"
        url = c.get("url")
        if url: msg += f"\n\nПосилання: {url}"
        return {"message": msg, "options": ["Зареєструватися", "Назад", "На головну"], "forwarded": False}
    return {**root_screen(), "forwarded": False}

async def handle_userdata(sess, st, user_text: str):
    step = st["ctx"].get("step", 1)
    form = st["ctx"].setdefault("form", {})
    if step == 1:
        if not user_text or len(user_text) < 3:
            return {"message": "Будь ласка, введіть коректні ПІБ:", "options": ["На головну"], "forwarded": False}
        form["Name"] = user_text.strip()
        st["ctx"]["step"] = 2
        return {"message": "Вкажіть ваш вік (число):", "options": ["На головну"], "forwarded": False}
    if step == 2:
        if not valid_age(user_text):
            return {"message": "Вік має бути числом від 5 до 99. Спробуйте ще раз:", "options": ["На головну"], "forwarded": False}
        form["Age"] = int(user_text)
        st["ctx"]["step"] = 3
        return {"message": "Вкажіть ваш E-mail:", "options": ["На головну"], "forwarded": False}
    if step == 3:
        if not valid_email(user_text):
            return {"message": "Схоже, E-mail некоректний. Спробуйте ще раз:", "options": ["На головну"], "forwarded": False}
        form["E-mail"] = user_text.strip()
        st["ctx"]["step"] = 4
        return {"message": "Вкажіть ваш номер телефону у форматі +380XXXXXXXXX:", "options": ["На головну"], "forwarded": False}
    if step == 4:
        if not valid_phone_ua(user_text):
            return {"message": "Телефон має бути у форматі +380XXXXXXXXX. Спробуйте ще раз:", "options": ["На головну"], "forwarded": False}
        form["namberphone"] = user_text.strip()
        st["ctx"]["step"] = 5
        return {"message": "Вкажіть вашу область/регіон:", "options": ["На головну"], "forwarded": False}
    if step == 5:
        form["regions"] = user_text.strip()
        st["ctx"]["step"] = 6
        return {"message": "Вкажіть ваш навчальний заклад (школа/ліцей):", "options": ["На головну"], "forwarded": False}
    if step == 6:
        form["school"] = user_text.strip()
        st["ctx"]["step"] = 7
        return {"message": "Оберіть вашу стать:", "options": GENDER_OPTS + ["На головну"], "forwarded": False}
    if step == 7:
        if user_text not in GENDER_OPTS:
            return {"message": "Будь ласка, оберіть один із варіантів:", "options": GENDER_OPTS + ["На головну"], "forwarded": False}
        form["gender"] = user_text
        st["ctx"]["step"] = 8
        return {"message": "Чи маєте пільги?", "options": BENEFIT_OPTS + ["На головну"], "forwarded": False}
    if step == 8:
        if user_text not in BENEFIT_OPTS:
            return {"message": "Оберіть варіант:", "options": BENEFIT_OPTS + ["На головну"], "forwarded": False}
        if user_text == "Інше":
            st["ctx"]["step"] = 8.5
            return {"message": "Опишіть, будь ласка, ваші пільги:", "options": ["На головну"], "forwarded": False}
        form["benefit"] = user_text
        st["ctx"]["step"] = 9
        return {"message": "Звідки ви дізналися про нас?", "options": SOURCE_OPTS + ["На головну"], "forwarded": False}
    if step == 8.5:
        form["benefit"] = user_text.strip()
        st["ctx"]["step"] = 9
        return {"message": "Звідки ви дізналися про нас?", "options": SOURCE_OPTS + ["На головну"], "forwarded": False}
    if step == 9:
        if user_text not in SOURCE_OPTS:
            form["info_source"] = user_text.strip()
        else:
            form["info_source"] = user_text
        st["ctx"]["step"] = 10
        return {"message": "Чи даєте ви згоду на обробку персональних даних?", "options": CONSENT_OPTS + ["На головну"], "forwarded": False}
    if step == 10:
        if user_text not in CONSENT_OPTS:
            return {"message": "Будь ласка, оберіть варіант:", "options": CONSENT_OPTS + ["На головну"], "forwarded": False}
        if user_text == "Ні":
            menu_state[sess] = {"stack": [], "mode": None, "ctx": {}}
            return {"message": "Без згоди ми не можемо зберегти анкету.", "options": ["На головну"], "forwarded": False}
        form["consent"] = True
        store_user_data(sess, form)
        try:
            msg = (
                f"🗂 Нова анкета з сайту\n"
                f"🆔 session_id: {sess}\n"
                f"👤 ПІБ: {form.get('Name','')}\n"
                f"🔹 Вік: {form.get('Age','')}\n"
                f"✉️ Email: {form.get('E-mail','')}\n"
                f"📱 Телефон: {form.get('namberphone','')}\n"
                f"🌍 Область: {form.get('regions','')}\n"
                f"🏫 Школа: {form.get('school','')}\n"
                f"⚧ Стать: {form.get('gender','')}\n"
                f"🧩 Пільги: {form.get('benefit','')}\n"
                f"🔎 Джерело: {form.get('info_source','')}"
            )
            if ADMIN_CHAT_ID:
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)
        except Exception:
            pass
        menu_state[sess] = {"stack": [], "mode": None, "ctx": {}}
        return {"message": "Дякуємо! Ваші дані збережено. Тепер можете обрати курс і зареєструватися.", "options": ["На головну"], "forwarded": False}
    return {"message": "Продовжимо заповнення анкети?", "options": ["На головну"], "forwarded": False}

async def engine_next(sess: str, user_text: str | None):
    Q = get_Q()
    st = menu_state[sess]
    if (user_text or "").strip() in ("На головну", "До головного меню"):
        menu_state[sess] = {"stack": [], "mode": None, "ctx": {}}
        return {**root_screen(), "forwarded": False}
    if (user_text or "").strip() == "Назад":
        pop(sess)
        ctx = peek(sess)
        if not ctx:
            menu_state[sess]["mode"] = None
            menu_state[sess]["ctx"] = {}
            return {**root_screen(), "forwarded": False}
        return screen_for_context(sess, ctx)
    if st["mode"] == "ask":
        if user_text:
            return {"message": "Дякуємо! Ваше питання надіслано адміністратору.", "options": ["На головну"], "forwarded": True}
        return {"message": "Напишіть ваше питання:", "options": ["На головну"], "forwarded": False}
    if st["mode"] == "feedback":
        if user_text:
            return {"message": "Дякуємо за зворотній зв'язок!", "options": ["На головну"], "forwarded": True}
        return {"message": "Напишіть ваш зворотній зв'язок:", "options": ["На головну"], "forwarded": False}
    if st["mode"] == "reviews":
        if user_text:
            return {"message": "Дякуємо за відгук!", "options": ["На головну"], "forwarded": True}
        return {"message": "Напишіть ваш відгук:", "options": ["На головну"], "forwarded": False}
    if st["mode"] == "userdata":
        return await handle_userdata(sess, st, user_text or "")
    if not user_text:
        return {**root_screen(), "forwarded": False}
    if not peek(sess):
        low = (user_text or "").lower()

        if any(k in low for k in ("faq", "пошир", "част", "питан")):
            push(sess, {"type": "faq_root"})
            return screen_for_context(sess, peek(sess))

        elif any(k in low for k in ("star for life", "про star")):
            txt = (Q.get("SchoolInfo", {}) or {}).get("text") or "Про школу"
            url = (Q.get("SchoolInfo", {}) or {}).get("url")
            if url:
                txt += f"\n\nПосилання: {url}"
            return {"message": txt, "options": ["На головну"], "forwarded": False}

        elif any(k in low for k in ("соц", "мереж")):
            push(sess, {"type": "social"})
            return screen_for_context(sess, peek(sess))

        elif "курс" in low:
            push(sess, {"type": "courses"})
            return screen_for_context(sess, peek(sess))

        elif any(k in low for k in ("дан", "анкета")):
            st["mode"] = "userdata"
            st["ctx"] = {"step": 1, "form": {}}
            return {"message": "Введіть ваші ПІБ (прізвище, імʼя, по батькові):", "options": ["На головну"], "forwarded": False}

        elif any(k in low for k in ("задати", "питання")):
            st["mode"] = "ask"
            return {"message": "Напишіть ваше питання:", "options": ["На головну"], "forwarded": False}

        elif "зворот" in low:
            st["mode"] = "feedback"
            return {"message": "Напишіть ваш зворотній зв'язок:", "options": ["На головну"], "forwarded": False}

        elif "відгук" in low:
            st["mode"] = "reviews"
            return {"message": "Напишіть ваш відгук:", "options": ["На головну"], "forwarded": False}

        return {"message": "Дякуємо! Ваше повідомлення передано оператору.", "options": ["На головну"], "forwarded": True}

    ctx = peek(sess)
    if ctx["type"] == "faq_root":
        if user_text == "Від дитини":
            push(sess, {"type": "faq_child"});  return screen_for_context(sess, peek(sess))
        if user_text == "Від дорослого":
            push(sess, {"type": "faq_adult"});  return screen_for_context(sess, peek(sess))
        return screen_for_context(sess, ctx)
    if ctx["type"] == "faq_child":
        pair = next((x for x in (Q.get("FAQs", {}).get("child") or []) if x.get("question") == user_text), None)
        if pair:
            return {"message": f"❓ {pair.get('question')}\n\n💬 {pair.get('answer','')}", "options": ["Назад", "На головну"], "forwarded": False}
        return screen_for_context(sess, ctx)
    if ctx["type"] == "faq_adult":
        pair = next((x for x in (Q.get("FAQs", {}).get("adult") or []) if x.get("question") == user_text), None)
        if pair:
            return {"message": f"❓ {pair.get('question')}\n\n💬 {pair.get('answer','')}", "options": ["Назад", "На головну"], "forwarded": False}
        return screen_for_context(sess, ctx)
    if ctx["type"] == "social":
        url = (Q.get("Social") or {}).get(user_text)
        if url:
            return {"message": f"{user_text}: {url}", "options": ["Назад", "На головну"], "forwarded": False}
        return screen_for_context(sess, ctx)
    if ctx["type"] == "courses":
        act = Q.get("ActiveCourse", {}) or {}
        course = next((c for c in (act.get("Course") or []) if c.get("title") == user_text), None)
        if course:
            push(sess, {"type": "course_one", "course": course})
            return screen_for_context(sess, peek(sess))
        return screen_for_context(sess, ctx)
    if ctx["type"] == "course_one":
        c = ctx["course"]
        if user_text == "Зареєструватися":
            form = get_user_data(sess)
            if not form or not form.get("consent"):
                st["mode"] = "userdata"
                st["ctx"] = {"step": 1, "form": {}}
                return {"message": "Спочатку, будь ласка, заповніть анкету. Введіть ваші ПІБ:", "options": ["На головну"], "forwarded": False}
            append_registration_local(c, form, sess)
            try:
                msg = (
                    f"✅ Заявка на курс: {c.get('title','')}\n"
                    f"🆔 session_id: {sess}\n"
                    f"👤 {form.get('Name','')} ({form.get('Age','')} років)\n"
                    f"✉️ {form.get('E-mail','')} | 📱 {form.get('namberphone','')}\n"
                    f"🌍 {form.get('regions','')} | 🏫 {form.get('school','')}\n"
                    f"⚧ {form.get('gender','')} | 🧩 {form.get('benefit','')}\n"
                    f"🔎 {form.get('info_source','')}\n"
                    f"🔗 {c.get('url','') or ''}"
                )
                if ADMIN_CHAT_ID:
                    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)
            except Exception:
                pass
            return {"message": "✅ Заявку на курс надіслано! Ми з вами звʼяжемося найближчим часом.", "options": ["На головну"], "forwarded": False}
        return screen_for_context(sess, ctx)
    return {"message": "Дякуємо! Ваше повідомлення передано оператору.", "options": ["На головну"], "forwarded": True}

@app.post("/api/next")
async def api_next(req: Request):
    data = await req.json()
    sess = data["session_id"]
    text = (data.get("text") or "").strip()
    result = await engine_next(sess, text if text else None)
    if result.get("forwarded") and text:
        chat_store[sess].append({"from_bot": False, "text": text})
        try:
            if ADMIN_CHAT_ID:
                await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"[{sess}] Повідомлення від користувача:\n{text}")
        except Exception:
            pass
    return {"message": result.get("message", ""), "options": result.get("options", [])}

@app.post("/api/send")
async def api_send(req: Request):
    data = await req.json()
    sess = data["session_id"]
    text = data["text"]
    chat_store[sess].append({"from_bot": False, "text": text})
    try:
        if ADMIN_CHAT_ID:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"[{sess}] Повідомлення від користувача:\n{text}")
    except Exception:
        pass
    return {"ok": True}

@app.post("/telegram_webhook")
async def tg_webhook(req: Request):
    data = await req.json()
    msg = data.get("message", {}) or {}
    chat = msg.get("chat", {}) or {}
    text = (msg.get("text") or "").strip()
    if chat.get("id") == ADMIN_CHAT_ID:
        parts = text.split(maxsplit=2)
        if parts and parts[0] == "/reply" and len(parts) == 3:
            _, session_id, answer = parts
            chat_store[session_id].append({"from_bot": True, "text": answer})
    return {"ok": True}

@app.websocket("/ws/{session_id}")
async def ws_endpoint(ws: WebSocket, session_id: str):
    await ws.accept()
    last = 0
    try:
        while True:
            await asyncio.sleep(0.5)
            msgs = chat_store[session_id][last:]
            for m in msgs:
                if m["from_bot"]:
                    await ws.send_text(m["text"])
            last += len(msgs)
    except Exception:
        pass

@app.get("/api/bootstrap")
async def bootstrap():
    base = root_screen()
    return {"greeting": base["message"], "options": base["options"]}

@app.get("/test")
async def test_page():
    return FileResponse(Path("test.html"))
