from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

import database.db as db
from config import ADMINS
from keyboards.inline import sub_kb
from utils.subscription import missing_channels


class SubMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user is None or user.is_bot:
            return await handler(event, data)
        await db.touch_user(user.id, user.full_name)

        if user.id in ADMINS or await db.is_kino_admin(user.id):
            return await handler(event, data)
        if isinstance(event, CallbackQuery) and event.data == "check_sub":
            return await handler(event, data)
        if isinstance(event, Message) and event.chat.type != "private":
            return await handler(event, data)

        miss = await missing_channels(data["bot"], user.id)
        if not miss:
            return await handler(event, data)

        text = "❗️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling, so'ng «Tekshirish» tugmasini bosing:"
        if isinstance(event, CallbackQuery):
            await event.answer("Avval kanallarga a'zo bo'ling!", show_alert=True)
            await event.message.answer(text, reply_markup=sub_kb(miss))
        else:
            await event.answer(text, reply_markup=sub_kb(miss))
