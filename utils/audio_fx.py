import os

from utils.ff import ffmpeg

FILTERS = {
    "8d": "aformat=channel_layouts=stereo,apulsator=hz=0.15,aecho=0.8:0.7:20:0.2",
    "hall": "aecho=0.8:0.9:1000|1800:0.3|0.25",
    "slow": "aresample=44100,asetrate=44100*0.85,aresample=44100,aecho=0.8:0.85:70:0.35",
    "minus": "aformat=channel_layouts=stereo,pan=stereo|c0=c0-c1|c1=c1-c0",
}
NAMES = {"8d": "8D", "hall": "Concert Hall", "slow": "Slowed+Reverb", "minus": "Minus"}


async def apply(kind: str, src: str, dst: str):
    await ffmpeg("-i", src, "-vn", "-af", FILTERS[kind], "-c:a", "libmp3lame", "-b:a", "192k", dst)
    if not os.path.exists(dst):
        raise RuntimeError("fayl yaratilmadi")
