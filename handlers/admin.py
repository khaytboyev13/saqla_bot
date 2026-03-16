from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from database import (
    count_users,
    get_all_users,
    add_channel,
    remove_channel,
    get_all_channels,
    get_top_users,
    get_user_language,
    get_full_users_data
)

import asyncio
import os

admin_router = Router()


# =========================
# STATES
# =========================
class BroadcastState(StatesGroup):
    waiting_for_message = State()


class ChannelAddState(StatesGroup):
    waiting_channel_url = State()


# =========================
# HELPERS
# =========================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# =========================
# ADMIN PANEL
# =========================
@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stat")],
            [InlineKeyboardButton(text="✉️ Xabar yuborish (Broadcast)", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📡 Majburiy kanallar", callback_data="show_channels")],
            [InlineKeyboardButton(text="🏆 Top foydalanuvchilar", callback_data="show_top_users")],
            [InlineKeyboardButton(text="📁 Excel export", callback_data="admin_export")]
        ]
    )

    await message.answer(
        "🛠 <b>Admin Panelga xush kelibsiz!</b>\n\nQuyidagi menyulardan birini tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================
# STATISTICS
# =========================
@admin_router.callback_query(F.data == "admin_stat")
async def show_statistics(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    total_users = await count_users()

    await callback.message.edit_text(
        f"📊 <b>Bot Statistikasi</b>\n\n"
        f"Jami foydalanuvchilar: <b>{total_users}</b> ta",
        parse_mode="HTML"
    )
    await callback.answer()


# =========================
# BROADCAST
# =========================
@admin_router.callback_query(F.data == "admin_broadcast")
async def broadcast_request(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "✍️ Barchaga yuborilishi kerak bo'lgan xabarni jo'nating:\n\n"
        "<i>Matn, rasm, video yoki forward qilingan post bo'lishi mumkin.\n"
        "To'xtatish uchun /cancel yozing.</i>",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.answer()


@admin_router.message(Command("cancel"))
async def cancel_action(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("❌ Amal bekor qilindi.")


@admin_router.message(BroadcastState.waiting_for_message)
async def process_broadcast(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()

    users = await get_all_users()
    succnt = 0
    errcnt = 0

    status_msg = await message.answer("⏳ Xabarnoma yuborilmoqda...")

    for user_id in users:
        try:
            await message.copy_to(chat_id=user_id)
            succnt += 1
            await asyncio.sleep(0.05)
        except Exception:
            errcnt += 1

    await status_msg.edit_text(
        f"✅ <b>Xabarnoma yakunlandi!</b>\n\n"
        f"Yetib bordi: <b>{succnt}</b> ta\n"
        f"Xatolik (bloklaganlar): <b>{errcnt}</b> ta",
        parse_mode="HTML"
    )


# =========================
# FORCED CHANNELS PANEL
# =========================
@admin_router.callback_query(F.data == "show_channels")
async def show_channels(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kanal/Guruh qo‘shish", callback_data="add_channel_panel")],
            [InlineKeyboardButton(text="📋 Kanallar ro‘yxati", callback_data="list_channels")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_admin_panel")]
        ]
    )

    await callback.message.edit_text(
        "📡 <b>Majburiy obuna boshqaruvi</b>\n\nKerakli bo‘limni tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data == "add_channel_panel")
async def add_channel_panel(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "➕ <b>Kanal yoki guruh qo‘shish</b>\n\n"
        "Kanal yoki guruh linkini yuboring.\n\n"
        "Masalan:\n"
        "https://t.me/kanalim",
        parse_mode="HTML"
    )
    await state.set_state(ChannelAddState.waiting_channel_url)
    await callback.answer()


@admin_router.message(ChannelAddState.waiting_channel_url)
async def save_channel_from_panel(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    channel_url = message.text.strip()

    if not (
        channel_url.startswith("https://t.me/")
        or channel_url.startswith("http://t.me/")
        or channel_url.startswith("@")
    ):
        await message.answer(
            "❌ Noto‘g‘ri link.\n\n"
            "To‘g‘ri format:\n"
            "https://t.me/kanal_nomi\n"
            "yoki\n"
            "@kanal_nomi"
        )
        return

    # ID talab qilinmaydi, linkning o'zi saqlanadi
    await add_channel(channel_url, channel_url)

    await message.answer(
        f"✅ Kanal/Guruh muvaffaqiyatli qo‘shildi!\n\n🔗 {channel_url}"
    )
    await state.clear()


@admin_router.callback_query(F.data == "list_channels")
async def list_channels(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    channels = await get_all_channels()

    if not channels:
        await callback.message.edit_text(
            "ℹ️ Hozircha majburiy kanallar ro‘yxati bo‘sh."
        )
        await callback.answer()
        return

    text = "📋 <b>Majburiy kanallar ro‘yxati:</b>\n\n"
    for idx, ch in enumerate(channels, 1):
        text += f"{idx}. {ch['url']}\n"

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


# =========================
# BACK TO ADMIN PANEL
# =========================
@admin_router.callback_query(F.data == "back_admin_panel")
async def back_admin_panel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stat")],
            [InlineKeyboardButton(text="✉️ Xabar yuborish (Broadcast)", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📡 Majburiy kanallar", callback_data="show_channels")],
            [InlineKeyboardButton(text="🏆 Top foydalanuvchilar", callback_data="show_top_users")],
            [InlineKeyboardButton(text="📁 Excel export", callback_data="admin_export")]
        ]
    )

    await callback.message.edit_text(
        "🛠 <b>Admin Panelga xush kelibsiz!</b>\n\nQuyidagi menyulardan birini tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# =========================
# OLD COMMAND: ADD CHANNEL
# =========================
@admin_router.message(Command("addchannel"))
async def cmd_addchannel(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "❌ Noto'g'ri format.\n\n"
            "Format: /addchannel [kanal_id_yoki_username] [url]\n\n"
            "Masalan:\n"
            "/addchannel -1001234567890 https://t.me/mening_kanalim"
        )
        return

    channel_id = args[1]
    channel_url = args[2]

    await add_channel(channel_id, channel_url)
    await message.answer(
        f"✅ Kanal muvaffaqiyatli qo'shildi!\n"
        f"ID: {channel_id}\n"
        f"URL: {channel_url}"
    )


# =========================
# OLD COMMAND: DELETE CHANNEL
# =========================
@admin_router.message(Command("delchannel"))
async def cmd_delchannel(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Noto'g'ri format.\n\n"
            "Format: /delchannel [kanal_id]\n\n"
            "Ro'yxatni ko'rish uchun /channels yuboring."
        )
        return

    channel_id = args[1]
    await remove_channel(channel_id)
    await message.answer("✅ Kanal ro'yxatdan o‘chirildi.")


# =========================
# OLD COMMAND: CHANNELS LIST
# =========================
@admin_router.message(Command("channels"))
async def cmd_channels(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    channels = await get_all_channels()
    if not channels:
        await message.answer("ℹ️ Majburiy kanallar ro'yxati hozircha bo'sh.")
        return

    text = "📋 <b>Sponsor kanallar ro'yxati:</b>\n\n"
    for idx, ch in enumerate(channels, 1):
        text += f"{idx}. <b>ID:</b> {ch['id']} | <b>URL:</b> {ch['url']}\n"

    await message.answer(text, parse_mode="HTML")


# =========================
# TOP USERS
# =========================
@admin_router.callback_query(F.data == "show_top_users")
async def show_top_users_callback(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    top_users = await get_top_users(10)

    if not top_users:
        await callback.message.edit_text("ℹ️ Hozircha natija yo‘q.")
        await callback.answer()
        return

    medal_emojis = ["🥇", "🥈", "🥉", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅"]
    text = "🏆 <b>Eng faol foydalanuvchilar (Top 10):</b>\n\n"

    import html
    for idx, usr in enumerate(top_users):
        name = html.escape(usr["first_name"] or "No name")
        downloads = usr["downloads"]
        emoji = medal_emojis[idx] if idx < len(medal_emojis) else "👤"
        text += f"{emoji} <b>{name}</b> — <i>{downloads}</i>\n"

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@admin_router.message(Command("top"))
async def cmd_top(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    top_users = await get_top_users(10)

    texts_top = {
        "uz": "🏆 <b>Eng faol foydalanuvchilar (Top 10):</b>\n\n",
        "ru": "🏆 <b>Самые активные пользователи (Топ 10):</b>\n\n",
        "en": "🏆 <b>Most active users (Top 10):</b>\n\n"
    }

    if not top_users:
        no_result = {
            "uz": "ℹ️ Hozircha hech qanday natija yo'q!",
            "ru": "ℹ️ Пока нет результатов!",
            "en": "ℹ️ No results yet!"
        }
        await message.answer(no_result.get(lang, no_result["en"]))
        return

    text = texts_top.get(lang, texts_top["en"])
    medal_emojis = ["🥇", "🥈", "🥉", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅"]

    import html
    for idx, usr in enumerate(top_users):
        name = html.escape(usr["first_name"] or "No name")
        downloads = usr["downloads"]
        emoji = medal_emojis[idx] if idx < len(medal_emojis) else "👤"
        text += f"{emoji} <b>{name}</b> — <i>{downloads}</i>\n"

    await message.answer(text, parse_mode="HTML")


# =========================
# EXPORT
# =========================
@admin_router.callback_query(F.data == "admin_export")
async def admin_export_callback(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    fake_message = callback.message
    fake_message.from_user = callback.from_user
    await cmd_export_excel(fake_message)
    await callback.answer()


@admin_router.message(Command("export"))
async def cmd_export_excel(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    msg = await message.answer("⏳ Bazaviy hisobot (.xlsx) tayyorlanmoqda, iltimos kuting...")

    try:
        import openpyxl
        from aiogram.types import FSInputFile

        users_data = await get_full_users_data()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Foydalanuvchilar_Bazasi"

        headers = ["T/R", "Foydalanuvchi ID", "Ismi", "Username", "Til", "Yuklamalar (Soni)"]
        ws.append(headers)

        for index, user in enumerate(users_data, 1):
            ws.append([
                index,
                user["user_id"],
                user["first_name"],
                user["username"] if user["username"] else "Mavjud emas",
                user["language"],
                user["downloads"]
            ])

        filename = "Bot_Baza_Eksport.xlsx"
        wb.save(filename)

        doc = FSInputFile(filename)
        await message.answer_document(
            document=doc,
            caption=f"📊 <b>Barcha foydalanuvchilar statistikasi</b>\nJami: {len(users_data)} ta profil.",
            parse_mode="HTML"
        )

        await msg.delete()

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        await msg.edit_text(f"❌ Eksportda xatolik yuz berdi: {e}")