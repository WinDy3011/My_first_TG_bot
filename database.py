import sqlite3
from datetime import datetime, timedelta

from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id_task INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            priority TEXT,
            time_inserted TEXT,
            deadline TEXT,
            time_accomplished TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_task(user_id, title, priority, time_inserted, deadline=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (
            user_id,
            title,
            priority,
            time_inserted,
            deadline
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            title,
            priority,
            time_inserted,
            deadline
        )
    )

    conn.commit()
    conn.close()


def get_all_tasks(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM tasks
        WHERE user_id = ?
        ORDER BY id_task DESC
        """,
        (user_id,)
    )

    tasks = cursor.fetchall()

    conn.close()

    return tasks


def get_tasks_count(user_id, status_filter=None, time_filter=None):
    """
    Возвращает количество задач,
    соответствующих фильтрам.
    """

    conditions = ["user_id = ?"]
    params = [user_id]

    # Фильтр по статусу
    if status_filter == "status_active":
        conditions.append("time_accomplished IS NULL")

    elif status_filter == "status_completed":
        conditions.append("time_accomplished IS NOT NULL")

    # Фильтр по времени
    today = datetime.now().date()

    if time_filter == "time_today":
        start_date = today
        end_date = today

    elif time_filter == "time_tomorrow":
        start_date = today + timedelta(days=1)
        end_date = start_date

    elif time_filter == "time_3days":
        start_date = today
        end_date = today + timedelta(days=3)

    elif time_filter == "time_week":
        start_date = today
        end_date = today + timedelta(days=7)

    else:
        start_date = None
        end_date = None

    if start_date is not None:
        conditions.append(
            "date(deadline) BETWEEN ? AND ?"
        )

        params.extend([
            start_date.isoformat(),
            end_date.isoformat()
        ])

    query = f"""
        SELECT COUNT(*)
        FROM tasks
        WHERE {' AND '.join(conditions)}
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, params)

    count = cursor.fetchone()[0]

    conn.close()

    return count


def get_tasks_page(
    user_id,
    page=0,
    status_filter=None,
    time_filter=None,
    per_page=10
):
    """
    Возвращает одну страницу задач.

    page=0 -> задачи 1-10
    page=1 -> задачи 11-20
    page=2 -> задачи 21-30
    """

    conditions = ["user_id = ?"]
    params = [user_id]

    # -------------------------
    # Фильтр по статусу
    # -------------------------

    if status_filter == "status_active":
        conditions.append("time_accomplished IS NULL")

    elif status_filter == "status_completed":
        conditions.append("time_accomplished IS NOT NULL")

    # -------------------------
    # Фильтр по времени
    # -------------------------

    today = datetime.now().date()

    if time_filter == "time_today":
        start_date = today
        end_date = today

    elif time_filter == "time_tomorrow":
        start_date = today + timedelta(days=1)
        end_date = start_date

    elif time_filter == "time_3days":
        start_date = today
        end_date = today + timedelta(days=3)

    elif time_filter == "time_week":
        start_date = today
        end_date = today + timedelta(days=7)

    else:
        start_date = None
        end_date = None

    if start_date is not None:
        conditions.append(
            "date(deadline) BETWEEN ? AND ?"
        )

        params.extend([
            start_date.isoformat(),
            end_date.isoformat()
        ])

    offset = page * per_page

    query = f"""
        SELECT *
        FROM tasks
        WHERE {' AND '.join(conditions)}
        ORDER BY id_task DESC
        LIMIT ? OFFSET ?
    """

    params.extend([
        per_page,
        offset
    ])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(query, params)

    tasks = cursor.fetchall()

    conn.close()

    return tasks

def complete_task(user_id, task_id, time_accomplished):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET time_accomplished = ?
        WHERE id_task = ? AND user_id = ?
        """,
        (time_accomplished, task_id, user_id)
    )

    conn.commit()
    conn.close()

def delete_task(user_id, task_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM tasks WHERE id_task = ? AND user_id = ?",
        (task_id, user_id)
    )
    conn.commit()
    conn.close()


def update_task_title(user_id, task_id, new_title):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET title = ? WHERE id_task = ? AND user_id = ?",
        (new_title, task_id, user_id)
    )
    conn.commit()
    conn.close()


# Добавьте это в конец database.py

def get_task_by_id(user_id, task_id):
    """Возвращает одну конкретную задачу по ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tasks WHERE id_task = ? AND user_id = ?",
        (task_id, user_id)
    )
    task = cursor.fetchone()
    conn.close()
    return task