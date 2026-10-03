import asyncio

from aiogram import F, Router
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton as B, InlineKeyboardMarkup as M, Message

import database.db as db
from config import ADMINS
from keyboards.inline import admin_menu, back_admin

router = Router()
router.message.filter(F.from_user.id.in_(set(ADMINS)))
router.callback_query.filter(F.from_user.id.in_(set(ADMINS)))
BG: set = set()


class Ch(StatesGroup):
    wait = State()


class Bc(StatesGroup):
    msg = State()
    btn = State()
    confirm = State()


@router.message(Command("admin"))
async def admin_cmd(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("👨‍💻 Admin panel", reply_markup=admin_menu())


@router.callback_query(F.data == "adm:menu")
async def admin_back(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.edit_text("👨‍💻 Admin panel", reply_markup=admin_menu())


@router.callback_query(F.data == "adm:stats")
async def stats(c: CallbackQuery):
    s = await db.stats()
    await c.message.edit_text(
        "📊 Statistika\n\n"
        f"👥 Jami foydalanuvchilar: {s['total']}\n"
        f"🆕 Bugun qo'shilgan: {s['new_today']}\n"
        f"🔥 Bugungi faol: {s['active_today']}\n"
        f"📅 7 kunlik faol: {s['active_week']}\n"
        f"🎬 Kinolar soni: {s['movies']}\n"
        f"🔗 Majburiy kanallar: {s['channels']}",
        reply_markup=back_admin())


# ---------- majburiy obuna ----------
async def _channels_view(target: Message, edit: bool):
    chs = await db.get_channels()
    rows = [[B(text=f"❌ {c['title']}", callback_data=f"ch:del:{c['chat_id']}")] for c in chs]
    rows.append([B(text="➕ Kanal qo'shish", callback_data="ch:add")])
    rows.append([B(text="⬅️ Admin panel", callback_data="adm:menu")])
    text = "🔗 Majburiy obuna kanallari" + ("" if chs else "\n\nHozircha kanal yo'q.") + "\n(❌ bosilsa o'chiriladi)"
    kb = M(inline_keyboard=rows)
    if edit:
        await target.edit_text(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)


@router.callback_query(F.data == "adm:ch")
async def ch_menu(c: CallbackQuery):
    await _channels_view(c.message, True)


@router.callback_query(F.data.startswith("ch:del:"))
async def ch_del(c: CallbackQuery):
    await db.del_channel(c.data[7:])
    await c.answer("O'chirildi")
    await _channels_view(c.message, True)


@router.callback_query(F.data == "ch:add")
async def ch_add(c: CallbackQuery, state: FSMContext):
    await state.set_state(Ch.wait)
    await c.message.answer(
        "Kanal @username yoki ID sini yuboring (bot kanalda admin bo'lishi shart).\n"
        "Maxfiy kanal uchun: <ID> <invite havola>\nMasalan: -1001234567890 https://t.me/+abc\n\nBekor: /cancel")
    await c.answer()


@router.message(Ch.wait, F.text)
async def ch_save(m: Message, state: FSMContext):
    parts = m.text.strip().split()
    ident = parts[0]
    link = parts[1] if len(parts) > 1 else None
    try:
        chat = await m.bot.get_chat(int(ident) if ident.lstrip("-").isdigit() else ident)
        me = await m.bot.get_chat_member(chat.id, m.bot.id)
        if me.status not in ("administrator", "creator"):
            return await m.answer("❌ Bot bu kanalda admin emas. Admin qiling va qayta yuboring.")
        if not link:
            if chat.username:
                link = f"https://t.me/{chat.username}"
            else:
                link = chat.invite_link or await m.bot.export_chat_invite_link(chat.id)
    except Exception as e:
        return await m.answer(f"❌ Xato: {e}")
    await db.add_channel(chat.id, chat.title or ident, link)
    await state.clear()
    await m.answer(f"✅ Qo'shildi: {chat.title}")
    await _channels_view(m, False)


# ---------- reklama ----------
@router.callback_query(F.data == "adm:bc")
async def bc_start(c: CallbackQuery, state: FSMContext):
    await state.set_state(Bc.msg)
    await c.message.answer("📢 Reklama xabarini yuboring (matn, rasm, video yoki boshqa kanaldan forward).\nBekor: /cancel")
    await c.answer()


@router.message(Bc.msg)
async def bc_msg(m: Message, state: FSMContext):
    await state.update_data(chat=m.chat.id, mid=m.message_id)
    await state.set_state(Bc.btn)
    await m.answer("🔘 Tugma qo'shasizmi? Har qatorga bittadan:\nMatn - https://havola\n\nTugma kerak bo'lmasa «-» yuboring.")


@router.message(Bc.btn, F.text)
async def bc_btn(m: Message, state: FSMContext):
    rows = []
    if m.text.strip() != "-":
        for line in m.text.splitlines():
            if " - " in line:
                t, u = line.split(" - ", 1)
                if u.strip().startswith(("http://", "https://", "tg://")):
                    rows.append([t.strip(), u.strip()])
    await state.update_data(btns=rows)
    d = await state.get_data()
    kb = M(inline_keyboard=[[B(text=t, url=u)] for t, u in rows]) if rows else None
    await m.answer("👁 Ko'rinishi:")
    await m.bot.copy_message(m.chat.id, d["chat"], d["mid"], reply_markup=kb)
    await state.set_state(Bc.confirm)
    await m.answer("Qanday yuboramiz?", reply_markup=M(inline_keyboard=[
        [B(text="📨 Nusxa (tugma bilan)", callback_data="bc:copy")],
        [B(text="↪️ Forward (tugmasiz)", callback_data="bc:fwd")],
        [B(text="❌ Bekor", callback_data="bc:cancel")]]))


async def _send(bot, uid, chat, mid, mode, kb):
    for _ in range(2):
        try:
            if mode == "fwd":
                await bot.forward_message(uid, chat, mid)
            else:
                await bot.copy_message(uid, chat, mid, reply_markup=kb)
            return True
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except Exception:
            return False
    return False


async def _broadcast(bot, admin_id, chat, mid, mode, kb):
    ok = fail = 0
    for uid in await db.all_user_ids():
        if await _send(bot, uid, chat, mid, mode, kb):
            ok += 1
        else:
            fail += 1
        await asyncio.sleep(0.04)
    await bot.send_message(admin_id, f"✅ Reklama tugadi\n\n📨 Yuborildi: {ok}\n🚫 Xato: {fail}")


@router.callback_query(Bc.confirm, F.data.in_({"bc:copy", "bc:fwd", "bc:cancel"}))
async def bc_go(c: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    await state.clear()
    await c.message.delete()
    if c.data == "bc:cancel":
        return await c.message.answer("❎ Bekor qilindi.")
    kb = M(inline_keyboard=[[B(text=t, url=u)] for t, u in d.get("btns", [])]) if d.get("btns") else None
    mode = "fwd" if c.data == "bc:fwd" else "copy"
    await c.message.answer("🚀 Yuborish boshlandi...")
    task = asyncio.create_task(_broadcast(c.bot, c.from_user.id, d["chat"], d["mid"], mode, kb))
    BG.add(task)
    task.add_done_callback(BG.discard)
