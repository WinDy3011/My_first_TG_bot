from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
from config import TASKS_MENU, FILTER_STATUS, FILTER_TIME, EDIT_TITLE
from database import (
    get_tasks_page,
    get_tasks_count,
    complete_task,
    delete_task,       # <-- ДОБАВИТЬ
    update_task_title
)


TASKS_PER_PAGE = 10


def format_tasks(tasks):
    message = ""

    for task in tasks:
        status = "✅ Выполнено" if task[6] else "🟢 Активна"

        message += (
            f"\n{status}\n"
            f"Название: {task[2]}\n"
            f"Приоритет: {task[3]}\n"
            f"Создана: {task[4]}\n"
            f"Дедлайн: {task[5]}\n"
        )

        if task[6]:
            message += f"Выполнено: {task[6]}\n"

        message += "\n"

    return message


def build_tasks_message(tasks, page, total_tasks):
    if total_tasks == 0:
        return "По этому фильтру задач не найдено."

    start_number = page * TASKS_PER_PAGE + 1
    end_number = min(
        start_number + len(tasks) - 1,
        total_tasks
    )

    message = (
        f"📋 Задачи {start_number}–{end_number} "
        f"из {total_tasks}\n"
    )

    message += format_tasks(tasks)

    return message


def create_tasks_keyboard(tasks, page, total_pages, prefix):
    keyboard = []

    for task in tasks:
        task_id = task[0]
        title = task[2]
        status = "✅" if task[6] else "🟢"

        keyboard.append([
            InlineKeyboardButton(
                f"{status} {title}",
                callback_data=f"task_{task_id}"
            )
        ])

    pagination_buttons = []

    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"{prefix}_page_{page - 1}"
            )
        )

    if page < total_pages - 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"{prefix}_page_{page + 1}"
            )
        )

    if pagination_buttons:
        keyboard.append(pagination_buttons)

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data="back_to_menu"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# ========== ОБРАБОТЧИК НАЖАТИЯ НА ЗАДАЧУ ==========
async def task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    task_id = int(query.data.replace("task_", ""))
    user_id = update.effective_user.id
    task = get_task_by_id(user_id, task_id)

    if not task:
        await query.edit_message_text("❌ Задача не найдена.")
        return TASKS_MENU

    status = "✅ Выполнено" if task[6] else "🟢 Активна"
    deadline_text = task[5] if task[5] else "Не указан"

    message = (
        f"{status}\n\n"
        f"📌 *{task[2]}*\n\n"
        f"Приоритет: {task[3]}\n"
        f"Создана: {task[4]}\n"
        f"Дедлайн: {deadline_text}\n"
    )
    if task[6]:
        message += f"\nВыполнено: {task[6]}"

    keyboard = [
        [InlineKeyboardButton("✅ Выполнить", callback_data=f"complete_{task_id}")],
        [InlineKeyboardButton("✏️ Изменить", callback_data=f"edit_{task_id}")],
        [InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_{task_id}")],
        [InlineKeyboardButton("⬅️ Назад к списку", callback_data="back_to_tasks")],
    ]

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return TASKS_MENU


# ========== КНОПКА "ВЫПОЛНИТЬ" ==========
async def complete_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🟢🟢 НАЖАТА КНОПКА ВЫПОЛНИТЬ 🟢🟢🟢")
    query = update.callback_query
    await query.answer()

    task_id = int(query.data.replace("complete_", ""))
    user_id = update.effective_user.id
    time_accomplished = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    complete_task(user_id, task_id, time_accomplished)

    keyboard = [[InlineKeyboardButton("⬅️ К списку задач", callback_data="back_to_tasks")]]
    await query.edit_message_text(
        "✅ Задача успешно выполнена!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASKS_MENU


# ========== КНОПКА "УДАЛИТЬ" ==========
async def delete_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🔴🔴🔴 НАЖАТА КНОПКА УДАЛИТЬ 🔴🔴🔴")
    query = update.callback_query
    await query.answer()

    task_id = int(query.data.replace("delete_", ""))
    user_id = update.effective_user.id

    delete_task(user_id, task_id)

    keyboard = [[InlineKeyboardButton("️ К списку задач", callback_data="back_to_tasks")]]
    await query.edit_message_text(
        "🗑 Задача успешно удалена.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASKS_MENU


# ========== КНОПКА "ИЗМЕНИТЬ" ==========
async def edit_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🟡🟡 НАЖАТА КНОПКА ИЗМЕНИТЬ 🟡🟡🟡")
    query = update.callback_query
    await query.answer()

    task_id = int(query.data.replace("edit_", ""))
    context.user_data["editing_task_id"] = task_id

    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_tasks")]]
    await query.edit_message_text(
        "✏️ Введите новое название для этой задачи:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_TITLE


# ========== СОХРАНЕНИЕ НОВОГО НАЗВАНИЯ ==========
async def save_edited_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_title = update.message.text
    task_id = context.user_data.get("editing_task_id")
    user_id = update.effective_user.id

    update_task_title(user_id, task_id, new_title)
    context.user_data.pop("editing_task_id", None)

    keyboard = [[InlineKeyboardButton("⬅️ К списку задач", callback_data="back_to_tasks")]]
    await update.message.reply_text(
        "✅ Название задачи обновлено!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASKS_MENU


# ========== КНОПКА "НАЗАД К СПИСКУ" ==========
async def back_to_tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    page = context.user_data.get("tasks_page", 0)
    status_filter = context.user_data.get("status_filter")
    time_filter = context.user_data.get("time_filter")
    user_id = update.effective_user.id

    total_tasks = get_tasks_count(user_id, status_filter, time_filter)

    if total_tasks == 0:
        keyboard = [[InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_menu")]]
        await query.edit_message_text(
            "Задач не найдено.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return TASKS_MENU

    total_pages = (total_tasks + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE

    if page >= total_pages:
        page = total_pages - 1
        context.user_data["tasks_page"] = page

    tasks = get_tasks_page(user_id, page, status_filter, time_filter, TASKS_PER_PAGE)
    message = build_tasks_message(tasks, page, total_tasks)

    prefix = "filtered" if (status_filter or time_filter) else "all"
    keyboard = create_tasks_keyboard(tasks, page, total_pages, prefix)

    await query.edit_message_text(message, reply_markup=keyboard)
    return TASKS_MENU




async def tasks_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.pop("status_filter", None)
    context.user_data.pop("time_filter", None)
    context.user_data["tasks_page"] = 0

    keyboard = [
        [
            InlineKeyboardButton(
                "📋 Показать все",
                callback_data="show_all"
            )
        ],
        [
            InlineKeyboardButton(
                "🔍 Отфильтровать",
                callback_data="filter"
            )
        ],
    ]

    await update.message.reply_text(
        "Что показать?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return TASKS_MENU


async def cancel_edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("editing_task_id", None)
    keyboard = [[InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_menu")]]
    await query.edit_message_text(
        "✖️ Редактирование отменено.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASKS_MENU

async def tasks_menu_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_menu":
        keyboard = [
            [
                InlineKeyboardButton(
                    "📋 Показать все",
                    callback_data="show_all"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔍 Отфильтровать",
                    callback_data="filter"
                )
            ],
        ]

        await query.edit_message_text(
            "Что показать?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return TASKS_MENU

    if query.data == "show_all":
        user_id = update.effective_user.id
        page = 0

        total_tasks = get_tasks_count(user_id)

        tasks = get_tasks_page(
            user_id=user_id,
            page=page,
            per_page=TASKS_PER_PAGE
        )

        context.user_data["tasks_page"] = page
        context.user_data["status_filter"] = None
        context.user_data["time_filter"] = None

        if total_tasks == 0:
            await query.edit_message_text(
                "У тебя пока нет задач."
            )
            return ConversationHandler.END

        total_pages = (
            total_tasks + TASKS_PER_PAGE - 1
        ) // TASKS_PER_PAGE

        message = build_tasks_message(
            tasks,
            page,
            total_tasks
        )

        keyboard = create_tasks_keyboard(
            tasks,
            page,
            total_pages,
            "all"
        )

        await query.edit_message_text(
            message,
            reply_markup=keyboard
        )

        return TASKS_MENU

    if query.data == "filter":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🟢 Активные",
                    callback_data="status_active"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ Выполненные",
                    callback_data="status_completed"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Назад",
                    callback_data="back_to_menu"
                )
            ],
        ]

        await query.edit_message_text(
            "По какому статусу отфильтровать?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return FILTER_STATUS

    if query.data.startswith("all_page_"):
        page = int(query.data.replace("filtered_page_", ""))
        user_id = update.effective_user.id

        status_filter = context.user_data.get("status_filter")
        time_filter = context.user_data.get("time_filter")

        total_tasks = get_tasks_count(user_id, status_filter, time_filter)

        tasks = get_tasks_page(
            user_id=user_id,
            page=page,
            status_filter=status_filter,
            time_filter=time_filter,
            per_page=TASKS_PER_PAGE
        )

        context.user_data["tasks_page"] = page

        total_pages = (total_tasks + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE

        message = build_tasks_message(tasks, page, total_tasks)

        keyboard = create_tasks_keyboard(tasks, page, total_pages, "filtered")

        await query.edit_message_text(message, reply_markup=keyboard)

        return TASKS_MENU


async def filter_status_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_menu":
        keyboard = [
            [
                InlineKeyboardButton(
                    "📋 Показать все",
                    callback_data="show_all"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔍 Отфильтровать",
                    callback_data="filter"
                )
            ],
        ]

        await query.edit_message_text(
            "Что показать?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return TASKS_MENU

    context.user_data["status_filter"] = query.data

    keyboard = [
        [
            InlineKeyboardButton(
                "📅 Сегодня",
                callback_data="time_today"
            )
        ],
        [
            InlineKeyboardButton(
                "📆 Завтра",
                callback_data="time_tomorrow"
            )
        ],
        [
            InlineKeyboardButton(
                "🗓 3 дня",
                callback_data="time_3days"
            )
        ],
        [
            InlineKeyboardButton(
                "🗓 Неделя",
                callback_data="time_week"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="back_to_status"
            )
        ],
    ]

    await query.edit_message_text(
        "За какой период?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return FILTER_TIME


async def filter_time_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_menu":
        keyboard = [
            [
                InlineKeyboardButton(
                    "📋 Показать все",
                    callback_data="show_all"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔍 Отфильтровать",
                    callback_data="filter"
                )
            ],
        ]

        await query.edit_message_text(
            "Что показать?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return TASKS_MENU

    if query.data == "back_to_status":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🟢 Активные",
                    callback_data="status_active"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ Выполненные",
                    callback_data="status_completed"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Назад",
                    callback_data="back_to_menu"
                )
            ],
        ]

        await query.edit_message_text(
            "По какому статусу отфильтровать?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return FILTER_STATUS

    if query.data.startswith("filtered_page_"):
        page = int(
            query.data.replace(
                "filtered_page_",
                ""
            )
        )

        status_filter = context.user_data.get(
            "status_filter"
        )
        time_filter = context.user_data.get(
            "time_filter"
        )
    else:
        page = 0

        status_filter = context.user_data.get(
            "status_filter"
        )
        time_filter = query.data

        context.user_data["time_filter"] = time_filter

    user_id = update.effective_user.id

    total_tasks = get_tasks_count(
        user_id=user_id,
        status_filter=status_filter,
        time_filter=time_filter
    )

    tasks = get_tasks_page(
        user_id=user_id,
        page=page,
        status_filter=status_filter,
        time_filter=time_filter,
        per_page=TASKS_PER_PAGE
    )

    if total_tasks == 0:
        await query.edit_message_text(
            "По этому фильтру задач не найдено."
        )
        return ConversationHandler.END

    total_pages = (
        total_tasks + TASKS_PER_PAGE - 1
    ) // TASKS_PER_PAGE

    context.user_data["tasks_page"] = page

    message = build_tasks_message(
        tasks,
        page,
        total_tasks
    )

    keyboard = create_tasks_keyboard(
        tasks,
        page,
        total_pages,
        "filtered"
    )

    await query.edit_message_text(
        message,
        reply_markup=keyboard
    )

    return TASKS_MENU


async def back_to_menu_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "📋 Показать все",
                callback_data="show_all"
            )
        ],
        [
            InlineKeyboardButton(
                "🔍 Отфильтровать",
                callback_data="filter"
            )
        ],
    ]

    await query.edit_message_text(
        "Что показать?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return TASKS_MENU


import logging


async def task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ЯРКИЙ ПРИНТ, КОТОРЫЙ МЫ УВИДИМ В КОНСОЛИ
    print("🔴🔴🔴 ЗАШЕЛ В task_handler! 🔴🔴🔴")

    query = update.callback_query
    await query.answer()

    print(f"📥 Получен callback: '{query.data}'")

    task_id_str = query.data.replace("task_", "")
    try:
        task_id = int(task_id_str)
        print(f"✅ Успешно преобразовал task_id в число: {task_id}")
    except ValueError:
        print(f"❌ ОШИБКА: не удалось преобразовать '{task_id_str}' в число")
        await query.edit_message_text("❌ Ошибка формата задачи.")
        return TASKS_MENU

    user_id = update.effective_user.id
    print(f"🔍 Ищу задачу в БД: user_id={user_id}, task_id={task_id}")

    # Убедитесь, что эта функция есть в database.py и импортирована здесь!
    from database import get_task_by_id
    task = get_task_by_id(user_id, task_id)

    if not task:
        print(f"❌ ЗАДАЧА НЕ НАЙДЕНА В БД!")
        await query.edit_message_text("❌ Задача не найдена или удалена.")
        return TASKS_MENU

    print(f"✅ ЗАДАЧА НАЙДЕНА: {task[2]}")

    status = "✅ Выполнено" if task[6] else "🟢 Активна"
    deadline_text = task[5] if task[5] else "Не указан"

    message = (
        f"{status}\n\n"
        f"📌 *{task[2]}*\n\n"
        f"Приоритет: {task[3]}\n"
        f"Создана: {task[4]}\n"
        f"Дедлайн: {deadline_text}\n"
    )
    if task[6]:
        message += f"\nВыполнено: {task[6]}"

    keyboard = [
        [InlineKeyboardButton("✅ Выполнить", callback_data=f"complete_{task_id}")],
        [InlineKeyboardButton("✏️ Изменить", callback_data=f"edit_{task_id}")],
        [InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_{task_id}")],
        [InlineKeyboardButton("⬅️ Назад к списку", callback_data="back_to_tasks")],
    ]

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return TASKS_MENU



async def complete_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    task_id = int(query.data.replace("complete_", ""))
    user_id = update.effective_user.id
    time_accomplished = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    complete_task(user_id, task_id, time_accomplished)

    keyboard = [[InlineKeyboardButton("⬅️ К списку задач", callback_data="back_to_tasks")]]
    await query.edit_message_text(
        "✅ Задача успешно выполнена!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASKS_MENU


async def delete_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    task_id = int(query.data.replace("delete_", ""))
    user_id = update.effective_user.id

    delete_task(user_id, task_id)

    keyboard = [[InlineKeyboardButton("⬅️ К списку задач", callback_data="back_to_tasks")]]
    await query.edit_message_text(
        "🗑 Задача успешно удалена.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASKS_MENU


async def edit_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    task_id = int(query.data.replace("edit_", ""))
    context.user_data["editing_task_id"] = task_id

    # МЕНЯЕМ ЗДЕСЬ: используем существующий обработчик возврата
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_tasks")]]
    await query.edit_message_text(
        "✏️ Введите новое название для этой задачи (или нажмите Отмена):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return EDIT_TITLE

async def back_to_tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # ДОБАВИТЬ ЭТУ СТРОКУ: очищаем флаг редактирования при любом возврате назад
    context.user_data.pop("editing_task_id", None)

    page = context.user_data.get("tasks_page", 0)
    status_filter = context.user_data.get("status_filter")
    # ... дальше весь ваш старый код без изменений ...


async def save_edited_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_title = update.message.text
    task_id = context.user_data.get("editing_task_id")
    user_id = update.effective_user.id

    update_task_title(user_id, task_id, new_title)

    # Очищаем временные данные
    context.user_data.pop("editing_task_id", None)

    keyboard = [[InlineKeyboardButton("⬅️ К списку задач", callback_data="back_to_tasks")]]
    await update.message.reply_text(
        "✅ Название задачи обновлено!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASKS_MENU


async def back_to_tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Умный возврат к списку задач с сохранением фильтров и страницы"""
    query = update.callback_query
    await query.answer()

    page = context.user_data.get("tasks_page", 0)
    status_filter = context.user_data.get("status_filter")
    time_filter = context.user_data.get("time_filter")
    user_id = update.effective_user.id

    total_tasks = get_tasks_count(user_id, status_filter, time_filter)

    if total_tasks == 0:
        keyboard = [[InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_menu")]]
        await query.edit_message_text(
            "Задач не найдено.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return TASKS_MENU

    total_pages = (total_tasks + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE

    # Защита от выхода за границы страниц при удалении задач
    if page >= total_pages:
        page = total_pages - 1
        context.user_data["tasks_page"] = page

    tasks = get_tasks_page(user_id, page, status_filter, time_filter, TASKS_PER_PAGE)

    message = build_tasks_message(tasks, page, total_tasks)

    # Определяем префикс для кнопок пагинации
    prefix = "filtered" if (status_filter or time_filter) else "all"
    keyboard = create_tasks_keyboard(tasks, page, total_pages, prefix)

    await query.edit_message_text(message, reply_markup=keyboard)
    return TASKS_MENU