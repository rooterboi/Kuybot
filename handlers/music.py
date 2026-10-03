import asyncio
import os
import re
import shutil
import tempfile
import uuid

from aiogram import F, Router
from aiogram.fsm.state import default_state
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, FSInputFile, Message

from keyboards.inline import fx_kb, search_kb
from utils import audio_fx, downloader as dl

router = Router()
URL_RE = re.compile(r"https?://\S+")
CACHE: dict[str, str] = {}
SEM = asyncio.Semaphore(3)


def _fmt(sec):
    return f" [{int(sec) // 60}:{int(sec) % 60:02d}]" if sec else ""


async def send_audio_file(msg: Message, path: str, info: dict):
    await msg.answer_audio(
        FSInputFile(path), title=info.get("title"), performer=info.get("uploader") or None,
        duration=info.get("duration") or None, reply_markup=fx_kb())


async def process_link(msg: Message, url: str):
    status = await msg.answer("⏳ Yuklanmoqda...")
    tmp = tempfile.mkdtemp(prefix="dl_")
    try:
        async with SEM:
            info = await dl.download(url, tmp, audio=False)
            path = info["path"]
            if path.lower().endswith(dl.AUDIO_EXT):
                if path.lower().endswith(".mp3"):
                    mp3 = path
                else:
                    mp3 = await dl.to_mp3(path, tmp)
            else:
                if dl.too_big(path):
                    await msg.answer("⚠️ Video 50MB dan katta, faqat audio yuboriladi.")
                else:
                    await msg.answer_video(FSInputFile(path), caption=f"🎬 {info['title'][:200]}",
                                           supports_streaming=True)
                mp3 = await dl.to_mp3(path, tmp)
            if dl.too_big(mp3):
                await msg.answer("⚠️ Audio fayl juda katta.")
            else:
                await send_audio_file(msg, mp3, info)
    except Exception as e:
        await msg.answer("❌ Yuklab bo'lmadi. Havola to'g'riligini tekshiring (yopiq/private bo'lishi mumkin).")
        print("DL ERROR:", e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        try:
            await status.delete()
        except Exception:
            pass


@router.message(StateFilter(default_state), F.text, ~F.text.startswith("/"))
async def on_text(m: Message):
    text = m.text.strip()
    link = URL_RE.search(text)
    if link:
        return await process_link(m, link.group(0))
    wait = await m.answer("🔎 Qidirilmoqda...")
    results = await dl.search(text, 8)
    try:
        await wait.delete()
    except Exception:
        pass
    if not results:
        return await m.answer("😕 Hech narsa topilmadi.")
    items, lines = [], []
    for i, r in enumerate(results, 1):
        tok = uuid.uuid4().hex[:10]
        CACHE[tok] = r["url"]
        items.append((tok, f"{i}. {r['title']}{_fmt(r['duration'])}"))
        lines.append(f"{i}. {r['title']}{_fmt(r['duration'])}")
    if len(CACHE) > 2000:
        for k in list(CACHE)[:1000]:
            CACHE.pop(k, None)
    await m.answer("🎵 Natijalar:\n\n" + "\n".join(lines), reply_markup=search_kb(items))


@router.callback_query(F.data.startswith("dl:"))
async def on_pick(c: CallbackQuery):
    url = CACHE.get(c.data[3:])
    if not url:
        return await c.answer("Qidiruv eskirgan, qaytadan yozing.", show_alert=True)
    await c.answer("⏳ Yuklanmoqda...")
    tmp = tempfile.mkdtemp(prefix="dl_")
    try:
        async with SEM:
            info = await dl.download(url, tmp, audio=True)
            if dl.too_big(info["path"]):
                return await c.message.answer("⚠️ Fayl juda katta.")
            await send_audio_file(c.message, info["path"], info)
    except Exception as e:
        await c.message.answer("❌ Yuklab bo'lmadi.")
        print("PICK ERROR:", e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@router.callback_query(F.data.startswith("fx:"))
async def on_fx(c: CallbackQuery):
    kind = c.data[3:]
    a = c.message.audio
    if kind not in audio_fx.FILTERS or not a:
        return await c.answer()
    if a.file_size and a.file_size > 20 * 1024 * 1024:
        return await c.answer("Fayl 20MB dan katta, qayta ishlab bo'lmaydi.", show_alert=True)
    await c.answer(f"⏳ {audio_fx.NAMES[kind]} qo'llanmoqda...")
    tmp = tempfile.mkdtemp(prefix="fx_")
    try:
        src, dst = os.path.join(tmp, "in.mp3"), os.path.join(tmp, "out.mp3")
        await c.bot.download(a.file_id, destination=src)
        async with SEM:
            await audio_fx.apply(kind, src, dst)
        base = a.title or "Audio"
        await c.message.answer_audio(
            FSInputFile(dst), title=f"{base} ({audio_fx.NAMES[kind]})"[:100],
            performer=a.performer, reply_markup=fx_kb())
    except Exception as e:
        await c.message.answer("❌ Effektni qo'llab bo'lmadi.")
        print("FX ERROR:", e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
