import asyncio
import glob
import os
import tempfile

import yt_dlp

from config import COOKIES_FILE, MAX_UPLOAD
from utils.ff import ffmpeg


def _base(outdir: str) -> dict:
    o = {
        "quiet": True, "no_warnings": True, "noplaylist": True,
        "outtmpl": os.path.join(outdir, "%(id)s.%(ext)s"),
        "socket_timeout": 30, "retries": 3,
    }
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        o["cookiefile"] = COOKIES_FILE
    return o


def _search(q: str, n: int, prefix: str):
    opts = {**_base(tempfile.gettempdir()), "extract_flat": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"{prefix}{n}:{q}", download=False)
    res = []
    for e in (info or {}).get("entries") or []:
        if not e:
            continue
        url = e.get("url") or e.get("webpage_url")
        if e.get("id") and (not url or not str(url).startswith("http")):
            url = f"https://www.youtube.com/watch?v={e['id']}"
        if url:
            res.append({"title": e.get("title") or "Noma'lum", "duration": e.get("duration"), "url": url})
    return res


async def search(q: str, n: int = 8):
    for prefix in ("ytsearch", "scsearch"):
        try:
            r = await asyncio.to_thread(_search, q, n, prefix)
        except Exception:
            r = []
        if r:
            return r
    return []


def _download(url: str, outdir: str, audio: bool) -> dict:
    opts = _base(outdir)
    if audio:
        opts.update(
            format="bestaudio/best",
            postprocessors=[{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        )
    else:
        opts.update(
            format="bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/bv*[height<=720]+ba/b",
            merge_output_format="mp4",
        )
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
    if info and info.get("entries"):
        info = info["entries"][0]
    files = [f for f in glob.glob(os.path.join(outdir, "*")) if not f.endswith((".part", ".ytdl"))]
    if audio:
        files = [f for f in files if f.endswith(".mp3")] or files
    if not files:
        raise RuntimeError("Fayl topilmadi")
    path = max(files, key=os.path.getsize)
    return {
        "path": path, "title": info.get("title") or "Audio",
        "uploader": info.get("uploader") or info.get("channel") or "",
        "duration": int(info.get("duration") or 0),
    }


async def download(url: str, outdir: str, audio: bool = False) -> dict:
    return await asyncio.to_thread(_download, url, outdir, audio)


async def to_mp3(video_path: str, outdir: str) -> str:
    dst = os.path.join(outdir, "audio.mp3")
    await ffmpeg("-i", video_path, "-vn", "-c:a", "libmp3lame", "-b:a", "192k", dst)
    return dst


AUDIO_EXT = (".mp3", ".m4a", ".opus", ".ogg", ".wav", ".aac", ".flac")


def too_big(path: str) -> bool:
    return os.path.getsize(path) > MAX_UPLOAD
