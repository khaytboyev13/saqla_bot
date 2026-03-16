from aiogram import BaseMiddleware, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_all_channels, get_user_language
from locales.texts import TEXTS

class CheckSubscribe(BaseMiddleware):
    async def __call__(self, handler, event: types.Message | types.CallbackQuery, data: dict):
        user = event.from_user
        if not user:
            return await handler(event, data)
            
        # Adminlar uchun tekshirmaymiz (agar xohlasangiz bu yerga ADMIN_ID shartini qo'shishingiz mumkin)
        
        channels = await get_all_channels()
        if not channels:
            return await handler(event, data) # Agar bazada kanallar bo'lmasa, o'tkazib yuboramiz
            
        bot = data.get('bot')
        lang = await get_user_language(user.id)
        
        not_subscribed = []
        for ch in channels:
            try:
                member = await bot.get_chat_member(chat_id=ch['id'], user_id=user.id)
                if member.status in ['left', 'kicked', 'banned']:
                    not_subscribed.append(ch)
            except Exception as e:
                # Agar bot kanalga admin bo'lmasa xato beradi, lekin baribir ro'yxatga qo'shamiz
                not_subscribed.append(ch)
                print(f"Boshqaruv xatosi (Kanal ID: {ch['id']}): {e}")
                
        if not_subscribed:
            # Agar obuna bo'lmagan kanallari bo'lsa
            kb = []
            for idx, ch in enumerate(not_subscribed, 1):
                kb.append([InlineKeyboardButton(text=f"Kanal {idx}", url=ch['url'])])
                
            # Tekshirish tugmasi qo'shish
            kb.append([InlineKeyboardButton(text=TEXTS[lang]['btn_check_sub'], callback_data="check_sub")])
            markup = InlineKeyboardMarkup(inline_keyboard=kb)
            
            text = TEXTS[lang]['must_subscribe']
            
            if isinstance(event, types.Message):
                await event.answer(text, reply_markup=markup)
            elif isinstance(event, types.CallbackQuery):
                if event.data == "check_sub":
                    await event.answer("Siz to'liq a'zo bo'lmadingiz!", show_alert=True)
                else:
                    await event.message.answer(text, reply_markup=markup)
            return # Skip the handler
            
        # Hammasiga a'zo bo'lgan bo'lsa, o'z ishimizni davom ettiramiz
        return await handler(event, data)
