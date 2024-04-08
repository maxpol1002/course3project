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
        await update.message.reply_text(f"Hello, {user_name}, your status is: {user_status}", reply_markup=admin_menu_markup)

    else:
        await update.message.reply_text(f"Hello unknown user, {user.first_name} {user.last_name}, "
                                        f"your status is: {user_status}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_user = update.effective_user
    user_status = get_user_status(current_user.id)
    user_input = update.message.text
    users_list = []
    users = []
    if user_input == "👤 Send direct message" and user_status == 1:
        users_list = db_get_all_users()
        print(users_list[0].username)
    n = 1
    for user in users_list:
        users.append([InlineKeyboardButton(f"{n}. {user.user_name} {user.user_surname}, username: {user.username}",
                                           callback_data=f'user {user.user_surname}')])
        n += 1
    reply_user_list_markup = InlineKeyboardMarkup(users)
    await update.message.reply_text(f"List of all users:", reply_markup=reply_user_list_markup)


async def send_group_msg_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Selected option: {query.data}")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(send_group_msg_button))
    application.add_handler(MessageHandler(~filters.COMMAND, message_handler))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
