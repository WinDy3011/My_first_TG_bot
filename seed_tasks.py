import sqlite3
import random
from datetime import datetime, timedelta
from database import DB_PATH, init_db
from config import DB_PATH


USER_ID = 896886297
TASK_COUNT = 1000


TITLES = [
    "Изучить Python",
    "Изучить SQLite",
    "Разобраться с Git",
    "Написать Telegram-бота",
    "Исправить баг",
    "Добавить новую функцию",
    "Изучить threading",
    "Прочитать документацию",
    "Сделать домашнее задание",
    "Написать тесты",
    "Оптимизировать код",
    "Разобраться с API",
    "Создать новый модуль",
    "Обновить README",
    "Проверить базу данных",
]


def generate_deadline(now):
    """Генерирует дедлайн в разных временных диапазонах."""

    deadline_type = random.choices(
        [
            "overdue",
            "today",
            "tomorrow",
            "3_days",
            "week",
            "later",
        ],
        weights=[
            15,  # просроченные
            15,  # сегодня
            15,  # завтра
            20,  # следующие 3 дня
            20,  # следующие 7 дней
            15,  # позже
        ]
    )[0]

    if deadline_type == "overdue":
        deadline = now - timedelta(
            days=random.randint(1, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

    elif deadline_type == "today":
        deadline = now + timedelta(
            hours=random.randint(0, 12),
            minutes=random.randint(0, 59)
        )

    elif deadline_type == "tomorrow":
        deadline = now + timedelta(
            days=1,
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

    elif deadline_type == "3_days":
        deadline = now + timedelta(
            days=random.randint(2, 3),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

    elif deadline_type == "week":
        deadline = now + timedelta(
            days=random.randint(4, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

    else:
        deadline = now + timedelta(
            days=random.randint(8, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

    return deadline


def generate_tasks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now()

    for i in range(TASK_COUNT):

        title = f"{random.choice(TITLES)} #{i + 1}"

        # Приоритет
        priority = random.choices(
            ["low", "medium", "high"],
            weights=[50, 35, 15]
        )[0]

        # Время создания задачи
        time_inserted = now - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        # Дедлайн
        deadline = generate_deadline(now)

        # Статус задачи
        is_completed = random.choices(
            [True, False],
            weights=[20, 80]
        )[0]

        if is_completed:
            # Задача была выполнена после создания
            time_accomplished = time_inserted + timedelta(
                hours=random.randint(1, 72),
                minutes=random.randint(0, 59)
            )

            # На всякий случай не ставим выполнение позже текущего момента
            if time_accomplished > now:
                time_accomplished = now

        else:
            time_accomplished = None

        cursor.execute(
            """
            INSERT INTO tasks (
                user_id,
                title,
                priority,
                time_inserted,
                deadline,
                time_accomplished
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                USER_ID,
                title,
                priority,
                time_inserted.strftime("%Y-%m-%d %H:%M:%S"),
                deadline.strftime("%Y-%m-%d %H:%M:%S"),
                (
                    time_accomplished.strftime("%Y-%m-%d %H:%M:%S")
                    if time_accomplished
                    else None
                )
            )
        )

    conn.commit()
    conn.close()

    print(f"Создано {TASK_COUNT} тестовых задач.")


if __name__ == "__main__":
    init_db()
    generate_tasks()