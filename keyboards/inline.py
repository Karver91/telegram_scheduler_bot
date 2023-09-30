from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from lexicon.lexicon import ADMIN_LEXICON, USER_LEXICON, DAYS_OF_THE_WEEK, MONTHS
from config_data.config import MONTH_LIMIT
from db.db import database
from keyboards import keyboards_utils


class CalendarCallback(CallbackData, prefix='date_button'):
    """Фабрика коллбэков для дат календаря"""
    year: str
    month: str
    day: str


def get_start_keyboard(lexicon: dict, width: int) -> InlineKeyboardMarkup:
    """Принимает название кнопок из словаря lexicon. Возвращает клавиатуру"""
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    for callback, text in lexicon.items():
        buttons.append(InlineKeyboardButton(
            text=text,
            callback_data=callback))

    keyboard: InlineKeyboardMarkup = kb_builder.row(*buttons, width=width).as_markup()
    return keyboard


async def get_service_keyboard() -> InlineKeyboardMarkup:
    """Получает список услуг и формирует из них клавиатуру на лету"""
    services: list[dict] = await database.get_services_from_db()
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    for service in services:
        buttons.append(InlineKeyboardButton(
            text=f"{service['service_name']}",
            callback_data=str(service['service_name'])
        ))

    keyboard: InlineKeyboardMarkup = kb_builder.row(*buttons, cancel_button, width=1).as_markup()
    return keyboard


# -------------------------------- Клавиатура календаря -------------------------------------
async def get_calendar_keyboard(date_id) -> InlineKeyboardMarkup:
    """Принимает id страницы календаря.
    Возвращает инлайн клавиатуру календаря"""
    await database.delete_old_records()  # Удаляет старые записи
    date: tuple = await keyboards_utils.get_date(date_id)
    month_calendar: list[list] = await keyboards_utils.get_working_days_for_month(date_id, date)
    pagination = await _get_pagination(date, date_id)
    keyboard: list = list()
    date: tuple = (str(date[0]), str(date[1]))
    for i in range(len(month_calendar)):
        keyboard.append([])
        for j in range(7):
            day_num = str(month_calendar[i][j])
            if day_num == '0':
                text = ' '
            else:
                text = day_num
            keyboard[i].append(InlineKeyboardButton(text=text,
                                                    callback_data=CalendarCallback(year=date[0],
                                                                                   month=date[1],
                                                                                   day=day_num).pack()))
    keyboard.insert(0, days_of_the_week)
    keyboard.append(pagination)
    keyboard.append([cancel_button])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _get_days_of_the_week() -> list:
    """Возвращает список из кнопок с днями недели"""
    days_of_the_week_buttons = list()
    for text in DAYS_OF_THE_WEEK:
        days_of_the_week_buttons.append(InlineKeyboardButton(text=text,
                                                             callback_data='0'))
    return days_of_the_week_buttons


async def _get_pagination(date, date_id) -> list:
    """Возвращает список кнопок пагинации"""
    date_btn = InlineKeyboardButton(text=f'{MONTHS[date[1]]} {date[0]}',
                                    callback_data='0')
    if date_id == 0:
        pagination = [pagination_buttons['empty'], date_btn, pagination_buttons['>>']]
    elif date_id == MONTH_LIMIT:
        pagination = [pagination_buttons['<<'], date_btn, pagination_buttons['empty']]
    else:
        pagination = [pagination_buttons['<<'], date_btn, pagination_buttons['>>']]

    return pagination


async def get_time_to_record(date: str, service_name: str):
    """Возвращает клавиатуру со свободным временем для записи"""
    time_to_record_list: list = await keyboards_utils.get_free_time_on_date(date, service_name)
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    for time in time_to_record_list:
        buttons.append(InlineKeyboardButton(
            text=str(time)[:-3],
            callback_data=str(time)
        ))

    keyboard: InlineKeyboardMarkup = kb_builder.row(*buttons, width=3).as_markup()
    keyboard.inline_keyboard.append([back_button])
    return keyboard


async def get_records_keyboard(date):
    """Возвращает клавиатуру с записями пользователей на текущую дату"""
    records_list: list[dict] = await database.get_schedule_for_date_from_db(date=date)
    records_list = sorted(records_list, key=lambda x: x['time'])
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    for record in records_list:
        buttons.append(InlineKeyboardButton(
            text=f"{str(record['time'])[:-3]} - {record['service_name']}",
            callback_data=str(record['time'])
        ))
    keyboard: InlineKeyboardMarkup = kb_builder.row(*buttons, cancel_button, width=1).as_markup()
    return keyboard

# Кнопка Cancel
cancel_button: InlineKeyboardButton = InlineKeyboardButton(text='Отмена', callback_data='cancel')
cancel_kb: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])

# Кнопка Next
next_button: InlineKeyboardButton = InlineKeyboardButton(text='Далее', callback_data='next')
next_kb: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=[[next_button]])

# Кнопка Back
back_button: InlineKeyboardButton = InlineKeyboardButton(text='Назад', callback_data='back')

# Кнопки календаря
days_of_the_week = _get_days_of_the_week()

# Кнопки пагинации
pagination_buttons = {'<<': InlineKeyboardButton(text='<<',
                                                 callback_data='backward'),
                      '>>': InlineKeyboardButton(text='>>',
                                                 callback_data='forward'),
                      'empty': InlineKeyboardButton(text=' ',
                                                    callback_data='0')}

# Клавиатура next_cancel
next_cancel_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=[[next_button],
                                                                                   [cancel_button]])

# Клавиатура next_back
next_back_keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(inline_keyboard=[[next_button],
                                                                                 [back_button]])

# Генерирую стартовую клавиатуру администратора
admin_start_keyboard = get_start_keyboard(ADMIN_LEXICON['start_buttons'], width=1)

# Генерирую стартовую клавиатуру пользователя
user_start_keyboard = get_start_keyboard(USER_LEXICON['start_buttons'], width=1)
