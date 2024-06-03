import calendar

from datetime import datetime


def get_user_status(user_id) -> int:
    if user_id == 648380859:
        return 1
    return 0


def get_current_datetime_str() -> str:
    current_datetime = datetime.now()
    formatted_datetime_str = current_datetime.strftime('%d-%m-%Y:%H:%M')

    return formatted_datetime_str


def get_days_in_month(year, month) -> int:
    return calendar.monthrange(year, month)[1]


def get_month_name(month_number) -> str:
    return calendar.month_name[month_number]
