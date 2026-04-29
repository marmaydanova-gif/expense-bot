import telebot
import sqlite3

TOKEN = "8739810929:AAEDlAh79km06uSRCLX2I0W4fkQRt3aoH5A"
bot = telebot.TeleBot(TOKEN)

# =====================
# DB
# =====================
conn = sqlite3.connect("base.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS projects(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS expenses(
id INTEGER PRIMARY KEY AUTOINCREMENT,
project TEXT,
person TEXT,
sum REAL,
comment TEXT,
photo TEXT
)
""")

conn.commit()

# =====================
# MENU
# =====================
def menu():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📁 Проекты", "➕ Новый проект")
    kb.row("💸 Добавить расход", "📊 Итоги")
    kb.row("❌ Удалить проект")
    return kb

# =====================
# START
# =====================
@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "🔥 BOT MAX активен", reply_markup=menu())

# =====================
# PROJECTS
# =====================
@bot.message_handler(func=lambda m: m.text == "📁 Проекты")
def show_projects(msg):
    cur.execute("SELECT name FROM projects")
    rows = cur.fetchall()

    if not rows:
        bot.send_message(msg.chat.id, "Проектов нет")
        return

    text = "📁 Проекты:\n\n"
    for r in rows:
        text += f"• {r[0]}\n"

    bot.send_message(msg.chat.id, text)

# =====================
# NEW PROJECT
# =====================
@bot.message_handler(func=lambda m: m.text == "➕ Новый проект")
def new_project(msg):
    x = bot.send_message(msg.chat.id, "Название проекта:")
    bot.register_next_step_handler(x, save_project)

def save_project(msg):
    cur.execute("INSERT INTO projects(name) VALUES(?)", (msg.text,))
    conn.commit()
    bot.send_message(msg.chat.id, "✅ Проект добавлен", reply_markup=menu())

# =====================
# DELETE PROJECT
# =====================
@bot.message_handler(func=lambda m: m.text == "❌ Удалить проект")
def del_project(msg):
    cur.execute("SELECT id,name FROM projects")
    rows = cur.fetchall()

    kb = telebot.types.InlineKeyboardMarkup()

    for r in rows:
        kb.add(
            telebot.types.InlineKeyboardButton(
                text="❌ " + r[1],
                callback_data="del_" + str(r[0])
            )
        )

    bot.send_message(msg.chat.id, "Выбери проект:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_"))
def delete_project(call):
    pid = call.data.split("_")[1]

    cur.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()

    bot.edit_message_text(
        "✅ Проект удалён",
        call.message.chat.id,
        call.message.message_id
    )

# =====================
# ADD EXPENSE
# =====================
@bot.message_handler(func=lambda m: m.text == "💸 Добавить расход")
def add_expense(msg):
    cur.execute("SELECT name FROM projects")
    rows = cur.fetchall()

    if not rows:
        bot.send_message(msg.chat.id, "Сначала создай проект")
        return

    kb = telebot.types.InlineKeyboardMarkup()

    for r in rows:
        kb.add(
            telebot.types.InlineKeyboardButton(
                text=r[0],
                callback_data="exp_" + r[0]
            )
        )

    bot.send_message(msg.chat.id, "Выбери проект:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("exp_"))
def choose_person(call):
    project = call.data.replace("exp_", "")

    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(
        telebot.types.InlineKeyboardButton("👨 Влад", callback_data="man_Vlad_" + project),
        telebot.types.InlineKeyboardButton("👨 Никита", callback_data="man_Nikita_" + project)
    )

    bot.edit_message_text(
        "Кто платил?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("man_"))
def enter_sum(call):
    arr = call.data.split("_")
    person = arr[1]
    project = arr[2]

    msg = bot.send_message(call.message.chat.id, "Введите сумму:")
    bot.register_next_step_handler(msg, enter_comment, project, person)

def enter_comment(msg, project, person):
    try:
        s = float(msg.text.replace(",", "."))
    except:
        bot.send_message(msg.chat.id, "Неверная сумма")
        return

    x = bot.send_message(msg.chat.id, "Комментарий:")
    bot.register_next_step_handler(x, ask_photo, project, person, s)

def ask_photo(msg, project, person, s):
    comment = msg.text

    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row("⏭ Пропустить")

    x = bot.send_message(
        msg.chat.id,
        "📸 Пришли фото чека или нажми Пропустить",
        reply_markup=kb
    )

    bot.register_next_step_handler(x, save_expense, project, person, s, comment)

def save_expense(msg, project, person, s, comment):
    photo_id = ""

    if msg.content_type == "photo":
        photo_id = msg.photo[-1].file_id

    if msg.text == "⏭ Пропустить":
        photo_id = ""

    cur.execute("""
        INSERT INTO expenses(project,person,sum,comment,photo)
        VALUES(?,?,?,?,?)
    """, (project, person, s, comment, photo_id))

    conn.commit()

    bot.send_message(
        msg.chat.id,
        f"✅ Расход сохранён\n\n📁 {project}\n👤 {person}\n💰 {s} ₽\n📝 {comment}",
        reply_markup=menu()
    )

# =====================
# TOTALS
# =====================
@bot.message_handler(func=lambda m: m.text == "📊 Итоги")
def totals(msg):
    cur.execute("SELECT person,SUM(sum) FROM expenses GROUP BY person")
    rows = cur.fetchall()

    if not rows:
        bot.send_message(msg.chat.id, "Расходов нет")
        return

    text = "📊 Итоги:\n\n"
    total = 0

    for r in rows:
        text += f"{r[0]}: {r[1]} ₽\n"
        total += r[1]

    text += f"\n💰 Общий расход: {total} ₽"

    bot.send_message(msg.chat.id, text)

# =====================
# OTHER
# =====================
@bot.message_handler(content_types=['photo'])
def photos(msg):
    bot.send_message(msg.chat.id, "Используй кнопку 💸 Добавить расход")

@bot.message_handler(func=lambda m: True)
def other(msg):
    bot.send_message(msg.chat.id, "Жми кнопки 👇", reply_markup=menu())

bot.infinity_polling()
