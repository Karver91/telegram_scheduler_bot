from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

import keyboards.inline
from config_data.config import SALON_ADDRESS, SALON_PHONE
from db.db import database
from keyboards import inline
from lexicon.lexicon import USER_LEXICON, OTHER_LEXICON
from filters.filters import check_date
from services.services import check_time_available, get_appointment
from states.states import FSMRecords

router: Router = Router()


# --------------------------------------------------- ХЭНДЕЛРЫ ------------------------------------------------

# Команда старт
@router.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(text=OTHER_LEXICON['start'],
                         reply_markup=inline.user_start_keyboard)


# -------------------- Команда "Записаться на прием" ----------------------------------
@router.callback_query(F.data == 'make_appointment', StateFilter(default_state))
async def process_make_appointment_command(callback: CallbackQuery, state: FSMContext):
    """Срабатывает на нажатие кнопки 'Записаться на прием'
    Запускает машину состояний"""
    keyboard = await inline.get_service_keyboard()
    await callback.message.answer(text=USER_LEXICON['make_appointment_command_answer'],
                                  reply_markup=keyboard)
    await state.set_state(FSMRecords.choice_service)
    await callback.answer()


@router.callback_query(StateFilter(FSMRecords.choice_service), ~F.data.in_({'next', 'back', 'cancel'}))
async def process_choice_service(callback: CallbackQuery, state: FSMContext):
    """Срабатывает на выбор услуги клиентом"""
    service_description = await database.get_service_description_from_db(callback.data)
    await callback.message.answer(text=f"{service_description['service_name']}\n"
                                       f"{service_description['description'] if service_description['description'] else ''}\n"
                                       f"Продолжительность: {service_description['duration']}\n"
                                       f"Цена: {service_description['price']}",
                                  reply_markup=inline.next_back_keyboard)
    await state.update_data(service_name=callback.data)
    await callback.answer()


@router.callback_query(F.data == 'remove_records', StateFilter(default_state))
@router.callback_query(StateFilter(FSMRecords.choice_service), F.data == 'next')
async def process_choice_date(callback: CallbackQuery, state: FSMContext):
    """Срабатывает на нажатие кнопки 'Посмотреть/Удалить запись на конкретную дату' для админа.
    Срабатывает на нажатие кнопки 'Далее' при выборе услуги"""
    await state.set_state(FSMRecords.choice_date)
    await state.update_data(date_id=0)
    keyboard = await inline.get_calendar_keyboard(date_id=0)
    await callback.message.answer(text=USER_LEXICON['choice_date_message'],
                                  reply_markup=keyboard)
    await callback.answer()


@router.callback_query(StateFilter(FSMRecords.choice_service), F.data == 'back')
async def process_choice_service_back(callback: CallbackQuery, state: FSMContext):
    """Срабатывает на нажатие кнопки 'Назад' при выборе услуги"""
    await process_make_appointment_command(callback, state)
    await callback.answer()


@router.message(StateFilter(FSMRecords.choice_service))
async def process_not_choice_service(message: Message):
    """Срабатывает, если вместо события нажатия кнопки, было совершено нечто другое"""
    await message.answer(text=USER_LEXICON['process_not_choice_service'])


@router.callback_query(StateFilter(FSMRecords.choice_date), F.data.in_({'forward', 'backward'}))
async def process_pagination_press(callback: CallbackQuery, state: FSMContext):
    """Срабатывает на нажатие кнопок пагинации для перелистывания страницы календаря"""
    states = await state.get_data()
    if callback.data == 'forward':
        date_id = states['date_id'] + 1
    else:
        date_id = states['date_id'] - 1
    await state.update_data(date_id=date_id)

    keyboard = await inline.get_calendar_keyboard(date_id=date_id)
    await callback.message.edit_reply_markup(text=USER_LEXICON['choice_date_message'],
                                             reply_markup=keyboard)
    await callback.answer()


@router.callback_query(StateFilter(FSMRecords.choice_date), F.data == '0')
@router.callback_query(StateFilter(FSMRecords.choice_date), inline.CalendarCallback.filter(F.day == '0'))
async def process_empty_press(callback: CallbackQuery):
    """Отлавливает нажатия на пустые кнопки"""
    await callback.answer()


@router.callback_query(StateFilter(FSMRecords.choice_date), F.data[:11] == 'date_button', check_date)
async def check_date(callback: CallbackQuery):
    """Отлавливает нажатия на неактуальную дату"""
    await callback.message.answer(text='Эта дата неактуальна, выберете другую')
    await callback.answer()


@router.callback_query(StateFilter(FSMRecords.choice_date), inline.CalendarCallback.filter(F.day != '0'))
async def process_date_press(callback: CallbackQuery, callback_data: inline.CalendarCallback, state: FSMContext):
    """Отлавливает нажатие на кнопку даты в календаре"""
    await state.set_state(FSMRecords.choice_time)
    await state.update_data(date=f'{callback_data.year}{callback_data.month:>02}{callback_data.day:>02}')
    states = await state.get_data()
    keyboard = await keyboards.inline.get_time_to_record(date=states['date'], service_name=states['service_name'])
    if keyboard.inline_keyboard:
        await callback.message.answer(text=USER_LEXICON['choice_time_message'],
                                      reply_markup=keyboard)
    else:
        await state.set_state(FSMRecords.choice_date)
        keyboard = await inline.get_calendar_keyboard(date_id=states['date_id'])
        await callback.message.answer(text=USER_LEXICON['no_time_message'],
                                      reply_markup=keyboard)

    await callback.answer()


@router.callback_query(StateFilter(FSMRecords.choice_time), F.data == 'back')
async def process_choice_time_back(callback: CallbackQuery, state: FSMContext):
    """Срабатывает на нажатие кнопки 'Назад' при выборе времени для записи"""
    await state.set_state(FSMRecords.choice_date)
    states = await state.get_data()
    keyboard = await inline.get_calendar_keyboard(date_id=states['date_id'])
    await callback.message.answer(text=USER_LEXICON['choice_date_message'],
                                  reply_markup=keyboard)
    await callback.answer()


@router.callback_query(StateFilter(FSMRecords.choice_time))
async def process_time_press(callback: CallbackQuery, state: FSMContext):
    """Отлавливает нажатие на кнопку выбора времени для записи"""
    states = await state.get_data()
    if await check_time_available(date=states['date'], time=callback.data):
        await database.add_record_to_schedule(user_id=callback.from_user.id,
                                             service_name=states['service_name'],
                                             date=states['date'],
                                             time=callback.data)
        await callback.message.answer(text=USER_LEXICON['recording successful'],
                                      reply_markup=inline.user_start_keyboard)
        await state.clear()
    else:
        await callback.message.answer(text=USER_LEXICON['recording failed'])
        await process_choice_date(callback, state)
    await callback.answer()


# -------------------- Команда "Посмотреть мою запись" ----------------------------------

@router.callback_query(F.data == 'view_appointment', StateFilter(default_state))
async def process_view_appointment_command(callback: CallbackQuery):
    my_appointment: str = await get_appointment(callback.from_user.id)
    await callback.message.answer(text=my_appointment,
                                  reply_markup=inline.user_start_keyboard)
    await callback.answer()


# -------------------- Команда "Наши контактные данные" ----------------------------------

@router.callback_query(F.data == 'get_contact', StateFilter(default_state))
async def process_get_contact_command(callback: CallbackQuery):
    await callback.message.answer(text=f'Наш адрес: {SALON_ADDRESS}\n\nНомер телефона для связи: {SALON_PHONE}')
    await callback.answer()
