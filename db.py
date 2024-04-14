import datetime
import sqlite3
from User import User
from Task import Task


def db_user_data_table_insert(user_id: int, user_name: str, user_surname: str, username: str, user_status: int):
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO user_data (user_id, user_name, user_surname, username, user_status) '
                   'VALUES (?, ?, ?, ?, ?)', (user_id, user_name, user_surname, username, user_status))
    conn.commit()
    conn.close()


def db_get_all_users():
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, user_name, user_surname, username FROM user_data')
    rows = cursor.fetchall()
    users = []
    if rows:
        for row in rows:
            user_id, user_name, user_surname, username = row
            user = User(user_id, user_name, user_surname, username)
            users.append(user)

    conn.close()
    return users


def db_user_tasks_table_insert(task_name: str, task_description: str, importance_level: int, task_setting_time: datetime,
                               task_deadline: datetime, assigned_users_id: str):
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO user_tasks (task_name, task_description, importance_level, task_setting_time,'
                   'task_deadline, assigned_users_id) VALUES (?, ?, ?, ?, ?, ?)',
                   (task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_users_id))
    conn.commit()
    conn.close()


def db_get_all_tasks():
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT id, task_name, task_description, importance_level, task_setting_time, task_deadline, '
                   'assigned_users_id FROM user_tasks')
    rows = cursor.fetchall()
    tasks = []
    if rows:
        for row in rows:
            task_id, task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_users_id = row
            task = Task(task_id, task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_users_id)
            tasks.append(task)

    conn.close()
    return tasks

