import os

TOKEN = "8706072606:AAFIBPEAYUtifW_BmYgKqd0jOXvpKowmlVQ" #os.getenv('BOT_TOKEN')
DB_PATH = os.getenv('DB_PATH', 'tasks.db')

# состояния диалогов — все в одном месте, чтобы не было конфликтов номеров
TITLE, PRIORITY = range(2)
TASKS_MENU, FILTER_STATUS, FILTER_TIME = range(2, 5)
EDIT_TITLE = 5