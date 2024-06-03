from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler
)

from db import (
    db_user_tasks_table_insert,
    db_get_all_users,
    db_get_all_tasks,
    db_get_tasks_for_user,
    db_get_user_data,
    db_task_status_update,
    db_report_table_insert,
    db_files_table_insert,
    db_get_report_id,
    db_get_reports,
    db_daily_report_insert,
    db_get_daily_rep_id,
    db_get_daily_reports,
    db_get_task_name,
    db_get_task_id
)

from print_methods import (
    print_reports,
    print_tasks,
    print_daily_reports,
    send_media
)

from inline_keyboards import (
    build_inline_calendar,
    build_inline_keyboard
)

from utility_methods import (
    get_user_status,
    get_current_datetime_str
)

from config import (
    TASK_DATA,
    DAILY_REPORT
)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_user = update.effective_user
    user_status = get_user_status(current_user.id)
    user_input = update.message.text
    admin_menu = [
        ["📋 View current tasks", "🔢 Sort tasks", "🛠 Manage tasks"],
        ["📊 View reports", "🗓 View daily reports"]
    ]
    admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
    if user_status == 1:
        match user_input:
            case "👥 Create task":
                context.user_data.clear()
                selected_users = context.user_data.get("selected_users", [])
                await update.message.reply_text("List of all users:",
                                                reply_markup=build_inline_keyboard(db_get_all_users(), selected_users))

            case "📋 View current tasks":
                active_tasks = db_get_all_tasks()
                if active_tasks:
                    await update.message.reply_text("Active tasks:", reply_markup=admin_menu_markup)
                    await print_tasks(update, context, active_tasks)
                else:
                    await update.message.reply_text("There are no tasks assigned at this moment.",
                                                    reply_markup=admin_menu_markup)

            case "📊 View reports":
                admin_menu = [
                    ["📋 View current tasks", "⏳ Pending reports"],
                    ["✔️ Approved reports", "🚫 Dismissed reports"]
                ]
                admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
                await update.message.reply_text("Click button below to check pending or approved reports.",
                                                reply_markup=admin_menu_markup)

            case "⏳ Pending reports":
                pending_reports = db_get_reports(status="pending")
                if pending_reports:
                    await update.message.reply_text("Pending reports:")
                    await print_reports(update, context, pending_reports)

                else:
                    await update.message.reply_text("There are no pending reports at this moment.")

            case "✔️ Approved reports":
                approved_reports = db_get_reports(status="approved")
                if approved_reports:
                    await update.message.reply_text("Approved reports:")
                    await print_reports(update, context, approved_reports)

                else:
                    await update.message.reply_text("There are no approved reports at this moment.")

            case "🚫 Dismissed reports":
                dismissed_reports = db_get_reports(status="dismissed")
                if dismissed_reports:
                    await update.message.reply_text("Dismissed reports:")
                    await print_reports(update, context, dismissed_reports)

                else:
                    await update.message.reply_text("There are no dismissed reports at this moment.")

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
                    ["📋 View current tasks", "✅ View completed tasks"], ["👥 Create task", "❌ Delete task"]
                ]
                admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
                await update.message.reply_text("Here you can manage all tasks.", reply_markup=admin_menu_markup)

            case "✅ View completed tasks":
                completed_tasks = db_get_all_tasks(1)
                if completed_tasks:
                    await update.message.reply_text("Completed tasks:")
                    await print_tasks(update, context, completed_tasks)
                else:
                    await update.message.reply_text("There are no completed tasks at this moment.")

            case "❌ Delete task":
                admin_menu = [
                    ["📋 View current tasks", "✅ View completed tasks"], ["👥 Create task", "❌ Delete task"]
                ]
                admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
                active_tasks = db_get_all_tasks()
                if active_tasks:
                    await update.message.reply_text("Choose which task you want to delete:",
                                                    reply_markup=admin_menu_markup)
                    for task in active_tasks:
                        if task.task_status == "pending":
                            msg = await update.message.reply_text(task.print_data())

                        else:
                            delete_task_button = [
                                [InlineKeyboardButton("Delete", callback_data=f"delete_task_{task.task_id}")]
                            ]
                            msg = await update.message.reply_text(task.print_data(),
                                                                  reply_markup=InlineKeyboardMarkup(delete_task_button))
                        await send_media(task, current_user.id, msg.id, context)

                else:
                    await update.message.reply_text("There are no tasks assigned at this moment.")

            case "🗓 View daily reports":
                admin_menu = [
                    ["📋 View current tasks", "🔢 Sort tasks", "🛠 Manage tasks"],
                    ["📊 View reports", "🗓 View daily reports"]
                ]
                admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
                daily_reports = db_get_daily_reports()
                if daily_reports:
                    await update.message.reply_text("Your daily reports:", reply_markup=admin_menu_markup)
                    await print_daily_reports(update, context, db_get_daily_reports())

                else:
                    await update.message.reply_text("There are no daily reports at this moment.",
                                                    reply_markup=admin_menu_markup)

    else:
        match user_input:
            case "📋 View active tasks":
                user_menu = [
                    ["📋 View active tasks", "📜 View completed tasks"],
                    ["🗓 Send daily report"]
                ]
                user_menu_markup = ReplyKeyboardMarkup(user_menu, resize_keyboard=True)
                active_tasks = db_get_tasks_for_user(current_user.id, "incomplete")
                if active_tasks:
                    await update.message.reply_text("My tasks:", reply_markup=user_menu_markup)
                    idx = 1
                    for task in active_tasks:
                        confirm_task_button = [[InlineKeyboardButton("Confirm",
                                                                     callback_data=f"confirm_task_{task.task_id}_{current_user.id}")]]
                        msg = await update.message.reply_text(task.print_for_user(idx),
                                                              reply_markup=InlineKeyboardMarkup(confirm_task_button))
                        await send_media(task, current_user.id, msg.id, context)
                        idx += 1

                else:
                    await update.message.reply_text("You have no active tasks at this moment.",
                                                    reply_markup=user_menu_markup)

            case "📜 View completed tasks":
                completed_tasks = db_get_tasks_for_user(current_user.id, "completed")
                if completed_tasks:
                    await update.message.reply_text("Completed tasks:")
                    idx = 1
                    for task in completed_tasks:
                        msg = await update.message.reply_text(task.print_for_user(idx))
                        await send_media(task, current_user.id, msg.id, context)
                        idx += 1

                else:
                    await update.message.reply_text("You have no completed tasks at this moment.")

            case "🗓 Send daily report":
                await update.message.reply_text("Enter report name:")
                return DAILY_REPORT


