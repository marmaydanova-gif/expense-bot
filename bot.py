import telebot

TOKEN = "8739810929:AAEDlAh79km06uSRCLX2I0W4fkQRt3aoH5A"
bot = telebot.TeleBot(TOKEN)

projects = []

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📁 Проекты", "➕ Новый проект")
    markup.row("💸 Добавить расход", "📊 Итоги")
    markup.row("❌ Удалить проект")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🔥 Бот запущен", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📁 Проекты")
def show_projects(message):
    if not projects:
        bot.send_message(message.chat.id, "📁 Проектов пока нет")
    else:
        txt = "📁 Проекты:\n\n" + "\n".join("• " + p for p in projects)
        bot.send_message(message.chat.id, txt)

@bot.message_handler(func=lambda m: m.text == "➕ Новый проект")
def add_project_start(message):
    msg = bot.send_message(message.chat.id, "✍️ Напиши название проекта:")
    bot.register_next_step_handler(msg, save_project)

def save_project(message):
    name = message.text.strip()
    projects.append(name)
    bot.send_message(message.chat.id, f"✅ Проект добавлен: {name}", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📊 Итоги")
def totals(message):
    bot.send_message(message.chat.id, "📊 Пока расходов нет")

@bot.message_handler(func=lambda m: m.text == "💸 Добавить расход")
def expense(message):
    bot.send_message(message.chat.id, "💸 Расходы подключим следующим шагом")

@bot.message_handler(func=lambda m: m.text == "❌ Удалить проект")
def delete_project(message):
    bot.send_message(message.chat.id, "❌ Удаление подключим следующим шагом")

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "Жми кнопки 👇", reply_markup=main_menu())

bot.infinity_polling()
