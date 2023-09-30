from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from lexicon.lexicon import OTHER_LEXICON

router: Router = Router()


# Кнопка Отмена
@router.callback_query(F.data == 'cancel')
async def process_cancel_command(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(text=OTHER_LEXICON['cancel'])
    await callback.answer()


# Хэндлер для сообщений, которые не попали в другие хэндлеры
@router.message(StateFilter(default_state))
async def send_answer(message: Message):
    await message.answer(text=OTHER_LEXICON['other_answer'])


@router.callback_query()
async def use_old_callback(callback: CallbackQuery):
    await callback.message.answer(text=OTHER_LEXICON['use_old_callback'])
    await callback.answer()
