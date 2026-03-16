import os
import asyncio
import uuid
import yt_dlp
import logging

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def search_music_options(query: str, limit: int = 5) -> list[dict]:
    """
    Berilgan so'rov (qo'shiqchi va qo'shiq nomi) bo'yicha Youtubedan bir nechta (limit) natijani faqat ma'lumotlarini qidirib topadi.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True, # Faqat axborot olamiz, download qilmimiz
    }
    
    def extract_info():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{limit}:{query} audio"
            info_dict = ydl.extract_info(search_query, download=False)
            
            if not info_dict or 'entries' not in info_dict or not info_dict['entries']:
                return []
                
            results = []
            for entry in info_dict['entries']:
                if entry:
                    results.append({
                        'id': entry.get('id'),
                        'title': entry.get('title', 'Unknown Title'),
                        'duration': entry.get('duration', 0)
                    })
            return results

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, extract_info)
        return result
    except Exception as e:
        logger.error(f"Musiqa qidirish xatoligi: {e}")
        return []

async def download_music_by_id(video_id: str) -> str | None:
    """
    Berilgan YouTube ID bo'yicha aniq videoning audiosini (MP3) yuklab oladi.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    unique_id = str(uuid.uuid4())[:8]
    output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}_music.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'extract_audio': True,
        'audio_format': 'mp3',
        'audio_quality': '192K',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    def download_audio():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            if not info_dict:
                return None
            
            base_filename, _ = os.path.splitext(ydl.prepare_filename(info_dict))
            return f"{base_filename}.mp3"

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, download_audio)
        return result
    except Exception as e:
        logger.error(f"ID orqali musiqa yuklashda xatolik: {e}")
        return None
