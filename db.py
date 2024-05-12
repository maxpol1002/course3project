import datetime
import sqlite3

from DailyReport import DailyReport
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
    cursor.execute('''
        SELECT ut.id, ut.task_name, ut.task_description, ut.importance_level, ut.task_setting_time, ut.task_deadline, 
        ut.assigned_users_id, ut.task_status, GROUP_CONCAT(fa.file_id || ':' || fa.file_type) AS file_details
        FROM user_tasks as ut
        LEFT JOIN file_attachments AS fa ON ut.id = fa.report_id AND fa.task_type = 'task'
        WHERE task_status='incomplete' OR task_status='pending' AND (fa.report_id IS NULL OR fa.task_type = 'task')
        GROUP BY ut.id
    ''')
    rows = cursor.fetchall()
    tasks = []
    if rows:
        for row in rows:
            task_id, task_name, task_description, importance_level, task_setting_time, task_deadline, \
                assigned_users_id_str, task_status, file_details = row
            assigned_users_id_list = list(map(int, assigned_users_id_str.split(',')))
            if file_details:
                file_details_list = file_details.split(",")
                files_list = []
                for file in file_details_list:
                    file_id, file_type = file.split(":")
                    files_list.append(File(file_id, file_type))
                task = Task(task_id, task_name, task_description, importance_level, task_setting_time, task_deadline,
                            assigned_users_id_list, task_status, files_list)
            else:
                task = Task(task_id, task_name, task_description, importance_level, task_setting_time, task_deadline,
                            assigned_users_id_list, task_status, None)
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


def db_get_daily_reports():
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT dr.id, dr.user_id, dr.report_name, dr.report_desc, dr.time_sent,
        GROUP_CONCAT(fa.file_id || ':' || fa.file_type) AS file_details
        FROM daily_reports as dr
        LEFT JOIN file_attachments AS fa ON dr.id = fa.report_id AND fa.task_type = 'daily_report'
        WHERE fa.report_id IS NULL OR fa.task_type = 'daily_report'
        GROUP BY dr.id
    ''')
    daily_reports = []
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            report_id, user_id, report_name, report_desc, send_time, file_details = row
            if file_details:
                file_details_list = file_details.split(",")
                files_list = []
                for file in file_details_list:
                    file_id, file_type = file.split(":")
                    files_list.append(File(file_id, file_type))

                report = DailyReport(report_id, user_id, report_name, report_desc, send_time, files_list)
            else:
                report = DailyReport(report_id, user_id, report_name, report_desc, send_time, None)
            daily_reports.append(report)

        return daily_reports

    else:
        return None


def db_get_tasks_for_user(user_id: str, task_status: str) -> list[Task] or None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    query = f'''
        SELECT ut.id, ut.task_name, ut.task_description, ut.importance_level, ut.task_setting_time, ut.task_deadline, 
        ut.assigned_users_id, ut.task_status, GROUP_CONCAT(fa.file_id || ':' || fa.file_type) AS file_details
        FROM user_tasks as ut
        LEFT JOIN file_attachments AS fa ON ut.id = fa.report_id AND fa.task_type = 'task'
        WHERE assigned_users_id LIKE ? AND task_status='{task_status}' AND (fa.report_id IS NULL OR fa.task_type = 'task')
        GROUP BY ut.id
        '''

    pattern = f'%{user_id}%'
    try:
        cursor.execute(query, (pattern,))
        task_details_list = cursor.fetchall()
        if task_details_list:
            if len(task_details_list) == 1:
                task_details = task_details_list[0]
                task_id, task_name, task_description, importance_level, task_setting_time, \
                    task_deadline, assigned_users_id_str, task_status, file_details = task_details
                assigned_users_id_list = list(map(int, assigned_users_id_str.split(',')))
                if file_details:
                    file_details_list = file_details.split(",")
                    files_list = []
                    for file in file_details_list:
                        file_id, file_type = file.split(":")
                        files_list.append(File(file_id, file_type))

                    return [Task(task_id, task_name, task_description, importance_level, task_setting_time,
                                 task_deadline, assigned_users_id_list, task_status, files_list)]
                else:
                    return [Task(task_id, task_name, task_description, importance_level, task_setting_time,
                                 task_deadline, assigned_users_id_list, task_status, None)]

            else:
                tasks = []
                for task_details in task_details_list:
                    task_id, task_name, task_description, importance_level, task_setting_time, task_deadline, \
                        assigned_users_id_str, task_status, file_details = task_details
                    assigned_users_id_list = list(map(int, assigned_users_id_str.split(',')))
                    if file_details:
                        file_details_list = file_details.split(",")
                        files_list = []
                        for file in file_details_list:
                            file_id, file_type = file.split(":")
                            files_list.append(File(file_id, file_type))
                        task = Task(task_id, task_name, task_description, importance_level, task_setting_time,
                                    task_deadline, assigned_users_id_list, task_status, files_list)
                    else:
                        task = Task(task_id, task_name, task_description, importance_level, task_setting_time,
                                    task_deadline, assigned_users_id_list, task_status, None)
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


def db_files_table_insert(report_id: int, file_id: str, file_type: str, task_type: str) -> None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO file_attachments (report_id, file_id, file_type, task_type) VALUES (?, ?, ?, ?)',
                   (report_id, file_id, file_type, task_type))

    conn.commit()
    conn.close()


def db_get_report_id(user_id: int, task_id: int) -> int:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f'SELECT id FROM task_reports WHERE user_id={user_id} AND task_id={task_id}')
    report_id = cursor.fetchone()
    conn.close()
    return report_id[0]


def db_get_daily_rep_id(user_id: int, report_desc: str) -> int:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM daily_reports WHERE user_id={user_id} AND report_desc='{report_desc}'")
    report_id = cursor.fetchone()
    conn.close()
    return report_id[0]


def db_get_task_id(task_name: str, task_desc: str) -> int:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM user_tasks WHERE task_name='{task_name}' AND task_description='{task_desc}'")
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
        LEFT JOIN file_attachments AS fa ON tr.id = fa.report_id AND fa.task_type = 'task_report'
        WHERE tr.report_status = '{status}' AND (fa.report_id IS NULL OR fa.task_type = 'task_report')
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


def db_daily_report_insert(user_id: int, report_name: str, report_desc: str, time_sent: str) -> None:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO daily_reports (user_id, report_name, report_desc, time_sent)"
        "VALUES (?, ?, ?, ?)", (user_id, report_name, report_desc, time_sent)
    )
    conn.commit()
    conn.close()


def db_get_task_name(task_id: int) -> str:
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"SELECT task_name FROM user_tasks WHERE id='{task_id}'")
    task_name = cursor.fetchone()
    conn.close()
    return task_name[0]
