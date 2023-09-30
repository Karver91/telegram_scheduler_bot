import re
import datetime


async def check_add_service_name(message):
    """Проверяет, чтобы название сервиса состояло из букв, возможны пробелы"""
    if message.text:
        return bool(re.match(r'^[а-яА-Яa-zA-Z\s]*[а-яА-Яa-zA-Z]+$', message.text))


async def check_date(callback):
    """Проверяет, что клиент записывается на актуальную дату"""
    date = list(map(int, callback.data.split(':')[1:]))
    return datetime.date.today() > datetime.date(year=date[0], month=date[1], day=date[2])
