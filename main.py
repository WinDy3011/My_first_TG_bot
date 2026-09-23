import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters
)

from config import TOKEN, TITLE, PRIORITY, TASKS_MENU, FILTER_STATUS, FILTER_TIME, EDIT_TITLE
from database import init_db
from handlers.start import start, cancel, unknown
from handlers.add_task import add_task_start, add_title, get_priority
from handlers.show_tasks import (
    tasks_start,
    tasks_menu_handler,
    filter_status_handler,
    filter_time_handler,
    task_handler,
    complete_task_handler,
    delete_task_handler,
    edit_task_handler,
    save_edited_title,
    back_to_tasks_handler,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    init_db()
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))

    add_task_conv = ConversationHandler(
        entry_points=[CommandHandler('addtask', add_task_start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
            PRIORITY: [CallbackQueryHandler(get_priority)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_message=False,  # Явно указываем, чтобы избежать варнингов
        per_chat=True,
    )
    application.add_handler(add_task_conv)

    tasks_conv = ConversationHandler(
        entry_points=[CommandHandler('tasks', tasks_start)],
        states={
            TASKS_MENU: [
                CallbackQueryHandler(task_handler, pattern=r"^task_\d+$"),
                CallbackQueryHandler(complete_task_handler, pattern=r"^complete_\d+$"),
                CallbackQueryHandler(delete_task_handler, pattern=r"^delete_\d+$"),
                CallbackQueryHandler(edit_task_handler, pattern=r"^edit_\d+$"),
                CallbackQueryHandler(back_to_tasks_handler, pattern=r"^back_to_tasks$"),
                CallbackQueryHandler(tasks_menu_handler),
            ],
            FILTER_STATUS: [CallbackQueryHandler(filter_status_handler)],
            FILTER_TIME: [CallbackQueryHandler(filter_time_handler)],
            EDIT_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_title),
                CallbackQueryHandler(back_to_tasks_handler, pattern=r"^back_to_tasks$"),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        per_message=False,  # Явно указываем, чтобы избежать варнингов
        per_chat=True,
    )
    application.add_handler(tasks_conv)

    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    try:
        application.run_polling()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == '__main__':
    main()