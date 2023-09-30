import datetime

from db.db import database


async def check_time_available(date: str, time: str) -> bool:
    """Проверяет не занято ли текущее время"""
    t = datetime.datetime.strptime(time, '%H:%M:%S')
    td = datetime.timedelta(hours=t.hour, minutes=t.minute)
    result = await database.get_record_by_date_and_time(date=date, time=td)
    return not bool(result)


async def get_appointment(user_id: int) -> str:
    """Возвращает запись клиента по его id"""
    records_list = await database.get_record_by_user_id(user_id=user_id)
    result: list[str] = await __get_string_list(records_list)

    if result:
        result.insert(0, 'Cписок ваших процедур:\n')
    else:
        result.append('Вы еще не записались на процедуру')
    result: str = '\n'.join(result)
    return result


async def get_all_records() -> str:
    """Возвращает все текущие записи"""
    records_list: list[dict] = await database.get_all_records_from_schedule()
    result: list[str] = await __get_string_list(records_list)
    if result:
        result.insert(0, 'Все доступные записи:\n')
    else:
        result.append('Записей не найдено')

    result: str = '\n'.join(result)
    return result


async def __get_string_list(records_list) -> list:
    records_list = sorted(records_list, key=lambda x: (x['date'], x['time']))
    result = []

    for data in records_list:
        name = data['service_name']
        date = data['date']
        time = data['time']
        result.append(f"{date.day:>02}.{date.month:>02}.{date.year} в {str(time)[:-3]}:\n{name}\n")

    return result
