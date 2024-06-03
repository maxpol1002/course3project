from pytz import timezone

from datetime import time

from telegram import (
    Update,
    ReplyKeyboardMarkup
)

from telegram.ext import ContextTypes

from db import (
    db_get_all_tasks,
    db_user_data_table_insert
)
from utility_methods import (
    get_current_datetime_str,
    get_user_status
)


async def task_notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    incomplete_tasks = db_get_all_tasks(2)
    current_date = get_current_datetime_str().split(':')[0]
    if incomplete_tasks:
        for task in incomplete_tasks:
            if task.task_deadline == current_date:
                await context.bot.send_message(task.assigned_user_id, f"Hey, you must complete task <{task.task_name}> today.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_menu = [
        ["📋 View current tasks"]
    ]
    user_menu = [
        ["📋 View active tasks"]
    ]
    admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
    user_menu_markup = ReplyKeyboardMarkup(user_menu, resize_keyboard=True)
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name
    user_surname = user.last_name
    username = user.username
    user_status = get_user_status(user.id)
    db_user_data_table_insert(user_id, user_name, user_surname, username, user_status)

    if user_status == 1:
        await update.message.reply_text(f"Hello, {user_name}, you can use me as a service to communicate with "
                                        f"your employees. With me, you can set tasks for your employees, receive and "
                                        f"manage reports and lots of other cool things! ",
                                        reply_markup=admin_menu_markup)

        t = time(9, 0, tzinfo=timezone('Europe/Kyiv'))
        context.job_queue.run_daily(task_notification, t)

    else:
        await update.message.reply_text(f"Hello, {user.first_name} {user.last_name}, "
                                        f"what a great day to work, isn't it?", reply_markup=user_menu_markup)


async def readme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    user_status = get_user_status(user_id)
    admin_markup = ReplyKeyboardMarkup([["📋 View current tasks"]], resize_keyboard=True)
    if user_status == 1:
        await update.message.reply_text("Use me via text buttons that appear automatically. "
                                        "Just click on them and let me do all the work =)", reply_markup=admin_markup)
    else:
        await update.message.reply_text("You can receive tasks here, send reports and daily reports. "
                                        "Just click on buttons and see the magic yourself.")
