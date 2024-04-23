import datetime
import sqlite3

from User import User
from Task import Task


def db_user_data_table_insert(user_id: int, user_name: str, user_surname: str, username: str, user_status: int) -> None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO user_data (user_id, user_name, user_surname, username, user_status) '
                   'VALUES (?, ?, ?, ?, ?)', (user_id, user_name, user_surname, username, user_status))
    conn.commit()
    conn.close()


def db_get_all_users() -> list:
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
                               task_deadline: datetime, assigned_users_id: str, task_status: str) -> None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO user_tasks (task_name, task_description, importance_level, task_setting_time,'
                   'task_deadline, assigned_users_id, task_status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_users_id, task_status))
    conn.commit()
    conn.close()


def db_get_all_tasks() -> list:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT id, task_name, task_description, importance_level, task_setting_time, task_deadline, '
                   'assigned_users_id, task_status FROM user_tasks')
    rows = cursor.fetchall()
    tasks = []
    if rows:
        for row in rows:
            task_id, task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_users_id_str, task_status = row
            assigned_users_id_list = list(map(int, assigned_users_id_str.split(',')))
            task = Task(task_id, task_name, task_description, importance_level, task_setting_time, task_deadline,
                        assigned_users_id_list, task_status)
            tasks.append(task)

    conn.close()
    return tasks


def db_get_user_data(user_id: int) -> str or None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT user_name, user_surname FROM user_data WHERE user_id={user_id}')
        user_details = cursor.fetchone()
        if user_details:
            user_name, user_surname = user_details
            return f"{user_name} {user_surname}"

        else:
            return None

    finally:
        conn.close()


def db_get_tasks_for_user(user_id: str) -> Task or list or None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    query = 'SELECT id, task_name, task_description, importance_level, task_setting_time, task_deadline, ' \
            'assigned_users_id, task_status FROM user_tasks WHERE assigned_users_id LIKE ?'
    pattern = f'%{user_id}%'
    try:
        cursor.execute(query, (pattern,))
        task_details_list = cursor.fetchall()
        if task_details_list:
            if len(task_details_list) == 1:
                task_details = task_details_list[0]
                task_id, task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_users_id_str, task_status = task_details
                assigned_users_id_list = list(map(int, assigned_users_id_str.split(',')))

                return [Task(task_id, task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_users_id_list, task_status)]

            else:
                tasks = []
                for task_details in task_details_list:
                    task_id, task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_users_id_str, task_status = task_details
                    assigned_users_id_list = list(map(int, assigned_users_id_str.split(',')))
                    task = Task(task_id, task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_users_id_list, task_status)
                    tasks.append(task)

                return tasks

        else:
            return None

    finally:
        conn.close()


def db_delete_task(task_id: int) -> None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM user_tasks WHERE id={task_id}')
    conn.commit()
    conn.close()


def db_task_status_update(task_id: int, task_status: str) -> None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE user_tasks SET task_status='{task_status}' WHERE id={task_id}")
    conn.commit()
    conn.close()


def db_report_table_insert(user_id: int, task_id: int, send_time: datetime, report_text: str, report_files: int) -> None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO task_reports (user_id, task_id, send_time, report_text, report_files) '
                   'VALUES (?, ?, ?, ?, ?)', (user_id, task_id, send_time, report_text, report_files))

    conn.commit()
    conn.close()


def db_files_table_insert(report_id: int, file_id: str, file_type: str) -> None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO file_attachments (report_id, file_id, file_type) VALUES (?, ?, ?)',
                   (report_id, file_id, file_type))

    conn.commit()
    conn.close()
