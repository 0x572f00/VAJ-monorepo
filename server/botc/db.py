### db.py (обновлённый с лимитами по каналам)

import os
import datetime
import aiosqlite
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "bot.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channel_limits (
                channel_id INTEGER PRIMARY KEY,
                daily_limit INTEGER NOT NULL DEFAULT 10
            );
        """)

        # Новая таблица для лимитов администраторов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_limits (
                admin_id INTEGER,
                channel_id INTEGER,
                daily_limit INTEGER NOT NULL DEFAULT 10,
                PRIMARY KEY(admin_id, channel_id)
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts_count (
                admin_id    INTEGER,
                channel_id  INTEGER,
                date        TEXT,
                count       INTEGER DEFAULT 0,
                PRIMARY KEY(admin_id, channel_id, date)
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts_total (
                admin_id    INTEGER,
                channel_id  INTEGER,
                total_count INTEGER DEFAULT 0,
                PRIMARY KEY(admin_id, channel_id)
            );
        """)
        await db.commit()

async def get_limit(channel_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT daily_limit FROM channel_limits WHERE channel_id = ?", (channel_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else 10

async def set_limit(channel_id: int, new_limit: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO channel_limits(channel_id, daily_limit) VALUES(?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET daily_limit = excluded.daily_limit;
        """, (channel_id, new_limit))
        await db.commit()

# Функции для работы с лимитами администраторов
async def get_admin_limit(admin_id: int, channel_id: int) -> int:
    """Получить лимит для конкретного администратора в канале"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT daily_limit FROM admin_limits WHERE admin_id = ? AND channel_id = ?", 
            (admin_id, channel_id)
        ) as cur:
            row = await cur.fetchone()
            if row:
                return row[0]
            else:
                # Если нет индивидуального лимита, используем лимит канала
                return await get_limit(channel_id)

async def set_admin_limit(admin_id: int, channel_id: int, new_limit: int):
    """Установить лимит для конкретного администратора в канале"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO admin_limits(admin_id, channel_id, daily_limit) VALUES(?, ?, ?)
            ON CONFLICT(admin_id, channel_id) DO UPDATE SET daily_limit = excluded.daily_limit;
        """, (admin_id, channel_id, new_limit))
        await db.commit()

async def get_all_admin_limits(channel_id: int) -> list[tuple[int, int]]:
    """Получить все индивидуальные лимиты администраторов для канала"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT admin_id, daily_limit FROM admin_limits WHERE channel_id = ?", 
            (channel_id,)
        ) as cur:
            return await cur.fetchall()

async def remove_admin_limit(admin_id: int, channel_id: int):
    """Удалить индивидуальный лимит администратора (будет использоваться лимит канала)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM admin_limits WHERE admin_id = ? AND channel_id = ?", 
            (admin_id, channel_id)
        )
        await db.commit()

# Получить общее число постов (total_count) по каналу
async def get_all_time(channel_id: int) -> list[tuple[int, int]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT admin_id, total_count FROM posts_total WHERE channel_id = ?",
            (channel_id,)
        ) as cur:
            return await cur.fetchall()

# Получить число постов за сегодня по каналу
async def get_daily(channel_id: int) -> list[tuple[int, int]]:
    today = datetime.date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT admin_id, count FROM posts_count WHERE channel_id = ? AND date = ?",
            (channel_id, today)
        ) as cur:
            return await cur.fetchall()

async def get_count(admin_id: int, channel_id: int) -> int:
    today = datetime.date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT count FROM posts_count WHERE admin_id = ? AND channel_id = ? AND date = ?",
            (admin_id, channel_id, today)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

async def inc_count(admin_id: int, channel_id: int):
    today = datetime.date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO posts_count(admin_id, channel_id, date, count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(admin_id, channel_id, date) DO UPDATE
                SET count = count + 1;
        """, (admin_id, channel_id, today))

        await db.execute("""
            INSERT INTO posts_total(admin_id, channel_id, total_count)
            VALUES (?, ?, 1)
            ON CONFLICT(admin_id, channel_id) DO UPDATE
                SET total_count = total_count + 1;
        """, (admin_id, channel_id))
        await db.commit()

async def stats_today(channel_id: int) -> list[tuple[int, int]]:
    today = datetime.date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT admin_id, count FROM posts_count WHERE channel_id = ? AND date = ?",
            (channel_id, today)
        ) as cur:
            return await cur.fetchall()

async def stats_total(channel_id: int) -> list[tuple[int, int]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT admin_id, total_count FROM posts_total WHERE channel_id = ?",
            (channel_id,)
        ) as cur:
            return await cur.fetchall()
        
async def get_today(channel_id: int) -> list[tuple[int, int]]:
    return await stats_today(channel_id)

async def get_all_time(channel_id: int) -> list[tuple[int, int]]:
    return await stats_total(channel_id)

async def reset_daily_limits():
    """Сбросить дневные лимиты (очистить таблицу posts_count)"""
    today = datetime.date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        # Удаляем записи за предыдущие дни, оставляем только сегодняшние
        await db.execute("DELETE FROM posts_count WHERE date < ?", (today,))
        await db.commit()