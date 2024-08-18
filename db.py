import datetime
import os

import psycopg2

from classes.User import User
from classes.Task import Task
from classes.File import File
from classes.Report import Report
from classes.DailyReport import DailyReport


DB_URI = os.getenv('DATABASE_URL')


def db_user_data_table_insert(user_id: int, user_name: str, user_surname: str, username: str, user_status: int) -> None:
    try:
        db_conn = psycopg2.connect(DB_URI, sslmode="require")
        cursor = db_conn.cursor()

        cursor.execute('INSERT INTO user_data (user_id, user_name, user_surname, username, user_status) '
                       'VALUES (%s, %s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING',
                       (user_id, user_name, user_surname, username, user_status))

        db_conn.commit()

    except Exception as e:
        print(f"Error: {e}")
        db_conn.rollback()

    finally:
        # Close the cursor
        cursor.close()


def db_get_all_users() -> list:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    with db_conn.cursor() as cursor:
        query = 'SELECT user_id, user_name, user_surname, username FROM user_data WHERE user_status=0'
        cursor.execute(query)
        rows = cursor.fetchall()

    users = []
    for row in rows:
        user_id, user_name, user_surname, username = row
        if not user_surname:
            user_surname = " "

        user = User(user_id, user_name, user_surname, username)
        users.append(user)

    return users


def db_user_tasks_table_insert(task_name: str, task_description: str, importance_level: int, task_setting_time: datetime,
                               task_deadline: datetime, assigned_user_id: int, task_status: str) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    with db_conn.cursor() as cursor:
        query = '''
            INSERT INTO user_tasks (task_name, task_description, importance_level, task_setting_time, 
                                    task_deadline, assigned_user_id, task_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        '''
        cursor.execute(query, (task_name, task_description, importance_level, task_setting_time, task_deadline, assigned_user_id, task_status))
        db_conn.commit()


def db_get_all_tasks(task_status=None) -> list:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    with db_conn.cursor() as cursor:
        if task_status is None:
            query = '''
                SELECT ut.id, ut.task_name, ut.task_description, ut.importance_level, ut.task_setting_time, ut.task_deadline, 
                ut.assigned_user_id, ut.task_status, STRING_AGG(fa.file_id || ':' || fa.file_type, ',') AS file_details
                FROM user_tasks as ut
                LEFT JOIN file_attachments AS fa ON ut.id = fa.report_id AND fa.task_type = 'task'
                WHERE (task_status='incomplete' OR task_status='pending') AND (fa.report_id IS NULL OR fa.task_type = 'task')
                GROUP BY ut.id
            '''
        elif task_status == 1:
            query = '''
                SELECT ut.id, ut.task_name, ut.task_description, ut.importance_level, ut.task_setting_time, ut.task_deadline, 
                ut.assigned_user_id, ut.task_status, STRING_AGG(fa.file_id || ':' || fa.file_type, ',') AS file_details
                FROM user_tasks as ut
                LEFT JOIN file_attachments AS fa ON ut.id = fa.report_id AND fa.task_type = 'task'
                WHERE task_status='completed' AND (fa.report_id IS NULL OR fa.task_type = 'task')
                GROUP BY ut.id
            '''
        elif task_status == 2:
            query = '''
                SELECT ut.id, ut.task_name, ut.task_description, ut.importance_level, ut.task_setting_time, ut.task_deadline, 
                ut.assigned_user_id, ut.task_status, STRING_AGG(fa.file_id || ':' || fa.file_type, ',') AS file_details
                FROM user_tasks as ut
                LEFT JOIN file_attachments AS fa ON ut.id = fa.report_id AND fa.task_type = 'task'
                WHERE task_status='incomplete' AND (fa.report_id IS NULL OR fa.task_type = 'task')
                GROUP BY ut.id
            '''

        cursor.execute(query)
        rows = cursor.fetchall()

    tasks = []
    for row in rows:
        task_id, task_name, task_description, importance_level, task_setting_time, task_deadline, \
            assigned_user_id, task_status, file_details = row

        if file_details:
            file_details_list = file_details.split(",")
            files_list = []
            for file in file_details_list:
                file_id, file_type = file.split(":")
                files_list.append(File(file_id, file_type))
            task = Task(task_id, task_name, task_description, importance_level, task_setting_time, task_deadline,
                        assigned_user_id, task_status, files_list)
        else:
            task = Task(task_id, task_name, task_description, importance_level, task_setting_time, task_deadline,
                        assigned_user_id, task_status, None)
        tasks.append(task)

    return tasks


