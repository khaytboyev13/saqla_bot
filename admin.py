from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID
from database import count_users, get_all_users, add_channel, remove_channel, get_all_channels, get_top_users, get_user_language, get_full_users_data
from locales.texts import TEXTS
import asyncio

admin_router = Router()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

# Faqat tashqi fayldan adminlarni filter qila oladigan sodda tekshiruv
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        return
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stat")],
        [InlineKeyboardButton(text="✉️ Xabar yuborish (Broadcast)", callback_data="admin_broadcast")]
    ])
    
    await message.answer("🛠 <b>Admin Panelga xush kelibsiz!</b>\n\nQuyidagi menyulardan birini tanlang:", reply_markup=keyboard, parse_mode="HTML")

@admin_router.callback_query(F.data == "admin_stat")
async def show_statistics(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
        
    total_users = await count_users()
    await callback.message.edit_text(f"📊 <b>Bot Statistikasi</b>\n\nJami foydalanuvchilar: <b>{total_users}</b> ta", parse_mode="HTML")
    await callback.answer()
@admin_router.callback_query(F.data == "admin_broadcast")
async def broadcast_request(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
        
    await callback.message.edit_text("✍️ Barchaga yuborilishi kerak bo'lgan xabarni jo'nating:\n\n<i>Matn, rasm yoki forward qilingan post bo'lishi mumkin. To'xtatish uchun /cancel yozing.</i>", parse_mode="HTML")
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.answer()

@admin_router.message(Command("cancel"))
async def cancel_broadcast(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("❌ Xabar yuborish bekor qilindi.")

@admin_router.message(BroadcastState.waiting_for_message)
async def process_broadcast(message: types.Message, state: FSMContext, bot):
    await state.clear()
    
    users = await get_all_users()
    succnt = 0
    errcnt = 0
    
    status_msg = await message.answer("⏳ Xabarnoma yuborilmoqda...")
    
    for user_id in users:
        try:
            # message.copy_to yordamida istalgan turni forward qilmasdan aslida yuboriladi
            await message.copy_to(chat_id=user_id)
            succnt += 1
            await asyncio.sleep(0.05) # Spamni oldini olish
        except Exception:
            errcnt += 1
            
    await status_msg.edit_text(f"✅ <b>Xabarnoma yakunlandi!</b>\n\nYetib bordi: <b>{succnt}</b> ta\nXatolik (Bloklaganlar): <b>{errcnt}</b> ta", parse_mode="HTML")

@admin_router.message(Command("addchannel"))
async def cmd_addchannel(message: types.Message):
    if not is_admin(message.from_user.id):
        return
        
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("❌ Noto'g'ri format.\nFormat: `/addchannel [kanal_id_yoki_username] [url]`\n\nMasalan: `/addchannel -1001234567890 https://t.me/mening_kanalim`")
        return
        
    channel_id = args[1]
    channel_url = args[2]
    
    await add_channel(channel_id, channel_url)
    await message.answer(f"✅ Kanal muvaffaqiyatli qo'shildi!\nID: {channel_id}\nURL: {channel_url}")

@admin_router.message(Command("delchannel"))
async def cmd_delchannel(message: types.Message):
    if not is_admin(message.from_user.id):
        return
        
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Noto'g'ri format.\nFormat: `/delchannel [kanal_id]`\n\nJoriy kanallar ro'yxatini ko'rish uchun /channels komandasini yuboring.")
        return
        
    channel_id = args[1]
    await remove_channel(channel_id)
    await message.answer(f"✅ Kanal ro'yxatdan o'chirildi (bunday id topilgan bo'lsa)!")

@admin_router.message(Command("channels"))
async def cmd_channels(message: types.Message):
    if not is_admin(message.from_user.id):
        return
        
    channels = await get_all_channels()
    if not channels:
        await message.answer("ℹ️ Majburiy kanallar ro'yxati hozircha bo'sh.")
        return
        
    text = "📋 <b>Sponsor kanallar ro'yxati:</b>\n\n"
    for idx, sh in enumerate(channels, 1):
        text += f"{idx}. <b>ID:</b> {sh['id']} | <b>URL:</b> {sh['url']}\n"
        
    await message.answer(text, parse_mode="HTML")

@admin_router.message(Command("top"))
async def cmd_top(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    top_users = await get_top_users(10)
    
    TEXTS_TOP = {
        'uz': "🏆 <b>Eng faol foydalanuvchilar (Top 10):</b>\n\n",
        'ru': "🏆 <b>Самые активные пользователи (Топ 10):</b>\n\n",
        'en': "🏆 <b>Most active users (Top 10):</b>\n\n"
    }
    
    if not top_users:
        return await message.answer("ℹ️ Hozircha hech qanday natija yo'q!" if lang == 'uz' else "ℹ️ No results yet!")
        
    text = TEXTS_TOP.get(lang, TEXTS_TOP['en'])
    medal_emojis = ["🥇", "🥈", "🥉", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅"]
    
    import html
    for idx, usr in enumerate(top_users):
        name = html.escape(usr['first_name'])
        downloads = usr['downloads']
        emoji = medal_emojis[idx] if idx < len(medal_emojis) else "👤"
        
        text += f"{emoji} <b>{name}</b> — <i>{downloads}</i>\n"
        
    await message.answer(text, parse_mode="HTML")

@admin_router.message(Command("export"))
async def cmd_export_excel(message: types.Message):
    if not is_admin(message.from_user.id):
        return
        
    msg = await message.answer("⏳ Bazaviy hisobot (.xlsx) tayyorlanmoqda, iltimos kuting...")
    
    try:
        import openpyxl
        from aiogram.types import FSInputFile
        import os
        
        users_data = await get_full_users_data()
        
        # Excel kitobini yaratish
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Foydalanuvchilar_Bazasi"
        
        # Sarlavhalarni qo'shish
        headers = ["T/R", "Foydalanuvchi ID", "Ismi", "Username", "Til", "Yuklamalar (Soni)"]
        ws.append(headers)
        
        # Ma'lumotlarni to'ldirish
        for index, user in enumerate(users_data, 1):
            ws.append([
                index,
                user['user_id'],
                user['first_name'],
                user['username'] if user['username'] else "Mavjud emas",
                user['language'],
                user['downloads']
            ])
            
        # Faylni xotiraga saqlash
        filename = "Bot_Baza_Eksport.xlsx"
        wb.save(filename)
        
        # Faylni adminga yuborish
        doc = FSInputFile(filename)
        await message.answer_document(
            document=doc, 
            caption=f"📊 <b>Barcha foydalanuvchilar statistikasi</b>\nJami: {len(users_data)} ta profil.",
            parse_mode="HTML"
        )
        
        await msg.delete()
        
        # Tozalash
        if os.path.exists(filename):
            os.remove(filename)
            
    except Exception as e:
        await msg.edit_text(f"❌ Eksportda xatolik yuz berdi: {e}")
