# from aiogram import types, Router
# from aiogram.types import ReplyKeyboardRemove
# from aiogram.fsm.context import FSMContext
# from aiogram.enums import ParseMode
# from aiogram.exceptions import TelegramBadRequest
# import re, logging

# from states.registration import RegistrationStates
# from utils.regex import isValidName

# logger = logging.getLogger(__name__)
# router = Router()


# @router.message(RegistrationStates.NAME)
# async def process_name(message: types.Message, state: FSMContext):
#     if not isValidName(message.text):
#         await message.answer("<b>Iltimos, lotin harflarida yozing.</b>", parse_mode=ParseMode.HTML)
#         logger.warning(f"User {message.from_user.id} used Cyrillic characters")
#         return
#     await state.update_data(name=message.text)
#     user_data = await state.get_data()
#     lang = user_data['language']
#     await message.answer(messages[lang]["ask_birthdate"], parse_mode=ParseMode.HTML)
#     await state.set_state(RegistrationStates.BIRTHDATE)
