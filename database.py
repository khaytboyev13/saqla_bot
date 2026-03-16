import aiosqlite
import logging

logger = logging.getLogger(__name__)

DB_NAME = "users-database.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                language_code TEXT DEFAULT 'en',
                download_count INTEGER DEFAULT 0
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                channel_url TEXT
            )
        ''')
        
        # Migratsiya: agar jadval qadimiy bo'lsa va download_count ustuni yo'q bo'lsa uni qo'shish
        try:
            await db.execute('ALTER TABLE users ADD COLUMN download_count INTEGER DEFAULT 0')
        except Exception as e:
            # Agar ustun allaqachon mavjud bo'lsa 'duplicate column name' xatosini ignor qiladi
            pass
            
        await db.commit()
    logger.info("Ma'lumotlar bazasi (SQLite) ishga tushirildi.")

async def add_user(user_id: int, first_name: str, username: str, language_code: str = 'en'):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO users (user_id, first_name, username, language_code) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET 
                first_name=excluded.first_name,
                username=excluded.username
        ''', (user_id, first_name, username, language_code))
        await db.commit()

async def get_user_language(user_id: int) -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT language_code FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 'en'

async def set_user_language(user_id: int, language_code: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET language_code = ? WHERE user_id = ?', (language_code, user_id))
        await db.commit()

async def get_all_users() -> list[int]:
    """Barcha foydalanuvchilar id raqamlarini qaytaradi"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id FROM users') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
            
async def get_full_users_data() -> list[dict]:
    """Barcha foydalanuvchilarning to'liq ma'lumotlarini qaytaradi (Eksport uchun)"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id, first_name, username, language_code, download_count FROM users') as cursor:
            rows = await cursor.fetchall()
            return [{'user_id': r[0], 'first_name': r[1], 'username': r[2], 'language': r[3], 'downloads': r[4]} for r in rows]
            
async def count_users() -> int:
    """Foydalanuvchilar umumiy soni"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def increment_download(user_id: int):
    """Foydalanuvchining yuklashlar sonini 1 taga oshiradi"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE users SET download_count = download_count + 1 WHERE user_id = ?', (user_id,))
        await db.commit()
        
async def get_user_stats(user_id: int) -> dict:
    """Yagona foydalanuvchining ma'lumotlarini (ismi va yuklashlari sonini) qaytaradi"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT first_name, download_count FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {'first_name': row[0], 'downloads': row[1]}
            return {'first_name': 'Unknown', 'downloads': 0}

async def get_top_users(limit: int = 10) -> list[dict]:
    """Eng ko'p yuklash qilgan TOP foydalanuvchilarni qaytaradi"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT first_name, download_count FROM users ORDER BY download_count DESC LIMIT ?', (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [{'first_name': row[0], 'downloads': row[1]} for row in rows]
            
# --- CHANNELS FOR SPONSORSHIP ---

async def add_channel(channel_id: str, channel_url: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO channels (channel_id, channel_url) 
            VALUES (?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET 
                channel_url=excluded.channel_url
        ''', (channel_id, channel_url))
        await db.commit()

async def remove_channel(channel_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM channels WHERE channel_id = ?', (channel_id,))
        await db.commit()

async def get_all_channels() -> list[dict]:
    """Barcha majburiy kanallarni id va url bilan dict ro'yxatida qaytaradi"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT channel_id, channel_url FROM channels') as cursor:
            rows = await cursor.fetchall()
            return [{'id': row[0], 'url': row[1]} for row in rows]
