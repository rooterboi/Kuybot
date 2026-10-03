from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import database.db as db
from config import ADMINS, KINO_CHANNEL_ID, SECRET_PIN
from keyboards.inline import kino_menu
from utils.texts import channel_post, movie_info

router = Router()


class Pin(StatesGroup):
    wait = State()


class Add(StatesGroup):
    video = State()
    title = State()
    year = State()
    quality = State()
    country = State()
    lang = State()
    genre = State()
    code = State()


class Find(StatesGroup):
    code = State()


class Del(StatesGroup):
    code = State()


async def allowed(uid: int) -> bool:
    return uid in ADMINS or await db.is_kino_admin(uid)


# ---------- yashirin buyruq ----------
@router.message(Command("creatorkodlikinobot"))
async def secret(m: Message, state: FSMContext):
    await state.set_state(Pin.wait)
    await m.answer("🔒 Kirish uchun raqamli kodni kiriting:")


@router.message(Pin.wait)
async def check_pin(m: Message, state: FSMContext):
    await state.clear()
    try:
        await m.delete()
    except Exception:
        pass
    if (m.text or "").strip() == SECRET_PIN:
        await db.add_kino_admin(m.from_user.id)
        await m.answer("✅ Kino Admin Paneli ochildi.", reply_markup=kino_menu())
    else:
        await m.answer("❌ Noto'g'ri kod. Menyu yopildi.")


@router.message(Command("kino"))
async def kino_cmd(m: Message):
    if await allowed(m.from_user.id):
        await m.answer("🎬 Kino Admin Paneli", reply_markup=kino_menu())


@router.callback_query(F.data == "kino:menu")
async def menu(c: CallbackQuery):
    if not await allowed(c.from_user.id):
        return await c.answer("Ruxsat yo'q", show_alert=True)
    await c.message.edit_text("🎬 Kino Admin Paneli", reply_markup=kino_menu())


@router.callback_query(F.data == "kino:close")
async def close(c: CallbackQuery):
    await c.message.delete()


# ---------- kino qo'shish ----------
@router.callback_query(F.data == "kino:add")
async def add_start(c: CallbackQuery, state: FSMContext):
    if not await allowed(c.from_user.id):
        return await c.answer("Ruxsat yo'q", show_alert=True)
    await state.set_state(Add.video)
    await c.message.answer("🎞 Kino videosini yuboring.\nBekor qilish: /cancel")
    await c.answer()


@router.message(Add.video, F.video | F.document)
async def add_video(m: Message, state: FSMContext):
    if m.video:
        fid, ftype = m.video.file_id, "video"
    else:
        fid, ftype = m.document.file_id, "document"
    await state.update_data(file_id=fid, ftype=ftype)
    await state.set_state(Add.title)
    await m.answer("🎬 Kino nomini kiriting:")


async def _step(m: Message, state: FSMContext, key: str, nxt, ask: str):
    if not m.text:
        return await m.answer("Matn yuboring.")
    await state.update_data(**{key: m.text.strip()})
    await state.set_state(nxt)
    await m.answer(ask)


@router.message(Add.title)
async def add_title(m: Message, state: FSMContext):
    await _step(m, state, "title", Add.year, "📅 Yilini kiriting (masalan: 2024):")


@router.message(Add.year)
async def add_year(m: Message, state: FSMContext):
    await _step(m, state, "year", Add.quality, "🖥 Sifatini kiriting (masalan: 1080p):")


@router.message(Add.quality)
async def add_quality(m: Message, state: FSMContext):
    await _step(m, state, "quality", Add.country, "🗽 Davlatini kiriting:")


@router.message(Add.country)
async def add_country(m: Message, state: FSMContext):
    await _step(m, state, "country", Add.lang, "🇺🇿 Tilini kiriting (masalan: O'zbek tilida):")


@router.message(Add.lang)
async def add_lang(m: Message, state: FSMContext):
    await _step(m, state, "lang", Add.genre, "🍿 Janrlarni vergul bilan kiriting (masalan: Jangari, Drama):")


