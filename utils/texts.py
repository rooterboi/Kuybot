import re


def hashtags(genre: str) -> str:
    parts = [g.strip().replace(" ", "_") for g in re.split(r"[,#]+", genre) if g.strip()]
    return " ".join("#" + re.sub(r"[^\w]", "", p) for p in parts)


def movie_info(m: dict) -> str:
    return (
        f"🎬 {m['title']}\n"
        f"📅 Yili: {m['year']}\n"
        f"🖥 Sifati: {m['quality']}\n"
        f"🗽 Davlati: {m['country']}\n"
        f"🇺🇿 Tili: {m['lang']}\n"
        f"🍿 Janri: {hashtags(m['genre'])}"
    )


def channel_post(m: dict, bot_username: str) -> str:
    return (
        movie_info(m)
        + f"\n\n✅ Filmni ko'rish uchun << {m['code']} ⬆️ kodini @{bot_username} ga yuboring 🍿"
    )