def db_get_user_data(user_id: int) -> str or None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    with db_conn.cursor() as cursor:
        query = 'SELECT user_name, user_surname FROM user_data WHERE user_id = %s'
        try:
            cursor.execute(query, (user_id,))
            user_details = cursor.fetchone()
            if user_details:
                user_name, user_surname = user_details
                if not user_surname:
                    return f"{user_name}"

                return f"{user_name} {user_surname}"
            else:
                return None

        except psycopg2.Error as e:
            print(f"Error fetching user data: {e}")

            return None


def db_get_daily_reports() -> list[Report] or None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    try:
        conn = db_conn
        cursor = conn.cursor()
        cursor.execute('''
               SELECT dr.id, dr.user_id, dr.report_name, dr.report_desc, dr.time_sent,
               STRING_AGG(fa.file_id || ':' || fa.file_type, ',') AS file_details
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

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    finally:
        cursor.close()


def db_get_tasks_for_user(user_id: int, task_status: str) -> list[Task] or None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    cursor = db_conn.cursor()
    query = '''
            SELECT ut.id, ut.task_name, ut.task_description, ut.importance_level, ut.task_setting_time, ut.task_deadline, 
            ut.assigned_user_id, ut.task_status, STRING_AGG(fa.file_id || ':' || fa.file_type, ',') AS file_details
            FROM user_tasks as ut
            LEFT JOIN file_attachments AS fa ON ut.id = fa.report_id AND fa.task_type = 'task'
            WHERE assigned_user_id=%s AND task_status=%s AND (fa.report_id IS NULL OR fa.task_type = 'task')
            GROUP BY ut.id
        '''

    try:
        cursor.execute(query, (user_id, task_status))
        task_details_list = cursor.fetchall()
        if task_details_list:
            tasks = []
            for task_details in task_details_list:
                task_id, task_name, task_description, importance_level, task_setting_time, task_deadline, \
                    assigned_user_id, task_status, file_details = task_details

                if file_details:
                    file_details_list = file_details.split(",")
                    files_list = []
                    for file in file_details_list:
                        file_id, file_type = file.split(":")
                        files_list.append(File(file_id, file_type))
                    task = Task(task_id, task_name, task_description, importance_level, task_setting_time,
                                task_deadline, assigned_user_id, task_status, files_list)

                else:
                    task = Task(task_id, task_name, task_description, importance_level, task_setting_time,
                                task_deadline, assigned_user_id, task_status, None)
                tasks.append(task)

            return tasks

        else:
            return None

    finally:
        cursor.close()


def db_delete_task(task_id: int) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    cursor = db_conn.cursor()
    try:
        cursor.execute('DELETE FROM user_tasks WHERE id = %s', (task_id,))
        db_conn.commit()

    finally:
        cursor.close()
        db_conn.close()


def db_delete_file(attached_id: int, task_type: str) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    cursor = db_conn.cursor()
    try:
        cursor.execute('DELETE FROM file_attachments WHERE report_id = %s AND task_type = %s', (attached_id, task_type))
        db_conn.commit()
    finally:
        cursor.close()
        db_conn.close()


def db_delete_daily_rep(rep_id: int) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    cursor = db_conn.cursor()
    try:
        cursor.execute('DELETE FROM daily_reports WHERE id = %s', (rep_id,))
        db_conn.commit()

    finally:
        cursor.close()
        db_conn.close()


def db_delete_report(rep_id: int) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    cursor = db_conn.cursor()
    try:
        cursor.execute("DELETE FROM task_reports WHERE id = %s", (rep_id,))
        db_conn.commit()

    finally:
        cursor.close()
        db_conn.close()


def db_task_status_update(task_id: int, task_status: str) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    cursor = db_conn.cursor()
    try:
        cursor.execute("UPDATE user_tasks SET task_status = %s WHERE id = %s", (task_status, task_id))
        db_conn.commit()

    finally:
        cursor.close()
        db_conn.close()


def db_report_table_insert(user_id: int, task_id: int, send_time: datetime, report_text: str, report_status: str, task_name: str) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    cursor = db_conn.cursor()
    try:
        cursor.execute('''
                INSERT INTO task_reports (user_id, task_id, send_time, report_text, report_status, task_name) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, task_id, send_time, report_text, report_status, task_name))
        db_conn.commit()

    finally:
        cursor.close()
        db_conn.close()


def db_report_status_update(report_id: int, report_status: str) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    cursor = db_conn.cursor()
    try:
        cursor.execute("UPDATE task_reports SET report_status = %s WHERE id = %s", (report_status, report_id))
        db_conn.commit()

    finally:
        cursor.close()
        db_conn.close()


