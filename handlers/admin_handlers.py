from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from config_data.config import ADMIN_IDS
from db.db import database
from services.services import get_all_records
from filters.filters import check_add_service_name
from keyboards import inline
from lexicon.lexicon import ADMIN_LEXICON, OTHER_LEXICON
from states.states import FSMAddService, FSMRemoveService, FSMRecords

router: Router = Router()

# Регистрирует в роутер фильтры по id администраторов бота.
router.message.filter(lambda message: message.from_user.id in ADMIN_IDS)
router.callback_query.filter(lambda message: message.from_user.id in ADMIN_IDS)


# --------------------------------------------------- ХЭНДЕЛРЫ --------------------------------------------------------

# Команда старт
@router.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(text=OTHER_LEXICON['start'],
                         reply_markup=inline.admin_start_keyboard)


# -------------------- Команда "Добавить услугу" ----------------------------------
@router.callback_query(F.data == 'add_service_button', StateFilter(default_state))
async def process_add_service_command(callback: CallbackQuery, state: FSMContext):
    """Срабатывает на нажатие кнопки 'Добавить услугу'
    Запускает машину состояний"""
    await callback.message.answer(text=ADMIN_LEXICON['add_service_name'],
                                  reply_markup=inline.cancel_kb)
    # Устанавливаем состояние ожидания ввода имени
    await state.set_state(FSMAddService.service_name)
    await callback.answer()


# НАЗВАНИЕ
@router.message(StateFilter(FSMAddService.service_name), check_add_service_name)
async def process_add_service_name(message: Message, state: FSMContext):
    """Отлавливает ввод названия услуги.
    Переводит состояние на ввод длительности оказания услуги"""
    await state.update_data(name=message.text)
    await message.answer(text=ADMIN_LEXICON['add_service_duration'],
                         reply_markup=inline.cancel_kb)
    # Устанавливаем состояние ожидания ввода времени оказания услуги
    await state.set_state(FSMAddService.service_duration)


@router.message(StateFilter(FSMAddService.service_name))
async def warning_add_service_not_name(message: Message):
    """Срабатывает, если название услуги было введено некорректно"""
    await message.answer(text=ADMIN_LEXICON['add_service_not_name'])


# ДЛИТЕЛЬНОСТЬ
@router.message(StateFilter(FSMAddService.service_duration), F.text.isdigit())
async def process_add_service_duration(message: Message, state: FSMContext):
    """Отлавливает ввод длительности оказания услуги.
    Переводит состояние на ввод стоймости услуги"""
    await state.update_data(duration=message.text)
    await message.answer(text=ADMIN_LEXICON['add_service_price'],
                         reply_markup=inline.cancel_kb)
    # Устанавливаем состояние ожидания ввода стоймости оказания услуги
    await state.set_state(FSMAddService.service_price)


@router.message(StateFilter(FSMAddService.service_duration))
async def warning_add_service_not_duration(message: Message):
    """Срабатывает, если длительность услуги была введена некорректно"""
    await message.answer(text=ADMIN_LEXICON['add_service_not_duration'])


# ЦЕНА
@router.message(StateFilter(FSMAddService.service_price), F.text.isdigit())
async def process_add_service_price(message: Message, state: FSMContext):
    """Отлавливает ввод стоймости оказания услуги"""
    await state.update_data(price=message.text)
    await message.answer(text=ADMIN_LEXICON['add_service_description'],
                         reply_markup=inline.next_cancel_keyboard)
    await state.set_state(FSMAddService.service_description)


@router.message(StateFilter(FSMAddService.service_price))
async def warning_add_service_not_price(message: Message):
    """Срабатывает, если стоймость услуги была введена некорректно"""
    await message.answer(text=ADMIN_LEXICON['add_service_not_price'])


# ОПИСАНИЕ
@router.callback_query(StateFilter(FSMAddService.service_description), F.data == 'next')
@router.message(StateFilter(FSMAddService.service_description), F.text)
async def process_add_service_description(answer: Message | CallbackQuery, state: FSMContext):
    if isinstance(answer, Message):
        answer: Message
        await state.update_data(description=answer.text)
        await answer.answer(text=ADMIN_LEXICON['add_service_save_data'],
                            reply_markup=inline.admin_start_keyboard)
    else:
        answer: CallbackQuery
        await state.update_data(description=None)
        await answer.message.answer(text=ADMIN_LEXICON['add_service_save_data'],
                                    reply_markup=inline.admin_start_keyboard)
        await answer.answer()

    # Сохраняет данные в бд
    data = await state.get_data()
    await database.add_service_to_db(data)

    # Очищаем машину состояний
    await state.clear()


