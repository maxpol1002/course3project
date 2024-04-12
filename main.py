import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from db import db_table_insert, db_get_all_users
from config import TOKEN

logging.basicConfig(
    filename='bot.logs',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_user_status(user_id) -> int:
    if user_id == 648380859:
        return 1
    return 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_menu = [
        ["👤 Send direct message", "👥 Send msg to everyone"]
    ]
    admin_menu_markup = ReplyKeyboardMarkup(admin_menu, resize_keyboard=True)
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name
    user_surname = user.last_name
    username = user.username
    user_status = get_user_status(user.id)
    db_table_insert(user_id, user_name, user_surname, username, user_status)

    if user_status == 1:
        await update.message.reply_text(f"Hello, {user_name}, your status is: {user_status}",
                                        reply_markup=admin_menu_markup)

    else:
        await update.message.reply_text(f"Hello unknown user, {user.first_name} {user.last_name}, "
                                        f"your status is: {user_status}")


def build_inline_keyboard(users_list, selected_users=None):
    users = []
    idx = 1
    for user in users_list:
        is_selected = user.user_id in selected_users if selected_users else False
        check_mark = "❌" if is_selected else "✅"
        users.append([
            InlineKeyboardButton(f"{idx}. {user.user_name} {user.user_surname}, username: {user.username}",
                                 callback_data="do_nothing"),
            InlineKeyboardButton(check_mark, callback_data=f"select_user_{user.user_id}")
        ])
        idx += 1
    if selected_users:
        users.append([InlineKeyboardButton("Create task", callback_data="send_selected")])
    reply_user_list_markup = InlineKeyboardMarkup(users)
    return reply_user_list_markup


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_user = update.effective_user
    user_status = get_user_status(current_user.id)
    user_input = update.message.text
    if user_input == "👤 Send direct message" and user_status == 1:
        await update.message.reply_text(f"List of all users:", reply_markup=build_inline_keyboard(db_get_all_users()))


async def send_group_msg_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data.startswith("select_user"):
        selected_user_id = int(query.data.split("_")[2])
        selected_users = context.user_data.get("selected_users", [])
        if selected_user_id in selected_users:
            selected_users.remove(selected_user_id)
        else:
            selected_users.append(selected_user_id)
        context.user_data["selected_users"] = selected_users
        await query.edit_message_reply_markup(reply_markup=build_inline_keyboard(db_get_all_users(), selected_users))

    elif query.data.startswith("send_selected"):
        selected_users = context.user_data["selected_users"]
        for user_id in selected_users:
            await context.bot.send_message(user_id, "hello task1")

        context.user_data["selected_users"] = []


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(send_group_msg_button))
    application.add_handler(MessageHandler(~filters.COMMAND, message_handler))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
