from aiogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M


def fx_kb():
    return M(inline_keyboard=[
        [B(text="🎧 8D", callback_data="fx:8d"), B(text="🏟 Concert Hall", callback_data="fx:hall")],
        [B(text="🐢 Slowed", callback_data="fx:slow"), B(text="🎤 Minus", callback_data="fx:minus")],
    ])


def search_kb(items):
    """items: [(token, label)]"""
    return M(inline_keyboard=[[B(text=l[:60], callback_data=f"dl:{t}")] for t, l in items])


def sub_kb(channels):
    rows = [[B(text=f"➕ {c['title']}", url=c["link"])] for c in channels if c.get("link")]
    rows.append([B(text="✅ Tekshirish", callback_data="check_sub")])
    return M(inline_keyboard=rows)


def admin_menu():
    return M(inline_keyboard=[
        [B(text="📊 Statistika", callback_data="adm:stats")],
        [B(text="📢 Reklama yuborish", callback_data="adm:bc")],
        [B(text="🔗 Majburiy obuna", callback_data="adm:ch")],
        [B(text="🎬 Kino bazasi", callback_data="kino:menu")],
    ])


def back_admin():
    return M(inline_keyboard=[[B(text="⬅️ Admin panel", callback_data="adm:menu")]])


def kino_menu():
    return M(inline_keyboard=[
        [B(text="➕ Kino qo'shish", callback_data="kino:add")],
        [B(text="🔎 Kod bo'yicha qidirish", callback_data="kino:find"),
         B(text="🗑 Kino o'chirish", callback_data="kino:del")],
        [B(text="📋 Kinolar ro'yxati", callback_data="kino:list")],
        [B(text="🚪 Yopish", callback_data="kino:close")],
    ])
