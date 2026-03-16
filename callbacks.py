import os
from aiogram import Router, F, types
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from services.music_downloader import search_music_options, download_music_by_id
from database import get_user_language, increment_download
from locales.texts import TEXTS

callbacks_router = Router()

@callbacks_router.callback_query(F.data.startswith("dl_m:"))
async def process_music_download(callback: types.CallbackQuery):
    query = callback.data.split("dl_m:")[1]
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    TEXTS = {
        'en': {
            'music_search': "🔍 Searching options for '{query}'... Please wait.",
            'select_track': "🎵 Select a track to download:",
            'music_not_found': "❌ Sorry, no music found.",
            'dl_error': "❌ Unexpected error occurred.",
            'btn_downloading': "Downloading..."
        },
        'uz': {
            'music_search': "🔍 '{query}' variantlari qidirilmoqda... Iltimos kuting.",
            'select_track': "🎵 Yuklash uchun kerakli trekni tanlang:",
            'music_not_found': "❌ Kechirasiz, musiqa topilmadi.",
            'dl_error': "❌ Kutilmagan xatolik yuz berdi.",
            'btn_downloading': "Yuklanmoqda..."
        },
        'ru': {
            'music_search': "🔍 Поиск вариантов для '{query}'... Подождите.",
            'select_track': "🎵 Выберите трек для скачивания:",
            'music_not_found': "❌ Извините, музыка не найдена.",
            'dl_error': "❌ Произошла непредвиденная ошибка.",
            'btn_downloading': "Скачивается..."
        }
    }
    
    # Callback loading'ni to'xtatish
    await callback.answer(TEXTS[lang].get('music_search_short', '...'), show_alert=False)
    status_msg = await callback.message.answer(TEXTS[lang]['music_search'].format(query=query))
    
    try:
        # 1. Musiqani 5 ta variantini izlash
        options = await search_music_options(query, limit=5)
        
        if options:
            import html
            escaped_query = html.escape(query)
            text = f"🎵 <b>{escaped_query}</b>\n\n"
            inline_kb = []
            row_btns = []
            
            for idx, opt in enumerate(options, 1):
                duration_sec = opt.get('duration')
                if duration_sec:
                    duration_sec = int(duration_sec)
                    mins = duration_sec // 60
                    secs = duration_sec % 60
                    duration_str = f" {mins}:{secs:02d}"
                else:
                    duration_str = ""
                    
                title = html.escape(opt['title'])
                text += f"<b>{idx}.</b> {title} <b>{duration_str}</b>\n"
                
                btn = InlineKeyboardButton(text=str(idx), callback_data=f"dl_id:{opt['id']}")
                row_btns.append(btn)
                
            inline_kb.append(row_btns)
            
            markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
            await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
        else:
            await callback.message.answer(TEXTS[lang]['music_not_found'])
            
    except Exception as e:
        await callback.message.answer(TEXTS[lang]['dl_error'])
        print(f"Music options search error: {e}")
    finally:
        await status_msg.delete()

@callbacks_router.callback_query(F.data.startswith("dl_id:"))
async def download_selected_music(callback: types.CallbackQuery):
    video_id = callback.data.split("dl_id:")[1]
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    TEXTS_DL = {
        'uz': {'downloading': "Yuklanmoqda...", 'found': "🎵 Musiqa yuklandi", 'err': "❌ Kechirasiz xatolik yuz berdi"},
        'ru': {'downloading': "Скачивается...", 'found': "🎵 Музыка скачана", 'err': "❌ Извините, произошла ошибка"},
        'en': {'downloading': "Downloading...", 'found': "🎵 Music downloaded", 'err': "❌ Sorry, an error occurred"}
    }
    
    await callback.answer(TEXTS_DL[lang]['downloading'])
    status_msg = await callback.message.answer(f"⏳ {TEXTS_DL[lang]['downloading']}")
    
    try:
        file_path = await download_music_by_id(video_id)
        if file_path:
            audio_file = FSInputFile(file_path)
            await callback.message.answer_audio(audio=audio_file, caption=TEXTS_DL[lang]['found'])
            await increment_download(user_id) # Statistika oshiriladi
            
            import asyncio
            import os
            await asyncio.sleep(1)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
        else:
            await callback.message.answer(TEXTS_DL[lang]['err'])
    except Exception as e:
        await callback.message.answer(TEXTS_DL[lang]['err'])
        print(f"DL By ID error: {e}")
    finally:
        await status_msg.delete()
