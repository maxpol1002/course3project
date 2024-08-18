from datetime import datetime

from telegram.ext import ContextTypes

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

import config
from inline_keyboards import build_inline_keyboard, build_inline_calendar

from config import (
    TASK_DATA,
    REPORT_DATA,
    REPORT_FILES,
    DAILY_REPORT_FILES,
    TASK_FILES,
    DISMISS_REP
)

from db import (
    db_user_tasks_table_insert,
    db_get_all_users,
    db_get_all_tasks,
    db_get_user_data,
    db_task_status_update,
    db_report_table_insert,
    db_daily_report_insert,
    db_get_task_name,
    db_delete_file,
    db_delete_task,
    db_report_status_update,
    db_dismiss_update,
    db_task_deadline_update,
    db_delete_report,
    db_delete_daily_rep
)

from print_methods import send_media

from utility_methods import get_current_datetime_str


async def callback_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("do_nothing"):
        await query.answer()

    elif query.data.startswith("select_user"):
        selected_user_id = int(query.data.split("_")[2])
        selected_users = context.user_data.get("selected_users", [])
        if not selected_users:
            selected_users.append(selected_user_id)
        else:
            if selected_user_id == selected_users[0]:
                selected_users.clear()
            else:
                selected_users.clear()
                selected_users.append(selected_user_id)

        context.user_data["selected_users"] = selected_users
        await query.edit_message_reply_markup(reply_markup=build_inline_keyboard(db_get_all_users(), selected_users))
        await query.answer()

    elif query.data.startswith("send_selected"):
        await update.effective_message.delete()
        await context.bot.send_message(query.message.chat.id, "Введіть назву завдання:")
        await query.answer()
        return TASK_DATA

    elif query.data.startswith("sort.tasks"):
        sort_value = str(query.data.split(".")[2])
        sort_type = {
            "importance_level": "Cтупінь важливості",
            "task_setting_time": "Дата встановлення завдання",
            "task_deadline": "Дедлайн завдання"
        }

        sorted_tasks = sorted(db_get_all_tasks(), key=lambda x: getattr(x, sort_value))
        await context.bot.send_message(query.message.chat.id,
                                       f"==================================\nВідсортовано за: {sort_type[sort_value]}\n"
                                       f"==================================")
        for task in sorted_tasks:
            msg = await context.bot.send_message(query.message.chat.id, task.print_data())
            await send_media(task, query.message.chat.id, msg.id, context)
        await query.answer()

    elif query.data.startswith("delete_task"):
        task_id = int(query.data.split("_")[2])
        db_delete_task(task_id)
        db_delete_file(task_id, "task")
        await update.effective_message.delete()
        await context.bot.send_message(query.message.chat.id, f"Завдання {task_id} успішно видалено.")
        await query.answer()

    elif query.data.startswith("confirm_task"):
        task_id = int(query.data.split("_")[2])
        user_id = int(query.data.split("_")[3])
        rep_choice = [
            [InlineKeyboardButton("Так", callback_data=f"send_report_{task_id}_{user_id}"),
             InlineKeyboardButton("Ні", callback_data=f"no_report_{task_id}_{user_id}")]
        ]
        rep_choice_markup = InlineKeyboardMarkup(rep_choice)
        await update.effective_message.delete()
        await context.bot.send_message(query.message.chat.id,
                                       f"Завдання: {db_get_task_name(task_id)} позначено як виконане, чи бажаєте ви додати звіт?",
                                       reply_markup=rep_choice_markup)
        await query.answer()

    elif query.data.startswith("send_report"):
        await update.effective_message.delete()
        task_id = int(query.data.split("_")[2])
        user_id = int(query.data.split("_")[3])
        context.user_data["report_task_id"] = task_id
        context.user_data["report_user_id"] = user_id
        await context.bot.send_message(query.message.chat.id, f"Додайте опис до звіту.")
        await query.answer()
        return REPORT_DATA

    elif query.data.startswith("no_report"):
        await update.effective_message.delete()
        task_id = int(query.data.split("_")[2])
        user_id = int(query.data.split("_")[3])
        db_report_table_insert(user_id, task_id, get_current_datetime_str(), "No description", "pending", db_get_task_name(task_id))
        db_task_status_update(task_id, "pending")
        await context.bot.send_message(query.message.chat.id, f"Ваш звіт було надіслано. Очікуйте на перевірку.")
        await context.bot.send_message(config.ADMIN_ID,
                                       f"{db_get_user_data(user_id)} виконав завдання: {db_get_task_name(task_id)}")
        await query.answer()

    elif query.data == "report_add_file":
        await update.effective_message.delete()
        user_menu = [
            ["👌 Надіслати"]
        ]
        markup = ReplyKeyboardMarkup(user_menu, resize_keyboard=True)
        await context.bot.send_message(query.message.chat.id, "Надішліть фото чи файл.", reply_markup=markup)
        await query.answer()
        return REPORT_FILES

    elif query.data == "report_no_file":
        await update.effective_message.delete()
        await context.bot.send_message(query.message.chat.id, "Ваш звіт було надіслано. Очікуйте на перевірку.")
        report_text = context.user_data["report_text"]
        task_id = context.user_data["report_task_id"]
        user_id = context.user_data["report_user_id"]
        db_report_table_insert(user_id, task_id, get_current_datetime_str(), report_text, "pending", db_get_task_name(task_id))
        db_task_status_update(task_id, "pending")
        await context.bot.send_message(config.ADMIN_ID, f"{db_get_user_data(user_id)} виконав завдання: {db_get_task_name(task_id)}\n"
                                                  f"Текст звіту: {report_text}")
        context.user_data.clear()
        await query.answer()

    elif query.data.startswith("approve_report"):
        report_id = int(query.data.split("_")[2])
        task_id = int(query.data.split("_")[3])
        user_id = int(query.data.split("_")[4])
        db_task_status_update(task_id, "completed")
        db_report_status_update(report_id, "approved")
        await update.effective_message.delete()
        await context.bot.send_message(query.message.chat.id, f"Звіт №{report_id} затверджено.")
        await context.bot.send_message(user_id,
                                       f"Ваш звіт до завдання {db_get_task_name(task_id)} було затверджено.")
        await query.answer()

    elif query.data.startswith("month"):
        year = context.user_data["year"]
        month_index = int(query.data.split("_")[1])
        if month_index > 12:
            year += 1
            month_index = 1

        elif month_index < 1:
            year -= 1
            month_index = 12

        if year < datetime.now().year or (year == datetime.now().year and month_index < datetime.now().month):
            context.user_data["year"] = datetime.now().year
            await query.edit_message_reply_markup(build_inline_calendar(datetime.now().month, datetime.now().year))

        else:
            context.user_data["year"] = year
            await query.edit_message_reply_markup(build_inline_calendar(month_index, year))

        await query.answer()

    elif query.data.startswith("cal"):
        day = query.data.split("_")[1]
        month = query.data.split("_")[2]
        year = query.data.split("_")[3]
        context.user_data["task_deadline"] = f"{day}-{month}-{year}"
        if "dismiss_text" not in context.user_data:
            await context.bot.send_message(query.message.chat.id, f"Обраний дедлайн: {day}-{month}-{year}")
            file_choice = [
                [InlineKeyboardButton("Так", callback_data=f"task_add_file"),
                 InlineKeyboardButton("Ні", callback_data=f"task_no_file")]
            ]
            markup = InlineKeyboardMarkup(file_choice)
            await update.effective_message.delete()
            await context.bot.send_message(query.message.chat.id, "Чи бажаєте ви додати фото або файли?", reply_markup=markup)
            await query.answer()

        else:
            report_id = context.user_data["dismiss_rep_id"]
            task_id = context.user_data["dismiss_rep_tid"]
            user_id = context.user_data["dismiss_rep_uid"]
            note = context.user_data["dismiss_text"]
            dismiss_text = "\n++++++++++++++++++++++++++++++++++\nДодаток: "
            dismiss_text += note
            dismiss_text += "\n++++++++++++++++++++++++++++++++++"
            await update.effective_message.delete()
            db_dismiss_update(task_id, dismiss_text)
            db_task_status_update(task_id, "incomplete")
            db_report_status_update(report_id, "dismissed")
            db_task_deadline_update(task_id, f"{day}-{month}-{year}")
            await context.bot.send_message(config.ADMIN_ID, f"Звіт №{report_id} було відхилено.")
            await context.bot.send_message(user_id,
                                           f"Ваш звіт до завдання {db_get_task_name(task_id)} було відхилено. Переробіть завдання.\n"
                                           f"Додаток: {note}")
            context.user_data.clear()

    elif query.data == "task_add_file":
        await update.effective_message.delete()
        menu = [
            ["Надіслати завдання"]
        ]
        markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)
        await context.bot.send_message(query.message.chat.id, "Надішліть фото чи файл.", reply_markup=markup)
        await query.answer()
        return TASK_FILES

    elif query.data == "task_no_file":
        await update.effective_message.delete()
        task_name = context.user_data["task_name"]
        task_description = context.user_data["task_description"]
        importance_level = context.user_data["task_importance"]
        task_setting_time = get_current_datetime_str()
        task_deadline = context.user_data["task_deadline"]
        selected_users_list = context.user_data["selected_users"]
        selected_user = selected_users_list[0]
        task_status = "incomplete"

        db_user_tasks_table_insert(task_name, task_description, importance_level, task_setting_time, task_deadline,
                                   selected_user, task_status)
        await context.bot.send_message(query.message.chat.id, "Завдання успішно створено!")
        for user_id in selected_users_list:
            await context.bot.send_message(user_id, "Вітаю, у вас нове завдання!")

        context.user_data.clear()
        await query.answer()

    elif query.data == "daily_rep_file":
        await update.effective_message.delete()
        context.user_data["daily_user_id"] = query.from_user.id
        user_menu = [
            ["📩 Надіслати щоденний звіт"]
        ]
        markup = ReplyKeyboardMarkup(user_menu, resize_keyboard=True)
        await context.bot.send_message(query.message.chat.id, "Okay, send your photo/file.", reply_markup=markup)
        await query.answer()
        return DAILY_REPORT_FILES

    elif query.data == "daily_rep_no":
        await update.effective_message.delete()
        daily_rep_name = context.user_data["daily_rep_name"]
        daily_rep_desc = context.user_data["daily_rep_desc"]
        db_daily_report_insert(query.from_user.id, daily_rep_name, daily_rep_desc, get_current_datetime_str())
        await context.bot.send_message(config.ADMIN_ID, f"У вас новий щоденний звіт від {db_get_user_data(query.from_user.id)}.")
        await context.bot.send_message(query.message.chat.id, "Щоденний звіт успішно надіслано.")
        context.user_data.clear()
        await query.answer()

    elif query.data.startswith("dismiss_report"):
        context.user_data["dismiss_rep_id"] = int(query.data.split("_")[2])
        context.user_data["dismiss_rep_tid"] = int(query.data.split("_")[3])
        context.user_data["dismiss_rep_uid"] = int(query.data.split("_")[4])
        await update.effective_message.delete()
        await context.bot.send_message(query.message.chat.id, "Поясніть причину відхилення звіту та дайте нові інструкції:")
        await query.answer()
        return DISMISS_REP

    elif query.data.startswith("delete_daily"):
        report_id = int(query.data.split("_")[2])
        db_delete_daily_rep(report_id)
        db_delete_file(report_id, "daily_report")
        await update.effective_message.delete()
        await query.answer()

    elif query.data.startswith("delete_report"):
        report_id = int(query.data.split("_")[2])
        db_delete_report(report_id)
        db_delete_file(report_id, "task_report")
        await update.effective_message.delete()
        await query.answer()