@router.message(Add.genre)
async def add_genre(m: Message, state: FSMContext):
    nxt = await db.next_code()
    await _step(m, state, "genre", Add.code, f"🔢 Raqamli kodni kiriting (tavsiya: {nxt}):")


@router.message(Add.code)
async def add_code(m: Message, state: FSMContext):
    code = (m.text or "").strip()
    if not code.isdigit():
        return await m.answer("❌ Kod faqat raqamlardan iborat bo'lishi kerak.")
    if await db.get_movie(code):
        return await m.answer("❌ Bu kod band. Boshqa kod kiriting:")
    data = await state.get_data()
    data["code"] = code
    await state.clear()
    await db.add_movie(data)
    await m.answer(f"✅ Kino bazaga qo'shildi. Kod: {code}", reply_markup=kino_menu())

    if not KINO_CHANNEL_ID:
        return await m.answer("ℹ️ KINO_CHANNEL_ID sozlanmagan — kanalga post yuborilmadi.")
    me = await m.bot.get_me()
    chat = int(KINO_CHANNEL_ID) if KINO_CHANNEL_ID.lstrip("-").isdigit() else KINO_CHANNEL_ID
    try:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🎬 Botga o'tish", url=f"https://t.me/{me.username}")]])
        await m.bot.send_message(chat, channel_post(data, me.username), reply_markup=kb)
        await m.answer("📣 Kanalga post joylandi.")
    except Exception as e:
        await m.answer(f"⚠️ Kanalga post yuborib bo'lmadi: {e}\nBot kanalda admin ekanini tekshiring.")


# ---------- qidirish / o'chirish / ro'yxat ----------
@router.callback_query(F.data == "kino:find")
async def find_start(c: CallbackQuery, state: FSMContext):
    if not await allowed(c.from_user.id):
        return await c.answer("Ruxsat yo'q", show_alert=True)
    await state.set_state(Find.code)
    await c.message.answer("🔎 Kino kodini kiriting:")
    await c.answer()


@router.message(Find.code)
async def find_do(m: Message, state: FSMContext):
    await state.clear()
    mv = await db.get_movie((m.text or "").strip())
    if not mv:
        return await m.answer("❌ Topilmadi.", reply_markup=kino_menu())
    await send_movie(m, mv)
    await m.answer("🎬 Kino Admin Paneli", reply_markup=kino_menu())


@router.callback_query(F.data == "kino:del")
async def del_start(c: CallbackQuery, state: FSMContext):
    if not await allowed(c.from_user.id):
        return await c.answer("Ruxsat yo'q", show_alert=True)
    await state.set_state(Del.code)
    await c.message.answer("🗑 O'chiriladigan kino kodini kiriting:")
    await c.answer()


@router.message(Del.code)
async def del_do(m: Message, state: FSMContext):
    await state.clear()
    ok = await db.del_movie((m.text or "").strip())
    await m.answer("✅ O'chirildi." if ok else "❌ Bunday kod yo'q.", reply_markup=kino_menu())


@router.callback_query(F.data == "kino:list")
async def list_movies(c: CallbackQuery):
    if not await allowed(c.from_user.id):
        return await c.answer("Ruxsat yo'q", show_alert=True)
    rows = await db.list_movies(40)
    text = "📋 Oxirgi kinolar:\n\n" + ("\n".join(f"{r['code']} — {r['title']} ({r['year']})" for r in rows) or "Bo'sh")
    await c.message.answer(text)
    await c.answer()


# ---------- foydalanuvchi: kod yuborish ----------
async def send_movie(m: Message, mv: dict):
    me = await m.bot.get_me()
    cap = movie_info(mv) + f"\n\n🤖 @{me.username}"
    if mv["ftype"] == "document":
        await m.answer_document(mv["file_id"], caption=cap)
    else:
        await m.answer_video(mv["file_id"], caption=cap)


@router.message(StateFilter(default_state), F.text.regexp(r"^\s*\d+\s*$"))
async def by_code(m: Message):
    mv = await db.get_movie(m.text.strip())
    if not mv:
        return await m.answer("❌ Bunday kodli kino topilmadi.")
    await send_movie(m, mv)
