import calendar
import time
import datetime
from zoneinfo import ZoneInfo

from config_data.config import WEEKEND, MONTH_LIMIT
from db.db import database

async def get_date(date_id: int) -> tuple:
    """Принимает id даты для страницы календаря
    Возвращает дату в соотвествии с id"""
    date = datetime.date.today()
    year, month, day  = date.year, date.month, date.day
    for i in range(date_id):
        month += 1
        if month > 12:
            month = 1
            year += 1

    return (year, month, day)


async def get_working_days_for_month(date_id: int, date: tuple, months_limith: int = MONTH_LIMIT):
    """Проверяет рабочие дни месяца"""
    month_calendar = calendar.monthcalendar(year=date[0], month=date[1])
    today = date[2]
    for week in month_calendar:
        for indx in range(7):
            __check_weekend(week, indx)
            if date_id == 0:
                __less_than(week, indx, today)
            elif date_id == months_limith:
                __greater_than(week, indx, today)
    return month_calendar


def __check_weekend(week, indx):
    if indx in WEEKEND:
        week[indx] = 0


def __greater_than(week, indx, today):
    if week[indx] > today:
        week[indx] = 0


def __less_than(week, indx, today):
    if week[indx] < today:
        week[indx] = 0


async def get_free_time_on_date(date: str, service_name: str) -> list[datetime.timedelta]:
    """Получает свободное время для записи на переданную дату"""
    working_hours_list: list[dict] = await database.get_working_hours()
    working_hours_list: list = await __convert_dict_to_list(working_hours_list)
    occupied_time_list: list[dict] = await database.get_time_and_duration_for_date_from_schedule(date)
    occupied_time_list: list[dict] = sorted(occupied_time_list, key=lambda x: x['time'])
    service_description: dict = await database.get_service_description_from_db(service_name)
    user_service_duration: int = service_description['duration']
    working_hours_list_copy: list = working_hours_list[:]
    index = 0

    for service_time in occupied_time_list:
        # Вычисляю время окончания услуги: время ее начала + ее длительность
        service_end_time = service_time['time'] + datetime.timedelta(minutes=service_time['duration'])
        service_time = service_time['time']

        for working_time in working_hours_list[index:]:
            # Вычисляю время окончания процедуры, на которую записывается клиент, от текщего времени
            user_service_end_time = working_time + datetime.timedelta(minutes=user_service_duration)

            if working_time < service_end_time <= user_service_end_time or \
                    service_time < user_service_end_time <= service_end_time:
                working_hours_list_copy.remove(working_time)

            if working_time >= service_end_time:
                index = working_hours_list.index(working_time)
                break

    return working_hours_list_copy

async def __convert_dict_to_list(time_list: list[dict]) -> list[datetime.timedelta]:
    """Конвентирует список словарей в список"""
    result: list = []
    for time in time_list:
        result.append(time['time'])
    return result
