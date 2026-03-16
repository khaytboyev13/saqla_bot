from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import add_user, get_user_language, set_user_language, get_user_stats
from locales.texts import TEXTS

start_router = Router()

@start_router.message(CommandStart())
async def start_handler(message: types.Message):
    await add_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username
    )

    lang = await get_user_language(message.from_user.id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")
        ]
    ])

    await message.answer(
        TEXTS[lang]['start'].format(name=message.from_user.first_name),
        parse_mode="HTML"
    )
    await message.answer(TEXTS[lang]['choose_lang'], reply_markup=keyboard)

@start_router.callback_query(F.data.startswith("lang:"))
async def change_language(callback: types.CallbackQuery):
    lang_code = callback.data.split(":")[1]
    user_id = callback.from_user.id

    await set_user_language(user_id, lang_code)

    await callback.message.edit_text(TEXTS[lang_code]['lang_saved'])
    await callback.message.answer(
        TEXTS[lang_code]['start'].format(name=callback.from_user.first_name),
        parse_mode="HTML"
    )
    await callback.answer()

@start_router.message(Command("profile"))
async def my_profile(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)

    stats = await get_user_stats(user_id)
    count = stats['downloads']

    TEXT_PROF = {
        'uz': "👤 <b>Sizning profilingiz:</b>\n\n🆔 ID: <code>{id}</code>\n📥 Yuklangan medialar: <b>{cnt}</b> ta",
        'ru': "👤 <b>Ваш профиль:</b>\n\n🆔 ID: <code>{id}</code>\n📥 Скачано медиа: <b>{cnt}</b>",
        'en': "👤 <b>Your profile:</b>\n\n🆔 ID: <code>{id}</code>\n📥 Downloaded media: <b>{cnt}</b>"
    }

    await message.answer(TEXT_PROF[lang].format(id=user_id, cnt=count), parse_mode="HTML")