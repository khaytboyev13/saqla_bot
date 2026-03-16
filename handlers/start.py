from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import add_user, get_user_language, set_user_language, get_user_stats
from locales.texts import TEXTS

start_router = Router()


@start_router.message(CommandStart())
async def start_handler(message: types.Message):
    # Foydalanuvchini bazaga qo'shish
    await add_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username
    )

    # Joriy tilni olish
    lang = await get_user_language(message.from_user.id)

    # Tillarni tanlash klaviaturasi
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")
            ]
        ]
    )

    # Start matni
    start_texts = {
        "uz": (
            "Salom! 👋\n\n"
            "Men orqali siz turli xil ijtimoiy tarmoqlardan "
            "(Instagram, YouTube, TikTok va boshqalar) video yuklab olishingiz mumkin.\n\n"
            "Yana bir ajoyib xususiyatim: videoda qanday musiqa yangrayotganini "
            "topib bera olaman (Shazam)!\n\n"
            "Menga shunchaki video havolasini yuboring."
        ),
        "ru": (
            "Привет! 👋\n\n"
            "Через меня вы можете скачивать видео из разных социальных сетей "
            "(Instagram, YouTube, TikTok и других).\n\n"
            "Ещё одна полезная функция: я могу определить, какая музыка играет в видео "
            "(Shazam)!\n\n"
            "Просто отправьте мне ссылку на видео."
        ),
        "en": (
            "Hello! 👋\n\n"
            "You can use me to download videos from various social networks "
            "(Instagram, YouTube, TikTok and others).\n\n"
            "One more great feature: I can find what music is playing in the video "
            "(Shazam)!\n\n"
            "Just send me the video link."
        )
    }

    choose_lang_text = {
        "uz": "🌐 Tilni tanlang:",
        "ru": "🌐 Выберите язык:",
        "en": "🌐 Choose a language:"
    }

    await message.answer(start_texts.get(lang, start_texts["uz"]))
    await message.answer(choose_lang_text.get(lang, choose_lang_text["uz"]), reply_markup=keyboard)


@start_router.callback_query(F.data.startswith("lang:"))
async def change_language(callback: types.CallbackQuery):
    lang_code = callback.data.split(":")[1]
    user_id = callback.from_user.id

    # Bazada tilni yangilash
    await set_user_language(user_id, lang_code)

    # Til saqlandi matni
    lang_saved_text = {
        "uz": "✅ Til O'zbek tiliga o'zgardi!",
        "ru": "✅ Язык изменён на русский!",
        "en": "✅ Language changed to English!"
    }

    # Keyingi xabar
    follow_text = {
        "uz": "📥 Endi menga video linkini yuboring — men sizga videoni yuklab beraman.",
        "ru": "📥 Теперь отправьте мне ссылку на видео — я загружу его для вас.",
        "en": "📥 Now send me the video link — I will download the video for you."
    }

    await callback.message.edit_text(
        lang_saved_text.get(lang_code, lang_saved_text["uz"]),
        reply_markup=None
    )

    await callback.message.answer(
        follow_text.get(lang_code, follow_text["uz"])
    )

    await callback.answer()


@start_router.message(Command("profile"))
async def my_profile(message: types.Message):
    user_id = message.from_user.id
    lang = await get_user_language(user_id)

    stats = await get_user_stats(user_id)
    count = stats["downloads"]

    text_prof = {
        "uz": (
            "👤 <b>Sizning profilingiz:</b>\n\n"
            "🆔 ID: <code>{id}</code>\n"
            "📥 Yuklangan medialar: <b>{cnt}</b> ta"
        ),
        "ru": (
            "👤 <b>Ваш профиль:</b>\n\n"
            "🆔 ID: <code>{id}</code>\n"
            "📥 Скачано медиа: <b>{cnt}</b>"
        ),
        "en": (
            "👤 <b>Your profile:</b>\n\n"
            "🆔 ID: <code>{id}</code>\n"
            "📥 Downloaded media: <b>{cnt}</b>"
        )
    }

    await message.answer(
        text_prof[lang].format(id=user_id, cnt=count),
        parse_mode="HTML"
    )