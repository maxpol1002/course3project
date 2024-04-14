import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, \
    filters, ConversationHandler
from db import db_user_data_table_insert, db_get_all_users, db_user_tasks_table_insert, db_get_all_tasks
from config import TOKEN
from datetime import datetime

logging.basicConfig(
    filename='bot.logs',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TASK_DATA = 0


def get_user_status(user_id) -> int:
    if user_id == 648380859:
        return 1
    return 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_menu = [
        ["👥 Create task", "📋 View current tasks"]
    ]
    admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
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

    else:
        await update.message.reply_text(f"Hello unknown user, {user.first_name} {user.last_name}, "
                                        f"your status is: {user_status}")


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


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_user = update.effective_user
    user_status = get_user_status(current_user.id)
    user_input = update.message.text
    if user_status == 1:
        match user_input:
            case "👥 Create task":
                await update.message.reply_text("List of all users:", reply_markup=build_inline_keyboard(db_get_all_users()))

            case "📋 View current tasks":
                active_tasks = db_get_all_tasks()
                if active_tasks:
                    await update.message.reply_text("Active tasks:")
                    for task in active_tasks:
                        await update.message.reply_text(f"Task {task.task_id}: {task.task_name}\n"
                                                        f"Description: {task.task_description}\n"
                                                        f"Importance level: {task.importance_level}\n"
                                                        f"Date of issue: {task.task_setting_time}\n"
                                                        f"Deadline: {task.task_deadline}\n"
                                                        f"Assigned for: {task.assigned_users}")
                else:
                    await update.message.reply_text("There are no tasks assigned at this moment.")


async def task_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'task_name' not in context.user_data:
        context.user_data["task_name"] = update.message.text
        await context.bot.send_message(update.effective_user.id, "Input task description:")
        return TASK_DATA

    elif 'task_description' not in context.user_data:
        context.user_data["task_description"] = update.message.text
        await context.bot.send_message(update.effective_user.id, "Input task importance (1-5, where 5 is super-important):")
        return TASK_DATA

    elif 'task_importance' not in context.user_data:
        context.user_data["task_importance"] = update.message.text
        await context.bot.send_message(update.effective_user.id, "Input task deadline (YYYY-MM-DD):")
        return TASK_DATA

    elif 'task_deadline' not in context.user_data:
        context.user_data["task_deadline"] = update.message.text
        task_name = context.user_data["task_name"]
        task_description = context.user_data["task_description"]
        importance_level = context.user_data["task_importance"]
        task_setting_time = datetime.now().strftime('%Y-%m-%d')
        task_deadline = context.user_data["task_deadline"]
        selected_users_list = context.user_data["selected_users"]
        selected_users = ','.join(map(str, selected_users_list))

    db_user_tasks_table_insert(task_name, task_description, importance_level, task_setting_time, task_deadline, selected_users)
    await update.message.reply_text("Task created successfully!")
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
        await context.bot.send_message(648380859, "Input task name:")
        await query.answer()
        return TASK_DATA


if __name__ == '__main__':
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(callback_data_handler)],
        states={
            TASK_DATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, task_data_handler)
            ],
        },
        fallbacks=[],
        per_message=True
    )
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(callback_data_handler))
    application.add_handler(MessageHandler(~filters.COMMAND, message_handler))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
