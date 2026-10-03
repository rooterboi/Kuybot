import os
from datetime import datetime, timedelta, timezone

import aiosqlite

from config import DB_PATH

TZ = timezone(timedelta(hours=5))  # Toshkent


def today() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, joined TEXT, last_active TEXT);
CREATE TABLE IF NOT EXISTS channels(chat_id TEXT PRIMARY KEY, title TEXT, link TEXT);
CREATE TABLE IF NOT EXISTS movies(
    code TEXT PRIMARY KEY, file_id TEXT, ftype TEXT, title TEXT, year TEXT,
    quality TEXT, country TEXT, lang TEXT, genre TEXT, added TEXT);
CREATE TABLE IF NOT EXISTS kino_admins(user_id INTEGER PRIMARY KEY);
"""


async def init():
    d = os.path.dirname(DB_PATH)
    if d:
        os.makedirs(d, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def _exec(sql, args=()):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(sql, args)
        await db.commit()


async def _all(sql, args=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(sql, args)
        return [dict(r) for r in await cur.fetchall()]


async def _one(sql, args=()):
    rows = await _all(sql, args)
    return rows[0] if rows else None


# ---------- users ----------
async def touch_user(uid: int, name: str):
    t = today()
    await _exec(
        "INSERT INTO users(id,name,joined,last_active) VALUES(?,?,?,?) "
        "ON CONFLICT(id) DO UPDATE SET name=excluded.name, last_active=excluded.last_active",
        (uid, name, t, t),
    )


async def all_user_ids():
    return [r["id"] for r in await _all("SELECT id FROM users")]


async def stats():
    t = today()
    week = (datetime.now(TZ) - timedelta(days=6)).strftime("%Y-%m-%d")
    q = lambda sql, a=(): _one(sql, a)
    return {
        "total": (await q("SELECT COUNT(*) c FROM users"))["c"],
        "new_today": (await q("SELECT COUNT(*) c FROM users WHERE joined=?", (t,)))["c"],
        "active_today": (await q("SELECT COUNT(*) c FROM users WHERE last_active=?", (t,)))["c"],
        "active_week": (await q("SELECT COUNT(*) c FROM users WHERE last_active>=?", (week,)))["c"],
        "movies": (await q("SELECT COUNT(*) c FROM movies"))["c"],
        "channels": (await q("SELECT COUNT(*) c FROM channels"))["c"],
    }


# ---------- channels ----------
async def add_channel(chat_id, title, link):
    await _exec("INSERT OR REPLACE INTO channels VALUES(?,?,?)", (str(chat_id), title, link))


async def del_channel(chat_id):
    await _exec("DELETE FROM channels WHERE chat_id=?", (str(chat_id),))


async def get_channels():
    return await _all("SELECT * FROM channels")


# ---------- movies ----------
async def add_movie(d: dict):
    await _exec(
        "INSERT OR REPLACE INTO movies VALUES(?,?,?,?,?,?,?,?,?,?)",
        (d["code"], d["file_id"], d["ftype"], d["title"], d["year"], d["quality"],
         d["country"], d["lang"], d["genre"], today()),
    )


async def get_movie(code: str):
    return await _one("SELECT * FROM movies WHERE code=?", (code,))


async def del_movie(code: str) -> bool:
    if not await get_movie(code):
        return False
    await _exec("DELETE FROM movies WHERE code=?", (code,))
    return True


async def list_movies(limit=40):
    return await _all("SELECT code,title,year FROM movies ORDER BY CAST(code AS INTEGER) DESC LIMIT ?", (limit,))


async def next_code() -> int:
    r = await _one("SELECT MAX(CAST(code AS INTEGER)) m FROM movies")
    return (r["m"] or 0) + 1


# ---------- kino admins ----------
async def add_kino_admin(uid: int):
    await _exec("INSERT OR IGNORE INTO kino_admins VALUES(?)", (uid,))


async def is_kino_admin(uid: int) -> bool:
    return bool(await _one("SELECT 1 x FROM kino_admins WHERE user_id=?", (uid,)))