def db_files_table_insert(report_id: int, file_id: str, file_type: str, task_type: str) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    with db_conn.cursor() as cursor:
        query = '''
            INSERT INTO file_attachments (report_id, file_id, file_type, task_type)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        '''
        try:
            cursor.execute(query, (report_id, file_id, file_type, task_type))
            db_conn.commit()
        except psycopg2.Error as e:
            # Handle the error, e.g., log it or raise an exception
            print(f"Error inserting file attachment: {e}")


def db_get_report_id(user_id: int, task_id: int) -> int:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    cursor = db_conn.cursor()
    try:
        cursor.execute("SELECT id FROM task_reports WHERE user_id = %s AND task_id = %s AND report_status = %s",
                       (user_id, task_id, 'pending'))
        report_id = cursor.fetchone()
        if report_id:
            return report_id[0]
        else:
            return None

    finally:
        cursor.close()
        db_conn.close()


def db_get_daily_rep_id(user_id: int, report_desc: str) -> int:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    cursor = db_conn.cursor()
    try:
        # Use parameterized queries
        cursor.execute("SELECT id FROM daily_reports WHERE user_id = %s AND report_desc = %s",
                       (user_id, report_desc))
        report_id = cursor.fetchone()
        if report_id:
            return report_id[0]
        else:
            return None

    finally:
        cursor.close()
        db_conn.close()


def db_get_task_id(task_setting_time: str, task_name: str, task_description: str) -> int or None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    with db_conn.cursor() as cursor:
        query = '''
            SELECT id 
            FROM user_tasks 
            WHERE task_setting_time = %s 
              AND task_name = %s 
              AND task_description = %s
        '''
        try:
            cursor.execute(query, (task_setting_time, task_name, task_description))
            task_id = cursor.fetchone()
            if task_id:
                return task_id[0]
            else:
                return None

        except psycopg2.Error as e:
            print(f"Error fetching task ID: {e}")
            return None


def db_get_reports(status: str) -> list[Report] or None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    try:
        cursor = db_conn.cursor()
        query = '''
                SELECT tr.id, tr.user_id, tr.task_id, tr.send_time, tr.report_text, tr.report_status, tr.task_name,
                       STRING_AGG(fa.file_id || ':' || fa.file_type, ',') AS file_details
                FROM task_reports AS tr
                LEFT JOIN file_attachments AS fa ON tr.id = fa.report_id AND fa.task_type = 'task_report'
                WHERE tr.report_status = %s AND (fa.report_id IS NULL OR fa.task_type = 'task_report')
                GROUP BY tr.id
            '''

        cursor.execute(query, (status,))
        rows = cursor.fetchall()

        reports = []
        for row in rows:
            report_id, user_id, task_id, send_time, report_text, report_status, task_name, file_details = row

            if file_details:
                file_details_list = file_details.split(",")
                files_list = [File(file_id, file_type) for file_id, file_type in
                              (file.split(":") for file in file_details_list)]
                report = Report(report_id, user_id, task_id, send_time, report_text, report_status, task_name,
                                files_list)
            else:
                report = Report(report_id, user_id, task_id, send_time, report_text, report_status, task_name, None)

            reports.append(report)

        return reports if reports else None

    finally:
        cursor.close()
        db_conn.close()


def db_daily_report_insert(user_id: int, report_name: str, report_desc: str, time_sent: str) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    try:
        conn = db_conn
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO daily_reports (user_id, report_name, report_desc, time_sent) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT DO NOTHING",
            (user_id, report_name, report_desc, time_sent)
        )
        conn.commit()

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        cursor.close()


def db_get_task_name(task_id: int) -> str:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    with db_conn.cursor() as cursor:
        cursor.execute("SELECT task_name FROM user_tasks WHERE id = %s", (task_id,))
        task_name = cursor.fetchone()
        if task_name:
            return task_name[0]
        else:
            return None


def db_dismiss_update(task_id: int, note: str) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    with db_conn.cursor() as cursor:
        cursor.execute("""
            UPDATE user_tasks 
            SET task_description = task_description || %s 
            WHERE id = %s
        """, (note, task_id))
        db_conn.commit()


def db_task_deadline_update(task_id: int, task_deadline: str) -> None:
    db_conn = psycopg2.connect(DB_URI, sslmode="require")
    with db_conn.cursor() as cursor:
        cursor.execute("""
            UPDATE user_tasks 
            SET task_deadline = %s 
            WHERE id = %s
        """, (task_deadline, task_id))
        db_conn.commit()