@router.message(StateFilter(FSMAddService.service_description))
async def warning_add_service_incorrect_description(message: Message):
    await message.answer(text=ADMIN_LEXICON['add_service_incorrect_description'],
                         reply_markup=inline.next_cancel_keyboard)


# ---------------------------------------------------------------------------------

# --------------------- Команда "Удалить услугу" ----------------------------------
@router.callback_query(F.data == 'remove_service_button', StateFilter(default_state))
async def process_remove_service_command(callback: CallbackQuery, state: FSMContext):
    """Срабатывает на нажатие кнопки 'Удалить услугу'
    Выводит клавиатуру со списком услуг пользователю"""
    keyboard = await inline.get_service_keyboard()
    await state.set_state(FSMRemoveService.state_remove)
    await callback.message.answer(text=ADMIN_LEXICON['remove_service_message'],
                                  reply_markup=keyboard)
    await callback.answer()


@router.message(StateFilter(FSMRemoveService.state_remove))
async def warning_remove_service(message: Message):
    """Срабатывает, если вместо события нажатия кнопки, было совершено нечто другое"""
    await message.answer(text=ADMIN_LEXICON['remove_not_service'])


@router.callback_query(F.data != 'cancel', StateFilter(FSMRemoveService.state_remove))
async def process_remove_service(callback: CallbackQuery, state: FSMContext):
    """Срабатывает на нажатие кнопки с услугой, которую нужно удалить"""
    await database.remove_service_from_db(callback.data)
    await state.clear()
    await callback.message.answer(text=ADMIN_LEXICON['remove_service_success'],
                                  reply_markup=inline.admin_start_keyboard)
    await callback.answer()


# ---------------------------------------------------------------------------------

# ------------------ Команда "Посмотреть все доступные записи" --------------------
@router.callback_query(F.data == 'view_all_records', StateFilter(default_state))
async def process_view_appointment_command(callback: CallbackQuery):
    """Срабатывает на нажатие кнопки 'Посмотреть все доступные записи'"""
    all_records: str = await get_all_records()
    await callback.message.answer(text=all_records,
                                  reply_markup=inline.admin_start_keyboard)
    await callback.answer()

# ---------------------------------------------------------------------------------

# ----------- Команда "Посмотреть/Удалить запись на конкретную дату" --------------
@router.callback_query(StateFilter(FSMRecords.choice_date), inline.CalendarCallback.filter(F.day != '0'))
async def process_date_press(callback: CallbackQuery, callback_data: inline.CalendarCallback, state: FSMContext):
    """Срабатывает на нажатие кнопки с выбором даты"""
    await state.set_state(FSMRecords.choice_record)
    await state.update_data(date=f'{callback_data.year}{callback_data.month:>02}{callback_data.day:>02}')
    states = await state.get_data()
    keyboard = await inline.get_records_keyboard(date=states['date'])
    if len(keyboard.inline_keyboard) > 1:
        await callback.message.answer(text=ADMIN_LEXICON['choice_record_message'],
                                      reply_markup=keyboard)
    else:
        await state.set_state(FSMRecords.choice_date)
        keyboard = await inline.get_calendar_keyboard(date_id=states['date_id'])
        await callback.message.answer(text=ADMIN_LEXICON['no_record_message'],
                                      reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data != 'cancel', StateFilter(FSMRecords.choice_record))
async def process_remove_record(callback: CallbackQuery, state: FSMContext):
    """Срабатывает на нажатие кнопки с записью, которую нужно удалить"""
    states = await state.get_data()
    await database.delete_record(date=states['date'], time=callback.data)
    await callback.message.answer(text=ADMIN_LEXICON['record_deleted'],
                                  reply_markup=inline.admin_start_keyboard)
    await state.clear()
    await callback.answer()
