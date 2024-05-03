import calendar
import logging

from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    InputMediaPhoto,
    InputMediaDocument,
    InputMediaVideo
)

from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

from db import (
    db_user_data_table_insert,
    db_user_tasks_table_insert,
    db_get_all_users,
    db_get_all_tasks,
    db_get_tasks_for_user,
    db_delete_task,
    db_get_user_data,
    db_task_status_update,
    db_report_table_insert,
    db_files_table_insert,
    db_get_report_id,
    db_get_reports,
    db_report_status_update
)

from config import TOKEN

logging.basicConfig(
    filename='bot.logs',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TASK_DATA = 0
REPORT_DATA = 1
REPORT_FILES = 2


def get_user_status(user_id) -> int:
    if user_id == 648380859:
        return 1
    return 0


def get_current_datetime_str():
    current_datetime = datetime.now()
    formatted_datetime_str = current_datetime.strftime('%d-%m-%Y:%H:%M')

    return formatted_datetime_str


def get_days_in_month(year, month):
    return calendar.monthrange(year, month)[1]


def get_month_name(month_number):
    return calendar.month_name[month_number]


def build_inline_calendar(current_month, current_year) -> InlineKeyboardMarkup:
    cal = []
    month_name = get_month_name(current_month)
    days_in_month = get_days_in_month(current_year, current_month)
    cal.append([InlineKeyboardButton(f"{current_year}", callback_data="do_nothing")])
    cal.append([InlineKeyboardButton(f"{month_name}", callback_data="do_nothing")])
    month = []
    for i in range(days_in_month):
        month.append(InlineKeyboardButton(f"{i + 1}", callback_data=f"cal_{month_name}_{i + 1}"))
        if len(month) == 6:
            cal.append(month)
            month = []
    cal.append(month)
    cal.append([
        InlineKeyboardButton("◀️", callback_data=f"month_{current_month - 1}"),
        InlineKeyboardButton("▶️", callback_data=f"month_{current_month + 1}")
    ])

    return InlineKeyboardMarkup(cal)


def build_inline_keyboard(users_list, selected_users=None) -> InlineKeyboardMarkup:
    users = []
    idx = 1
    for user in users_list:
        is_selected = user.user_id in selected_users if selected_users else False
        check_mark = "❌" if is_selected else "✅"
        users.append([
            InlineKeyboardButton(f"{idx}. {user.user_name} {user.user_surname}",
                                 callback_data="do_nothing"),
            InlineKeyboardButton(check_mark, callback_data=f"select_user_{user.user_id}")
        ])
        idx += 1
    if selected_users:
        users.append([InlineKeyboardButton("Create task", callback_data="send_selected")])

    return InlineKeyboardMarkup(users)


async def print_reports(update: Update, context: ContextTypes.DEFAULT_TYPE, reports) -> None:
    for report in reports:
        if report.report_status == "pending":
            approve_report_button = [
                [InlineKeyboardButton("Approve", callback_data=f"approve_report_{report.report_id}_{report.task_id}")]]
            await update.message.reply_text(report.create_report_text(),
                                            reply_markup=InlineKeyboardMarkup(approve_report_button))
        else:
            await update.message.reply_text(report.create_report_text())

        if report.get_media():
            report_photos, report_videos, report_docs = report.get_media()
            if report_photos:
                if len(report_photos) == 1:
                    await context.bot.send_photo(648380859, report_photos[0], caption="Added photo ⬆️")

                else:
                    photos_list = []
                    for photo_id in report_photos:
                        photos_list.append(InputMediaPhoto(media=photo_id))
                    await context.bot.send_media_group(648380859, photos_list, caption="Added photos ⬆️")

            if report_docs:
                if len(report_docs) == 1:
                    await context.bot.send_document(648380859, report_docs[0], caption="Added document ⬆️")

                else:
                    docs_list = []
                    for doc_id in report_docs:
                        docs_list.append(InputMediaDocument(media=doc_id))
                    await context.bot.send_media_group(648380859, docs_list, caption="Added documents ⬆️")

            if report_videos:
                if len(report_videos) == 1:
                    await context.bot.send_video(648380859, report_videos[0], caption="Added video ⬆️")

                else:
                    videos_list = []
                    for vid_id in report_videos:
                        videos_list.append(InputMediaVideo(media=vid_id))
                    await context.bot.send_media_group(648380859, videos_list, caption="Added videos ⬆️")


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
        await update.message.reply_text(f"Hello, {user_name}, your status is: {user_status}",
                                        reply_markup=admin_menu_markup)

        await update.message.reply_text("Calendar:", reply_markup=build_inline_calendar(datetime.now().month, datetime.now().year))
        context.user_data["year"] = datetime.now().year

    else:
        await update.message.reply_text(f"Hello unknown user, {user.first_name} {user.last_name}, "
                                        f"your status is: {user_status}", reply_markup=user_menu_markup)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_user = update.effective_user
    user_status = get_user_status(current_user.id)
    user_input = update.message.text
    admin_menu = [
        ["📋 View current tasks", "🔢 Sort tasks", "🛠 Manage tasks"],
        ["📊 View reports"]
    ]
    admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
    if user_status == 1:
        match user_input:
            case "👥 Create task":
                selected_users = context.user_data.get("selected_users", [])
                await update.message.reply_text("List of all users:",
                                                reply_markup=build_inline_keyboard(db_get_all_users(), selected_users))

            case "📋 View current tasks":
                active_tasks = db_get_all_tasks()
                if active_tasks:
                    await update.message.reply_text("Active tasks:", reply_markup=admin_menu_markup)
                    for task in active_tasks:
                        await update.message.reply_text(task.print_data())
                else:
                    await update.message.reply_text("There are no tasks assigned at this moment.",
                                                    reply_markup=admin_menu_markup)

            case "📊 View reports":
                admin_menu = [
                    ["📋 View current tasks", "⏳ Pending reports", "✔️ Approved reports"],
                ]
                admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
                await update.message.reply_text("Click button below to check pending or approved reports.",
                                                reply_markup=admin_menu_markup)

            case "⏳ Pending reports":
                pending_reports = db_get_reports(status="pending")
                if pending_reports:
                    await print_reports(update, context, pending_reports)

                else:
                    await update.message.reply_text("There are no pending reports at this moment.")

            case "✔️ Approved reports":
                approved_reports = db_get_reports("approved")
                if approved_reports:
                    await print_reports(update, context, approved_reports)

                else:
                    await update.message.reply_text("There are no approved reports at this moment.")

            case "🔢 Sort tasks":
                if db_get_all_tasks():
                    sort_inline_keyboard = [
                        InlineKeyboardButton("Importance", callback_data="sort.tasks.importance_level"),
                        InlineKeyboardButton("Date of issue", callback_data="sort.tasks.task_setting_time"),
                        InlineKeyboardButton("Deadline", callback_data="sort.tasks.task_deadline")]
                    sort_inline_markup = InlineKeyboardMarkup([sort_inline_keyboard])

                    await update.message.reply_text("Sort tasks by:", reply_markup=sort_inline_markup)

                else:
                    await update.message.reply_text("There are no tasks assigned at this moment.")

            case "🛠 Manage tasks":
                admin_menu = [
                    ["📋 View current tasks", "👥 Create task", "✏️ Edit task", "❌ Delete task"]
                ]
                admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
                await update.message.reply_text("Here you can manage all tasks.", reply_markup=admin_menu_markup)

            case "❌ Delete task":
                admin_menu = [
                    ["📋 View current tasks", "👥 Create task", "✏️ Edit task", "❌ Delete task"]
                ]
                admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
                active_tasks = db_get_all_tasks()
                if active_tasks:
                    await update.message.reply_text("Choose which task you want to delete:",
                                                    reply_markup=admin_menu_markup)
                    for task in active_tasks:
                        delete_task_button = [
                            [InlineKeyboardButton("Delete", callback_data=f"delete_task_{task.task_id}")]]
                        await update.message.reply_text(task.print_data(),
                                                        reply_markup=InlineKeyboardMarkup(delete_task_button))
                else:
                    await update.message.reply_text("There are no tasks assigned at this moment.")

    else:
        match user_input:
            case "📋 View active tasks":
                user_menu = [
                    ["📋 View active tasks", "✅ Confirm execution", "📜 View completed tasks"]
                ]
                user_menu_markup = ReplyKeyboardMarkup(user_menu, resize_keyboard=True)
                active_tasks = db_get_tasks_for_user(str(current_user.id), "incomplete")
                if active_tasks:
                    await update.message.reply_text("My tasks:", reply_markup=user_menu_markup)
                    idx = 1
                    for task in active_tasks:
                        await update.message.reply_text(task.print_for_user(idx))
                        idx += 1

                else:
                    await update.message.reply_text("You have no active tasks at this moment.",
                                                    reply_markup=user_menu_markup)

            case "✅ Confirm execution":
                active_tasks = db_get_tasks_for_user(str(current_user.id), "incomplete")
                if active_tasks:
                    await update.message.reply_text("Choose executed task:")
                    idx = 1
                    for task in active_tasks:
                        confirm_task_button = [[InlineKeyboardButton("Confirm",
                                                                     callback_data=f"confirm_task_{task.task_id}_{current_user.id}")]]
                        await update.message.reply_text(task.print_for_user(idx),
                                                        reply_markup=InlineKeyboardMarkup(confirm_task_button))
                        idx += 1

                else:
                    await update.message.reply_text("You have no tasks at this moment.")

            case "📜 View completed tasks":
                completed_tasks = db_get_tasks_for_user(str(current_user.id), "completed")
                if completed_tasks:
                    await update.message.reply_text("Completed tasks:")
                    idx = 1
                    for task in completed_tasks:
                        await update.message.reply_text(task.print_for_user(idx))
                        idx += 1

                else:
                    await update.message.reply_text("You have no completed tasks at this moment.")


async def report_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "report_text" not in context.user_data:
        context.user_data["report_text"] = update.message.text
        file_choice = [
            [InlineKeyboardButton("Yes", callback_data=f"report_add_file"),
             InlineKeyboardButton("No", callback_data=f"report_no_file")]
        ]
        markup = InlineKeyboardMarkup(file_choice)
        await update.message.reply_text("Do you want to add photos/files?", reply_markup=markup)
        return ConversationHandler.END


async def report_files_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report_docs = context.user_data.setdefault("report_docs", [])
    report_photos = context.user_data.setdefault("report_photos", [])
    report_videos = context.user_data.setdefault("report_videos", [])
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id
        report_photos.append(photo_id)
        await update.message.reply_text("Photo received. You can add more files or proceed.")

    elif update.message.document:
        document_id = update.message.document.file_id
        report_docs.append(document_id)
        await update.message.reply_text("Document received. You can add more files or proceed.")

    elif update.message.video:
        video_id = update.message.video.file_id
        report_videos.append(video_id)
        await update.message.reply_text("Video received. You can add more files or proceed.")

    else:
        await update.message.reply_text("Wrong file type.")

    context.user_data["report_photos"] = report_photos
    context.user_data["report_docs"] = report_docs
    context.user_data["report_videos"] = report_videos


async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report_text = context.user_data["report_text"]
    report_photos = context.user_data["report_photos"]
    report_docs = context.user_data["report_docs"]
    report_videos = context.user_data["report_videos"]
    task_id = context.user_data["report_task_id"]
    user_id = context.user_data["report_user_id"]
    db_report_table_insert(user_id, task_id, get_current_datetime_str(), report_text, "pending")
    db_task_status_update(task_id, "pending")
    user_menu = [
        ["📋 View active tasks", "✅ Confirm execution"]
    ]
    await context.bot.send_message(648380859,
                                   f"You have new report for task №{task_id} from {db_get_user_data(user_id)}\n"
                                   f"Report text: {report_text}")
    if report_photos:
        for photo in report_photos:
            db_files_table_insert(db_get_report_id(user_id, task_id), photo, "photo")

    if report_docs:
        for document in report_docs:
            db_files_table_insert(db_get_report_id(user_id, task_id), document, "document")

    if report_videos:
        for video in report_videos:
            db_files_table_insert(db_get_report_id(user_id, task_id), video, "video")

    await context.bot.send_message(user_id, "Report has been sent.",
                                   reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

    context.user_data.clear()
    return ConversationHandler.END


async def task_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'task_name' not in context.user_data:
        context.user_data["task_name"] = update.message.text
        await context.bot.send_message(update.effective_user.id, "Input task description:")
        return TASK_DATA

    elif 'task_description' not in context.user_data:
        context.user_data["task_description"] = update.message.text
        await context.bot.send_message(update.effective_user.id,
                                       "Input task importance (1-5, where 5 is super-important):")
        return TASK_DATA

    elif 'task_importance' not in context.user_data:
        importance_input = update.message.text.strip()
        if not importance_input.isdigit() or not (1 <= int(importance_input) <= 5):
            await context.bot.send_message(update.effective_user.id,
                                           "Invalid input. Importance level must be a valid integer between 1 and 5.")
            await context.bot.send_message(update.effective_user.id, "Input task importance (1-5):")
            return TASK_DATA

        importance_level = int(importance_input)
        context.user_data["task_importance"] = importance_level
        await context.bot.send_message(update.effective_user.id, "Input task deadline (YYYY-DD-MM):")
        return TASK_DATA

    elif 'task_deadline' not in context.user_data:
        deadline_text = update.message.text.strip()
        try:
            task_deadline = datetime.strptime(deadline_text, '%Y-%d-%m')
        except ValueError:
            await context.bot.send_message(update.effective_user.id, "Invalid date format. Please use YYYY-MM-DD:")
            return TASK_DATA

        if task_deadline < datetime.now():
            await context.bot.send_message(update.effective_user.id,
                                           "Deadline must be in the future. Please enter again:")
            return TASK_DATA

        context.user_data["task_deadline"] = task_deadline

        task_name = context.user_data["task_name"]
        task_description = context.user_data["task_description"]
        importance_level = context.user_data["task_importance"]
        task_setting_time = get_current_datetime_str()
        task_deadline = context.user_data["task_deadline"]
        selected_users_list = context.user_data["selected_users"]
        selected_users = ','.join(map(str, selected_users_list))
        task_status = "incomplete"

        db_user_tasks_table_insert(task_name, task_description, importance_level, task_setting_time, task_deadline,
                                   selected_users, task_status)
        await update.message.reply_text("Task created successfully!")
        for user_id in selected_users_list:
            await context.bot.send_message(user_id, "Hello, you have a new task!")

        context.user_data.clear()
        return ConversationHandler.END


async def callback_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("do_nothing"):
        await query.answer()

    elif query.data.startswith("select_user"):
        selected_user_id = int(query.data.split("_")[2])
        selected_users = context.user_data.get("selected_users", [])
        if selected_user_id in selected_users:
            selected_users.remove(selected_user_id)
        else:
            selected_users.append(selected_user_id)
        context.user_data["selected_users"] = selected_users
        await query.edit_message_reply_markup(reply_markup=build_inline_keyboard(db_get_all_users(), selected_users))
        await query.answer()

    elif query.data.startswith("send_selected"):
        await context.bot.send_message(query.message.chat.id, "Input task name:")
        await query.answer()
        return TASK_DATA

    elif query.data.startswith("sort.tasks"):
        sort_value = str(query.data.split(".")[2])
        sorted_tasks = sorted(db_get_all_tasks(), key=lambda x: getattr(x, sort_value))
        await context.bot.send_message(query.message.chat.id, f"===========================================\nSorted by {sort_value}")
        for task in sorted_tasks:
            await context.bot.send_message(query.message.chat.id, task.print_data())
        await query.answer()

    elif query.data.startswith("delete_task"):
        task_id = int(query.data.split("_")[2])
        db_delete_task(task_id)
        await context.bot.send_message(query.message.chat.id, f"Task {task_id} was successfully deleted.")
        await query.answer()

    elif query.data.startswith("confirm_task"):
        task_id = int(query.data.split("_")[2])
        user_id = int(query.data.split("_")[3])
        rep_choice = [
            [InlineKeyboardButton("Yes", callback_data=f"send_report_{task_id}_{user_id}"),
             InlineKeyboardButton("No", callback_data=f"no_report_{task_id}_{user_id}")]
        ]
        rep_choice_markup = InlineKeyboardMarkup(rep_choice)
        await context.bot.send_message(query.message.chat.id,
                                       f"Task №{task_id} marked as completed, do you want to add a report?",
                                       reply_markup=rep_choice_markup)
        await query.answer()

    elif query.data.startswith("send_report"):
        task_id = int(query.data.split("_")[2])
        user_id = int(query.data.split("_")[3])
        context.user_data["report_task_id"] = task_id
        context.user_data["report_user_id"] = user_id
        await context.bot.send_message(query.message.chat.id, f"Add description to your report.")
        await query.answer()
        return REPORT_DATA

    elif query.data.startswith("no_report"):
        task_id = int(query.data.split("_")[2])
        user_id = int(query.data.split("_")[3])
        db_report_table_insert(user_id, task_id, get_current_datetime_str(), "No description", "pending")
        db_task_status_update(task_id, "pending")
        await context.bot.send_message(query.message.chat.id, f"Thanks, your task is waiting for approval.")
        await context.bot.send_message(648380859, f"{db_get_user_data(user_id)} completed task №{task_id}")
        await query.answer()

    elif query.data == "report_add_file":
        user_menu = [
            ["👌 Done"]
        ]
        markup = ReplyKeyboardMarkup(user_menu, resize_keyboard=True)
        await context.bot.send_message(query.message.chat.id, "Okay, send your photo/file.", reply_markup=markup)
        await query.answer()
        return REPORT_FILES

    elif query.data == "report_no_file":
        await context.bot.send_message(query.message.chat.id, "Your report was sent.")
        report_text = context.user_data["report_text"]
        task_id = context.user_data["report_task_id"]
        user_id = context.user_data["report_user_id"]
        db_report_table_insert(user_id, task_id, get_current_datetime_str(), report_text, "pending")
        db_task_status_update(task_id, "pending")
        await context.bot.send_message(648380859, f"{db_get_user_data(user_id)} completed task №{task_id}\n"
                                                  f"Report text: {report_text}")
        context.user_data.clear()
        await query.answer()

    elif query.data.startswith("approve_report"):
        report_id = int(query.data.split("_")[2])
        task_id = int(query.data.split("_")[3])
        db_task_status_update(task_id, "completed")
        db_report_status_update(report_id, "approved")
        await context.bot.send_message(648380859, f"Report №{report_id} is approved.")
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

        context.user_data["year"] = year
        await query.edit_message_reply_markup(build_inline_calendar(month_index, year))
        await query.answer()


if __name__ == '__main__':
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(callback_data_handler)],
        states={
            TASK_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_data_handler)],
            REPORT_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_text_handler)],
            REPORT_FILES: [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VIDEO, report_files_handler),
                           MessageHandler(filters.Regex(r'👌\s*Done'), send_report)]
        },
        fallbacks=[]
    )
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(callback_data_handler))
    application.add_handler(MessageHandler(~filters.COMMAND, message_handler))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
