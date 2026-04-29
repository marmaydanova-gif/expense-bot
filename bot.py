import telebot
import sqlite3
from datetime import datetime

TOKEN = "8739810929:AAEDlAh79km06uSRCLX2I0W4fkQRt3aoH5A"
bot = telebot.TeleBot(TOKEN)

# ======================
# DB
# ======================
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
created_at TEXT
)
""")

conn.commit()

# ======================
# MENU
# ======================
def menu():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📁 Проекты", "➕ Новый проект")
    kb.row("💸 Добавить расход", "📊 Итоги")
    kb.row("🗑 Удалить расход", "❌ Удалить проект")
    return kb

# ======================
# START
# ======================
@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "🔥 BOT ACTIVE", reply_markup=menu())

# ======================
# PROJECTS
# ======================
@bot.message_handler(func=lambda m: m.text == "📁 Проекты")
def projects(msg):
    cur.execute("SELECT name FROM projects")
    rows = cur.fetchall()

    if not rows:
        bot.send_message(msg.chat.id, "Проектов нет")
        return

    text = "📁 Проекты:\n\n"
    for r in rows:
        text += f"• {r[0]}\n"

    bot.send_message(msg.chat.id, text)

# ======================
# NEW PROJECT
# ======================
@bot.message_handler(func=lambda m: m.text == "➕ Новый проект")
def new_project(msg):
    x = bot.send_message(msg.chat.id, "Название проекта:")
    bot.register_next_step_handler(x, save_project)

def save_project(msg):
    cur.execute("INSERT INTO projects(name) VALUES(?)", (msg.text,))
    conn.commit()
    bot.send_message(msg.chat.id, "✅ Проект добавлен", reply_markup=menu())

# ======================
# DELETE PROJECT
# ======================
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

# ======================
# ADD EXPENSE
# ======================
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

# ======================
# CALLBACKS
# ======================
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):

    if call.data.startswith("del_"):
        pid = call.data.split("_")[1]

        cur.execute("DELETE FROM projects WHERE id=?", (pid,))
        conn.commit()

        bot.edit_message_text(
            "✅ Проект удалён",
            call.message.chat.id,
            call.message.message_id
        )
        return

    if call.data.startswith("exp_"):
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
        return

    if call.data.startswith("man_"):
        arr = call.data.split("_")
        person = arr[1]
        project = arr[2]

        x = bot.send_message(call.message.chat.id, "Введите сумму:")
        bot.register_next_step_handler(x, enter_comment, project, person)
        return

# ======================
# STEPS
# ======================
def enter_comment(msg, project, person):
    try:
        s = float(msg.text.replace(",", "."))
    except:
        bot.send_message(msg.chat.id, "Неверная сумма")
        return

    x = bot.send_message(msg.chat.id, "Комментарий:")
    bot.register_next_step_handler(x, save_expense, project, person, s)

def save_expense(msg, project, person, s):
    comment = msg.text
    dt = datetime.now().strftime("%d.%m.%Y %H:%M")

    cur.execute("""
        INSERT INTO expenses(project,person,sum,comment,created_at)
        VALUES(?,?,?,?,?)
    """, (project, person, s, comment, dt))

    conn.commit()

    bot.send_message(
        msg.chat.id,
        f"✅ Расход сохранён\n\n📅 {dt}\n📁 {project}\n👤 {person}\n💰 {s} ₽\n📝 {comment}",
        reply_markup=menu()
    )

# ======================
# DELETE LAST EXPENSE
# ======================
@bot.message_handler(func=lambda m: m.text == "🗑 Удалить расход")
def delete_last(msg):
    cur.execute("SELECT id FROM expenses ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()

    if not row:
        bot.send_message(msg.chat.id, "Расходов нет")
        return

    cur.execute("DELETE FROM expenses WHERE id=?", (row[0],))
    conn.commit()

    bot.send_message(msg.chat.id, "🗑 Последний расход удалён")

# ======================
# TOTALS
# ======================
@bot.message_handler(func=lambda m: m.text == "📊 Итоги")
def totals(msg):
    cur.execute("""
        SELECT project,person,SUM(sum)
        FROM expenses
        GROUP BY project,person
    """)

    rows = cur.fetchall()

    if not rows:
        bot.send_message(msg.chat.id, "Расходов нет")
        return

    data = {}

    for r in rows:
        project = r[0]
        person = r[1]
        amount = r[2]

        if project not in data:
            data[project] = {}

        data[project][person] = amount

    text = "📊 Итоги по проектам:\n\n"

    for project in data:
        text += f"📁 {project}\n"
        total = 0

        for person in data[project]:
            amount = data[project][person]
            total += amount
            text += f"   {person}: {amount} ₽\n"

        text += f"   💰 Всего: {total} ₽\n\n"

    bot.send_message(msg.chat.id, text)

# ======================
# OTHER
# ======================
@bot.message_handler(func=lambda m: True)
def other(msg):
    bot.send_message(msg.chat.id, "Жми кнопки 👇", reply_markup=menu())

bot.infinity_polling()