async def report_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler.END:
    if "report_text" not in context.user_data:
        context.user_data["report_text"] = update.message.text
        file_choice = [
            [InlineKeyboardButton("Yes", callback_data=f"report_add_file"),
             InlineKeyboardButton("No", callback_data=f"report_no_file")]
        ]
        markup = InlineKeyboardMarkup(file_choice)
        await update.message.reply_text("Do you want to add photos/files?", reply_markup=markup)
        return ConversationHandler.END


async def dismiss_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dismiss_text" not in context.user_data:
        context.user_data["dismiss_text"] = update.message.text

    context.user_data["year"] = datetime.now().year
    await update.message.reply_text("Choose new deadline:", reply_markup=build_inline_calendar(datetime.now().month, datetime.now().year))
    return ConversationHandler.END


async def files_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def daily_report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler.END:
    if "daily_rep_name" not in context.user_data:
        context.user_data["daily_rep_name"] = update.message.text
        await update.message.reply_text("Enter report description:")
        return DAILY_REPORT

    elif "daily_rep_desc" not in context.user_data:
        context.user_data["daily_rep_desc"] = update.message.text
        file_choice = [
            [InlineKeyboardButton("Yes", callback_data=f"daily_rep_file"),
             InlineKeyboardButton("No", callback_data=f"daily_rep_no")]
        ]
        markup = InlineKeyboardMarkup(file_choice)
        await context.bot.send_message(update.message.chat.id, "Do you want to add photos/files?", reply_markup=markup)
        return ConversationHandler.END


async def send_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler.END:
    daily_rep_name = context.user_data["daily_rep_name"]
    daily_rep_desc = context.user_data["daily_rep_desc"]
    daily_rep_photos = context.user_data["report_photos"]
    daily_rep_docs = context.user_data["report_docs"]
    daily_rep_videos = context.user_data["report_videos"]
    user_id = context.user_data["daily_user_id"]
    db_daily_report_insert(user_id, daily_rep_name, daily_rep_desc, get_current_datetime_str())

    if daily_rep_photos:
        for photo in daily_rep_photos:
            db_files_table_insert(db_get_daily_rep_id(user_id, daily_rep_desc), photo, "photo", "daily_report")

    if daily_rep_docs:
        for document in daily_rep_docs:
            db_files_table_insert(db_get_daily_rep_id(user_id, daily_rep_desc), document, "document", "daily_report")

    if daily_rep_videos:
        for video in daily_rep_videos:
            db_files_table_insert(db_get_daily_rep_id(user_id, daily_rep_desc), video, "video", "daily_report")

    user_menu = [
        ["📋 View active tasks", "📜 View completed tasks"],
        ["🗓 Send daily report"]
    ]
    markup = ReplyKeyboardMarkup(user_menu, resize_keyboard=True)
    await context.bot.send_message(user_id, "Daily report sent.", reply_markup=markup)
    await context.bot.send_message(648380859, f"You have new daily report from {db_get_user_data(user_id)}.")
    context.user_data.clear()
    return ConversationHandler.END


