import logging
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import asyncio
from datetime import datetime, time

# Константы состояний для редактирования сообщений
EDIT_NIGHT_MESSAGE, EDIT_MORNING_MESSAGE, EDIT_NIGHT_TIME, EDIT_MORNING_TIME = range(4)

# Сообщения по умолчанию
night_message = "Включен ночной режим в чате до {time} часов."
morning_message = "Доброе утро! Ночной режим отключен. Теперь вы можете писать в чат!"

# Времена по умолчанию
night_time = time(22, 0)
morning_time = time(8, 0)

# Флаг для контроля отправки сообщений
night_mode = False

# ID чата, в котором бот будет работать (замените на актуальный chat_id)
chat_id = None

def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id
    chat_id = update.effective_chat.id
    keyboard = [
        ["Приветственное сообщение"],
        ["Сообщение закрытия чата"],
        ["Время закрытия чата"],
        ["Время открытия чата"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(
        "Привет! Я бот для управления ночным режимом. Выберите настройку:", reply_markup=reply_markup
    )

def edit_night_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Введите новое сообщение для ночного режима:")
    return EDIT_NIGHT_MESSAGE

def save_night_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global night_message
    night_message = update.message.text
    update.message.reply_text(f"Сообщение ночного режима обновлено: {night_message}")
    return ConversationHandler.END

def edit_morning_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Введите новое сообщение для утреннего режима:")
    return EDIT_MORNING_MESSAGE

def save_morning_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global morning_message
    morning_message = update.message.text
    update.message.reply_text(f"Сообщение утреннего режима обновлено: {morning_message}")
    return ConversationHandler.END

def edit_night_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Введите новое время закрытия чата в формате HH:MM:")
    return EDIT_NIGHT_TIME

def save_night_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global night_time
    try:
        night_time = datetime.strptime(update.message.text, "%H:%M").time()
        update.message.reply_text(f"Время закрытия чата обновлено: {night_time}")
    except ValueError:
        update.message.reply_text("Неверный формат времени. Попробуйте снова.")
        return EDIT_NIGHT_TIME
    return ConversationHandler.END

def edit_morning_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Введите новое время открытия чата в формате HH:MM:")
    return EDIT_MORNING_TIME

def save_morning_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global morning_time
    try:
        morning_time = datetime.strptime(update.message.text, "%H:%M").time()
        update.message.reply_text(f"Время открытия чата обновлено: {morning_time}")
    except ValueError:
        update.message.reply_text("Неверный формат времени. Попробуйте снова.")
        return EDIT_MORNING_TIME
    return ConversationHandler.END

async def enable_night_mode(application):
    global night_mode
    if chat_id:
        night_mode = True
        await application.bot.send_message(chat_id, night_message.format(time=morning_time.strftime("%H:%M")))

async def disable_night_mode(application):
    global night_mode
    if chat_id:
        night_mode = False
        await application.bot.send_message(chat_id, morning_message)

async def schedule_tasks(application):
    while True:
        now = datetime.now().time()
        if now >= night_time and not night_mode:  # Включение ночного режима
            await enable_night_mode(application)
        elif now >= morning_time and night_mode:  # Отключение ночного режима
            await disable_night_mode(application)
        await asyncio.sleep(60)  # Проверка каждые 60 секунд

def main():
    try:
        application = Application.builder().token(
        os.environ.get("TOKEN")
    ).build()

        # Обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(ConversationHandler(
            entry_points=[CommandHandler("set_night_mode", start)],
            states={
                EDIT_NIGHT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_night_message)],
                EDIT_MORNING_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_morning_message)],
                EDIT_NIGHT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_night_time)],
                EDIT_MORNING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_morning_time)],
            },
            fallbacks=[]
        ))

        # Запуск фоновой задачи
        application.job_queue.run_once(lambda _: asyncio.create_task(schedule_tasks(application)), when=0)

        # Запуск бота
        application.run_polling()
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
