# 2-in-1 Telegram bot: Musiqa/Downloader + Yashirin Kodli Kino

## Imkoniyatlar
- Instagram/TikTok/YouTube/... havola -> video + MP3 (8D, Concert Hall, Slowed, Minus tugmalari)
- Nom bo'yicha qidiruv (YouTube, topilmasa SoundCloud)
- `/dumaloq` -> videoni dumaloq (video-note) qiladi
- Yashirin `/creatorkodlikinobot` (PIN: `SECRET_PIN`, default 0009) -> Kino admin paneli
- Kino qo'shilganda kanalga avtomatik post, foydalanuvchi kod yuborsa kino keladi
- Majburiy obuna, statistika, reklama (broadcast) - `/admin`

## Lokal ishga tushirish
1. `ffmpeg` o'rnating, `pip install -r requirements.txt`
2. `.env.example` -> `.env` ni to'ldiring
3. `python main.py`

## GitHub + Render
1. Papkani GitHub'ga push qiling.
2. Render -> New -> Web Service -> repo'ni tanlang -> Runtime: **Docker**.
3. Environment: `BOT_TOKEN`, `ADMINS`, `KINO_CHANNEL_ID`, `SECRET_PIN`, `DB_PATH`.
4. Deploy. Free planda 15 daqiqa so'rov bo'lmasa servis uxlaydi: UptimeRobot bilan
   `https://<app>.onrender.com/` ni har 5 daqiqada ping qiling.

## Muhim
- SQLite Render free planda qayta deploy'da o'chadi. Doimiy saqlash uchun Render Disk
  (`DB_PATH=/data/bot.db`, disk mount `/data`) ulang.
- Bot kino kanalida va majburiy obuna kanallarida **admin** bo'lishi kerak.
- Instagram ba'zan login talab qiladi: brauzerdan `cookies.txt` eksport qilib `COOKIES_FILE` ga yo'lini bering.
- Telegram Bot API limiti: yuborish 50MB, yuklab olish 20MB (effektlar/dumaloq uchun).