async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler.END:
    report_text = context.user_data["report_text"]
    report_photos = context.user_data["report_photos"]
    report_docs = context.user_data["report_docs"]
    report_videos = context.user_data["report_videos"]
    task_id = context.user_data["report_task_id"]
    user_id = context.user_data["report_user_id"]
    db_report_table_insert(user_id, task_id, get_current_datetime_str(), report_text, "pending", db_get_task_name(task_id))
    db_task_status_update(task_id, "pending")
    user_menu = [
        ["📋 View active tasks", "📜 View completed tasks"],
        ["🗓 Send daily report"]
    ]
    await context.bot.send_message(648380859,
                                   f"You have new report for task: {db_get_task_name(task_id)} from {db_get_user_data(user_id)}\n"
                                   f"Report text: {report_text}")
    if report_photos:
        for photo in report_photos:
            db_files_table_insert(db_get_report_id(user_id, task_id), photo, "photo", "task_report")

    if report_docs:
        for document in report_docs:
            db_files_table_insert(db_get_report_id(user_id, task_id), document, "document", "task_report")

    if report_videos:
        for video in report_videos:
            db_files_table_insert(db_get_report_id(user_id, task_id), video, "video", "task_report")

    await context.bot.send_message(user_id, "Report has been sent.",
                                   reply_markup=ReplyKeyboardMarkup(user_menu, resize_keyboard=True))

    context.user_data.clear()
    return ConversationHandler.END


async def send_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler.END:
    task_name = context.user_data["task_name"]
    task_description = context.user_data["task_description"]
    importance_level = context.user_data["task_importance"]
    task_setting_time = get_current_datetime_str()
    task_deadline = context.user_data["task_deadline"]
    selected_users_list = context.user_data["selected_users"]
    task_photos = context.user_data["report_photos"]
    task_docs = context.user_data["report_docs"]
    task_videos = context.user_data["report_videos"]
    task_status = "incomplete"
    db_user_tasks_table_insert(task_name, task_description, importance_level, task_setting_time, task_deadline,
                               selected_users_list[0], task_status)

    if task_photos:
        for photo in task_photos:
            db_files_table_insert(db_get_task_id(task_setting_time, task_name, task_description), photo, "photo", "task")

    if task_docs:
        for document in task_docs:
            db_files_table_insert(db_get_task_id(task_setting_time, task_name, task_description), document, "document", "task")

    if task_videos:
        for video in task_videos:
            db_files_table_insert(db_get_task_id(task_setting_time, task_name, task_description), video, "video", "task")

    admin_menu = [
        ["📋 View current tasks", "🔢 Sort tasks", "🛠 Manage tasks"],
        ["📊 View reports", "🗓 View daily reports"]
    ]
    admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)

    await context.bot.send_message(648380859, "Task created successfully!", reply_markup=admin_menu_markup)
    for user_id in selected_users_list:
        await context.bot.send_message(user_id, "Hello, you have a new task!")

    context.user_data.clear()
    return ConversationHandler.END


async def task_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler.END:
    if "task_name" not in context.user_data:
        context.user_data["task_name"] = update.message.text
        await context.bot.send_message(update.effective_user.id, "Input task description:")
        return TASK_DATA

    elif "task_description" not in context.user_data:
        context.user_data["task_description"] = update.message.text
        await context.bot.send_message(update.effective_user.id,
                                       "Input task importance (1-5, where 5 is super-important):")
        return TASK_DATA

    elif "task_importance" not in context.user_data:
        importance_input = update.message.text.strip()
        if not importance_input.isdigit() or not (1 <= int(importance_input) <= 5):
            await context.bot.send_message(update.effective_user.id,
                                           "Invalid input. Importance level must be a valid integer between 1 and 5.")
            await context.bot.send_message(update.effective_user.id, "Input task importance (1-5):")
            return TASK_DATA

        importance_level = int(importance_input)
        context.user_data["task_importance"] = importance_level
        await context.bot.send_message(update.effective_user.id, "Select task deadline:",
                                       reply_markup=build_inline_calendar(datetime.now().month, datetime.now().year))
        context.user_data["year"] = datetime.now().year

        return ConversationHandler.END
