import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from utility_methods import (
    get_month_name,
    get_days_in_month
)


def build_inline_calendar(current_month, current_year) -> InlineKeyboardMarkup:
    cal = []
    month_name = get_month_name(current_month)
    if current_month == datetime.datetime.now().month:
        first_day = datetime.datetime.now().day
    else:
        first_day = 1
    cal.append([InlineKeyboardButton(f"{current_year}", callback_data="do_nothing")])
    cal.append([InlineKeyboardButton(f"{month_name}", callback_data="do_nothing")])
    month = []
    for i in range(first_day, get_days_in_month(current_year, current_month) + 1):
        cb_day = f"0{i}" if i < 10 else f"{i}"
        cb_month = f"0{current_month}" if current_month < 10 else f"{current_month}"
        month.append(InlineKeyboardButton(f"{i}", callback_data=f"cal_{cb_day}_{cb_month}_{current_year}"))
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
        check_mark = "✅" if is_selected else "❌"
        users.append([
            InlineKeyboardButton(f"{idx}. {user.user_name} {user.user_surname}",
                                 callback_data="do_nothing"),
            InlineKeyboardButton(check_mark, callback_data=f"select_user_{user.user_id}")
        ])
        idx += 1
    if selected_users:
        users.append([InlineKeyboardButton("Create task", callback_data="send_selected")])

    return InlineKeyboardMarkup(users)
