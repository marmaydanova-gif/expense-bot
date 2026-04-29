import telebot
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

TOKEN = "8739810929:AAEDlAh79km06uSRCLX2I0W4fkQRt3aoH5A"
bot = telebot.TeleBot(TOKEN)

projects = []

def menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📁 Проекты", "➕ Новый проект")
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "🔥 Бот работает", reply_markup=menu())

@bot.message_handler(func=lambda m: m.text == "📁 Проекты")
def pr(message):
    if not projects:
        bot.send_message(message.chat.id, "Проектов нет")
    else:
        bot.send_message(message.chat.id, "\n".join(projects))

@bot.message_handler(func=lambda m: m.text == "➕ Новый проект")
def np(message):
    msg = bot.send_message(message.chat.id, "Напиши название:")
    bot.register_next_step_handler(msg, save)

def save(message):
    projects.append(message.text)
    bot.send_message(message.chat.id, "✅ Добавлено", reply_markup=menu())

def run_bot():
    bot.infinity_polling()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

threading.Thread(target=run_bot).start()

port = int(os.environ.get("PORT", 10000))
server = HTTPServer(("0.0.0.0", port), Handler)
server.serve_forever()
