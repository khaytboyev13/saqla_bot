import asyncio
import os
import uuid
import yt_dlp
import logging
import time

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
# Jildni yaratish agar yo'q bo'lsa
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def download_media(url: str, progress_callback=None) -> list[dict]:
    """
    Berilgan URL dan videoni asinxron tarzda yuklab oladi. Playlistlarni qo'llab quvvatlaydi.
    progress_callback(percent_str, speed_str) deb chaqiriluvchi asinxron funksiyani oladi.
    Qaytaradi: dict'lar ro'yxati (list of dictionaries containing file_path, vs) of None.
    """
    unique_id = str(uuid.uuid4())[:8]
    output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}_%(title)s.%(ext)s")
    
    loop = asyncio.get_event_loop()
    last_update = [time.time()]

    def my_hook(d):
        if d['status'] == 'downloading' and progress_callback:
            now = time.time()
            if now - last_update[0] >= 2.0:  # 2 soniyalik debounce (Spamni oldini olish)
                last_update[0] = now
                # Konsol ranglarini tozalash
                import re
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                percent = ansi_escape.sub('', d.get('_percent_str', '')).strip()
                speed = ansi_escape.sub('', d.get('_speed_str', '')).strip()
                asyncio.run_coroutine_threadsafe(progress_callback(percent, speed), loop)
                
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [my_hook] if progress_callback else [],
        'cookiefile': 'cookies.txt', # Agar Instagram kabi joylardan muammo bo'lsa cookies ishlatish uchun
    }
    
    def extract_and_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # extract_info ni 'extract_flat=False' sharti bilan yuboramizki barchasi yuklansin
            info_dict = ydl.extract_info(url, download=True)
            if not info_dict:
                return []
                
            results = []
            # Agar bu playlist yoki karusel rasmlar ro'yxati bo'lsa
            if 'entries' in info_dict:
                for entry in info_dict['entries']:
                    if entry:
                        results.append({
                            'file_path': ydl.prepare_filename(entry),
                            'title': entry.get('title', 'Unknown Title'),
                            'duration': entry.get('duration', 0)
                        })
            else:
                results.append({
                    'file_path': ydl.prepare_filename(info_dict),
                    'title': info_dict.get('title', 'Unknown Title'),
                    'duration': info_dict.get('duration', 0)
                })
            return results

    try:
        # Bloklovchi funksiyani asinxronga o'tkazamiz (loop tepada olingan edi)
        result = await loop.run_in_executor(None, extract_and_download)
        return result
    except Exception as e:
        logger.error(f"Yuklab olishda xatolik: {e}")
        return []
