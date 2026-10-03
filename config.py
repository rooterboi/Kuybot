import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMINS = [int(x) for x in os.getenv("ADMINS", "").replace(" ", "").split(",") if x.isdigit()]
SECRET_PIN = os.getenv("SECRET_PIN", "0009")
KINO_CHANNEL_ID = os.getenv("KINO_CHANNEL_ID", "").strip()
DB_PATH = os.getenv("DB_PATH", "data/bot.db")
PORT = int(os.getenv("PORT", "10000"))
COOKIES_FILE = os.getenv("COOKIES_FILE", "").strip()
MAX_UPLOAD = 49 * 1024 * 1024      # Bot API yuklash limiti ~50MB
MAX_DOWNLOAD_TG = 20 * 1024 * 1024  # Bot API yuklab olish limiti 20MB
