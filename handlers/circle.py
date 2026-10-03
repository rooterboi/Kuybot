import os
import re
import shutil
import tempfile

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, Message

from config import MAX_DOWNLOAD_TG
from utils import downloader as dl
from utils.ff import ffmpeg

router = Router()


class Circle(StatesGroup):
    wait = State()


async def to_circle(src: str, dst: str):
    await ffmpeg(
        "-i", src, "-t", "60",
        "-vf", "crop='min(iw,ih)':'min(iw,ih)',scale=640:640,setsar=1",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", dst)


def _media(m: Message):
    if m is None:
        return None
    if m.video:
        return m.video
    if m.animation:
        return m.animation
    if m.document and (m.document.mime_type or "").startswith("video"):
        return m.document
    return None


async def circle_from_message(msg: Message, src: Message, state: FSMContext = None):
    media = _media(src)
    if not media:
        return await msg.answer("❌ Video topilmadi.")
    if media.file_size and media.file_size > MAX_DOWNLOAD_TG:
        return await msg.answer("⚠️ Video 20MB dan katta. Kichikroq video yuboring.")
    status = await msg.answer("⏳ Dumaloq video tayyorlanmoqda...")
    tmp = tempfile.mkdtemp(prefix="circle_")
    try:
        inp, out = os.path.join(tmp, "in.mp4"), os.path.join(tmp, "out.mp4")
        await msg.bot.download(media.file_id, destination=inp)
        await to_circle(inp, out)
        await msg.bot.send_video_note(msg.chat.id, FSInputFile(out))
    except Exception as e:
        await msg.answer("❌ Videoni qayta ishlab bo'lmadi.")
        print("CIRCLE ERROR:", e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if state:
            await state.clear()
        try:
            await status.delete()
        except Exception:
            pass


@router.message(F.caption.startswith("/dumaloq"), F.video | F.animation | F.document)
async def caption_cmd(m: Message):
    await circle_from_message(m, m)


@router.message(Command("dumaloq"))
async def cmd(m: Message, state: FSMContext):
    if _media(m.reply_to_message):
        return await circle_from_message(m, m.reply_to_message)
    await state.set_state(Circle.wait)
    await m.answer("⭕️ Dumaloq qilish uchun video yuboring (60 soniyagacha) yoki Instagram/TikTok havolasini yuboring.\n\nBekor: /cancel")


@router.message(Circle.wait, F.video | F.animation | F.document)
async def got_video(m: Message, state: FSMContext):
    await circle_from_message(m, m, state)


@router.message(Circle.wait, F.text)
async def got_link(m: Message, state: FSMContext):
    link = re.search(r"https?://\S+", m.text or "")
    if not link:
        return await m.answer("Video yoki havola yuboring. Bekor: /cancel")
    status = await m.answer("⏳ Yuklanmoqda...")
    tmp = tempfile.mkdtemp(prefix="circle_")
    try:
        info = await dl.download(link.group(0), tmp, audio=False)
        out = os.path.join(tmp, "circle.mp4")
        await to_circle(info["path"], out)
        await m.bot.send_video_note(m.chat.id, FSInputFile(out))
    except Exception as e:
        await m.answer("❌ Videoni olib bo'lmadi.")
        print("CIRCLE LINK ERROR:", e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        await state.clear()
        try:
            await status.delete()
        except Exception:
            pass
