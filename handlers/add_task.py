from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import TITLE, PRIORITY
from database import add_task


async def add_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Name your task, please!")
    return TITLE


async def add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    keyboard = [[
        InlineKeyboardButton("🟢 Низкий", callback_data="priority_low"),
        InlineKeyboardButton("🟡 Средний", callback_data="priority_medium"),
        InlineKeyboardButton("🔴 Высокий", callback_data="priority_high"),
    ]]
    await update.message.reply_text("Выбери приоритет:", reply_markup=InlineKeyboardMarkup(keyboard))
    return PRIORITY


async def get_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    priority_map = {"priority_low": "Lower", "priority_medium": "Medium", "priority_high": "High"}
    priority = priority_map[query.data]
    title = context.user_data['title']
    user_id = update.effective_user.id
    time_inserted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    add_task(user_id, title, priority, time_inserted)

    await query.edit_message_text(f"✅ Задача добавлена!\nНазвание: {title}\nПриоритет: {priority}")
    return ConversationHandler.END