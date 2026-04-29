import telebot
import sqlite3

TOKEN = "8739810929:AAEDlAh79km06uSRCLX2I0W4fkQRt3aoH5A"
bot = telebot.TeleBot(TOKEN)

# ======================
# DATABASE
# ======================
conn = sqlite3.connect("base.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS projects(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT
)
""")
conn.commit()

# ======================
# MENU
# ======================
def menu():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📁 Проекты", "➕ Новый проект")
    kb.row("❌ Удалить проект")
    return kb

# ======================
# START
# ======================
@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "🔥 PRO бот активен", reply_markup=menu())

# ======================
# SHOW PROJECTS
# ======================
@bot.message_handler(func=lambda m: m.text == "📁 Проекты")
def show_projects(msg):
    cur.execute("SELECT name FROM projects")
    rows = cur.fetchall()

    if not rows:
        bot.send_message(msg.chat.id, "📁 Проектов нет")
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
    x = bot.send_message(msg.chat.id, "✍️ Напиши название проекта:")
    bot.register_next_step_handler(x, save_project)

def save_project(msg):
    name = msg.text.strip()
    cur.execute("INSERT INTO projects(name) VALUES(?)", (name,))
    conn.commit()

    bot.send_message(msg.chat.id, f"✅ Проект добавлен:\n{name}", reply_markup=menu())

# ======================
# DELETE PROJECT
# ======================
@bot.message_handler(func=lambda m: m.text == "❌ Удалить проект")
def del_project(msg):
    cur.execute("SELECT id,name FROM projects")
    rows = cur.fetchall()

    if not rows:
        bot.send_message(msg.chat.id, "Удалять нечего")
        return

    kb = telebot.types.InlineKeyboardMarkup()

    for r in rows:
        kb.add(
            telebot.types.InlineKeyboardButton(
                text="❌ " + r[1],
                callback_data=f"del_{r[0]}"
            )
        )

    bot.send_message(msg.chat.id, "Выбери проект:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_"))
def delete_btn(call):
    pid = call.data.split("_")[1]

    cur.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()

    bot.edit_message_text(
        "✅ Проект удалён",
        call.message.chat.id,
        call.message.message_id
    )

# ======================
# OTHER
# ======================
@bot.message_handler(func=lambda m: True)
def other(msg):
    bot.send_message(msg.chat.id, "Жми кнопки 👇", reply_markup=menu())

bot.infinity_polling()
