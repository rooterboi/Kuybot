from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.inline import sub_kb
from utils.subscription import missing_channels

router = Router()


@router.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(
        "👋 Salom!\n\n"
        "🎵 Menga Instagram, TikTok, YouTube va boshqa tarmoqlardan havola yuboring — "
        "video va MP3 qilib beraman.\n"
        "🔎 Yoki musiqa/qo'shiq nomini yozing.\n"
        "⭕️ /dumaloq — videoni dumaloq (video-note) qilish.\n"
        "🎬 Kino ko'rish uchun kino kodini yuboring."
    )


@router.message(Command("cancel"), StateFilter("*"))
async def cancel(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("❎ Bekor qilindi.")


@router.callback_query(F.data == "check_sub")
async def check_sub(c: CallbackQuery):
    miss = await missing_channels(c.bot, c.from_user.id)
    if miss:
        await c.answer("❌ Hali hamma kanalga a'zo bo'lmadingiz!", show_alert=True)
        try:
            await c.message.edit_reply_markup(reply_markup=sub_kb(miss))
        except Exception:
            pass
        return
    await c.answer("✅ Rahmat!")
    try:
        await c.message.delete()
    except Exception:
        pass
    await c.message.answer("✅ Obuna tasdiqlandi. Link yuboring yoki musiqa nomini yozing.")
