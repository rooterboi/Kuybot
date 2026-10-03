from aiogram import Bot

import database.db as db


async def missing_channels(bot: Bot, uid: int):
    miss = []
    for ch in await db.get_channels():
        try:
            cid = int(ch["chat_id"]) if ch["chat_id"].lstrip("-").isdigit() else ch["chat_id"]
            mem = await bot.get_chat_member(cid, uid)
            if mem.status in ("left", "kicked"):
                miss.append(ch)
        except Exception:
            continue  # bot kanalga kira olmasa o'tkazib yuboramiz
    return miss
