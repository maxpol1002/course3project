import calendar
import pytz
from datetime import datetime

import config


def get_user_status(user_id) -> int:
    if user_id == config.ADMIN_ID:
        return 1
    return 0


def get_current_datetime_str() -> str:
    kyiv_tz = pytz.timezone('Europe/Kyiv')
    current_datetime = datetime.now(kyiv_tz)
    formatted_datetime_str = current_datetime.strftime('%d-%m-%Y:%H:%M')

    return formatted_datetime_str


def get_days_in_month(year, month) -> int:
    return calendar.monthrange(year, month)[1]


def get_month_name(month_number) -> str:
    months = {
        1: "Січень",
        2: "Лютий",
        3: "Березень",
        4: "Квітень",
        5: "Травень",
        6: "Червень",
        7: "Липень",
        8: "Серпень",
        9: "Вересень",
        10: "Жовтень",
        11: "Листопад",
        12: "Грудень"
    }

    return months[month_number]
