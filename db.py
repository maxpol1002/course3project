import datetime
import sqlite3

from User import User
from Task import Task
from Report import Report
from File import File


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
    cursor.execute("SELECT id, task_name, task_description, importance_level, task_setting_time, task_deadline, "
                   "assigned_users_id, task_status "
                   "FROM user_tasks "
                   "WHERE task_status='incomplete' OR task_status='pending'")
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


def db_get_tasks_for_user(user_id: str, task_status=None) -> Task or list or None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    if task_status == "pending" or task_status == "completed" or task_status == "incomplete":
        query = f"SELECT id, task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_users_id, task_status " \
                f"FROM user_tasks " \
                f"WHERE assigned_users_id LIKE ? AND task_status='{task_status}'"

    else:
        query = f"SELECT id, task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_users_id, task_status " \
                f"FROM user_tasks " \
                f"WHERE assigned_users_id LIKE ?"

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


def db_report_table_insert(user_id: int, task_id: int, send_time: datetime, report_text: str, report_status: str) -> None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO task_reports (user_id, task_id, send_time, report_text, report_status) '
                   'VALUES (?, ?, ?, ?, ?)', (user_id, task_id, send_time, report_text, report_status))

    conn.commit()
    conn.close()


def db_report_status_update(report_id: int, report_status: str) -> None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE task_reports SET report_status='{report_status}' WHERE id={report_id}")
    conn.commit()
    conn.close()


def db_files_table_insert(report_id: int, file_id: str, file_type: str) -> None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO file_attachments (report_id, file_id, file_type) VALUES (?, ?, ?)',
                   (report_id, file_id, file_type))

    conn.commit()
    conn.close()


def db_get_report_id(user_id: int, task_id: int) -> int:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f'SELECT id FROM task_reports WHERE user_id={user_id} AND task_id={task_id}')
    report_id = cursor.fetchone()
    conn.close()
    return report_id[0]


def db_get_reports(status: str):
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT tr.id, tr.user_id, tr.task_id, tr.send_time, tr.report_text, tr.report_status,
        GROUP_CONCAT(fa.file_id || ':' || fa.file_type) AS file_details 
        FROM task_reports AS tr
        LEFT JOIN file_attachments AS fa ON tr.id = fa.report_id
        WHERE tr.report_status='{status}'
        GROUP BY tr.id
    ''')
    reports = []
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            report_id, user_id, task_id, send_time, report_text, report_status, file_details = row
            if file_details:
                file_details_list = file_details.split(",")
                files_list = []
                for file in file_details_list:
                    file_id, file_type = file.split(":")
                    files_list.append(File(file_id, file_type))

                report = Report(report_id, user_id, task_id, send_time, report_text, report_status, files_list)
            else:
                report = Report(report_id, user_id, task_id, send_time, report_text, report_status, None)
            reports.append(report)

        return reports

    else:
        return None





