import sqlite3
from User import User


def db_table_insert(user_id: int, user_name: str, user_surname: str, username: str, user_status: int):
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO user_data (user_id, user_name, user_surname, username, user_status) '
                   'VALUES (?, ?, ?, ?, ?)', (user_id, user_name, user_surname, username, user_status))
    conn.commit()


def db_get_all_users():
    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, user_name, user_surname, username FROM user_data WHERE user_status = 0")
    rows = cursor.fetchall()
    users = []
    if rows:
        for row in rows:
            user_id, user_name, user_surname, username = row
            user = User(user_id, user_name, user_surname, username)
            users.append(user)

    return users
