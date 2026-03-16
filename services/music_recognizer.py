import os
import asyncio
import logging
from shazamio import Shazam

logger = logging.getLogger(__name__)

async def recognize_music(file_path: str) -> dict:
    """
    Shazamio yordamida berilgan media fayldan (audio yoki video bo'lishidan qat'i nazar
    shazamio ffmpeg orqali o'zi ham ajratib olish imkoniga ega) musiqani aniqlaydi.
    """
    if not os.path.exists(file_path):
        logger.error(f"Fayl topilmadi: {file_path}")
        return None

    shazam = Shazam()
    try:
        # Shazamio to'g'ridan-to'g'ri faylni qabul qiladi
        out = await shazam.recognize(file_path)
        
        # Agar musiqa topilgan bo'lsa
        if out and 'track' in out:
            track = out['track']
            return {
                'title': track.get('title', 'Noma\'lum'),
                'subtitle': track.get('subtitle', 'Noma\'lum'),
                'url': track.get('url', ''),
                'coverart': track.get('images', {}).get('coverart', '')
            }
        return None
    except Exception as e:
        logger.error(f"Shazamio xatoligi: {e}")
        return None
