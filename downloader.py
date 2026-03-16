import os
from aiogram import Router, types, F
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
from services.media_downloader import download_media
from services.music_recognizer import recognize_music
from database import get_user_language, increment_download
from locales.texts import TEXTS

downloader_router = Router()

@downloader_router.message(F.text.regexp(r'https?://[^\s]+'))
async def handle_url(message: types.Message):
    url = message.text.strip()
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    status_msg = await message.reply(TEXTS[lang]['downloading'])

    async def progress_cb(percent: str, speed: str):
        bar_length = 10
        try:
            p = float(percent.replace('%', '').strip())
            filled = int(bar_length * (p / 100))
        except ValueError:
            filled = 0
            
        bar = '█' * filled + '▒' * (bar_length - filled)
        text = f"⏳ Yuklanmoqda...\n\n[{bar}] <b>{percent}</b>\n🚀 Tezlik: {speed}"
        
        from aiogram.exceptions import TelegramAPIError
        try:
            await status_msg.edit_text(text, parse_mode="HTML")
        except TelegramAPIError:
            pass # Edit_text xatosi (Bir xil o'zgarishda) bo'lsa kutamiz

    try:
        # 1. Videoni yuklab olish
        media_list = await download_media(url, progress_callback=progress_cb)
        
        if not media_list:
            await status_msg.edit_text(TEXTS[lang]['dl_error'])
            return

        # 2. Musiqani aniqlash faqat birinchi fayl uchun
        first_file_path = media_list[0]['file_path']
        await status_msg.edit_text(TEXTS[lang]['searching_music'])
        music_info = await recognize_music(first_file_path)

        # 3. Yuborish uchun matn tayyorlash
        caption = f"{TEXTS[lang]['video_downloaded']}"
        reply_markup = None
        if music_info:
            # Fayl ostidan original matn olib tashlandi.
            # Tugma tayyorlash
            search_query = f"{music_info['subtitle']} {music_info['title']}"[:50]
            btn = InlineKeyboardButton(
                text=TEXTS[lang]['btn_dl_music'],
                callback_data=f"dl_m:{search_query}"
            )
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[btn]])
        else:
            caption += TEXTS[lang]['music_not_found']

        # 4. Foydalanuvchiga media jo'natish
        await status_msg.edit_text(TEXTS[lang]['sending_video'])
        
        def is_photo(path):
            return os.path.splitext(path)[1].lower() in ['.jpg', '.jpeg', '.png', '.webp']

        if len(media_list) == 1:
            file_path = media_list[0]['file_path']
            media_file = FSInputFile(file_path)
            if is_photo(file_path):
                await message.answer_photo(photo=media_file, caption=caption, reply_markup=reply_markup)
            else:
                await message.answer_video(video=media_file, caption=caption, reply_markup=reply_markup)
        else:
            # Karusel / Playlist
            media_group = []
            for idx, media_item in enumerate(media_list):
                path = media_item['file_path']
                fsi = FSInputFile(path)
                m_caption = caption if idx == 0 else None
                if is_photo(path):
                    media_group.append(InputMediaPhoto(media=fsi, caption=m_caption))
                else:
                    media_group.append(InputMediaVideo(media=fsi, caption=m_caption))
                    
            await message.answer_media_group(media=media_group)
            if reply_markup: # yordamchi knopka mediagroup bilan birga yuborilmaydi
                await message.answer(TEXTS[lang]['send_music'], reply_markup=reply_markup)
        
        # Yuklashlar sonini oshirib qo'yish
        await increment_download(user_id)

        # Status xabarni o'chirish (Video jonatilgandan keyin)
        import asyncio
        await asyncio.sleep(1)
        try:
            await status_msg.delete()
        except: pass

        # Tozalash
        for media_item in media_list:
            file_p = media_item['file_path']
            try:
                if os.path.exists(file_p):
                    os.remove(file_p)
            except Exception as e:
                print(f"O'chirishda xato (kutilyapti): {e}")

    except Exception as e:
        await status_msg.edit_text(TEXTS[lang]['unexpected_error'])
        print(f"Error handling URL: {e}")
