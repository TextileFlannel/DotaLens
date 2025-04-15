from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ]
    ])
    return keyboard


def back_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back")
        ]
    ])
    return keyboard


def settings_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔗 Изменить ссылку", callback_data="change_steam_id")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back")
        ]
    ])
    return keyboard


def stats_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📜 История матчей", callback_data="match_history"),
            InlineKeyboardButton(text="🎮 Последний матч", callback_data="last_match")
        ],
        [
            InlineKeyboardButton(text="📈 Мета по позициям", callback_data="meta"),
            InlineKeyboardButton(text="🏆 Лучшие герои", callback_data="top_heroes")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back")
        ]
    ])
    return keyboard


def match_back(id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="STRATZ", url=f"https://stratz.com/matches/{id}"),
            InlineKeyboardButton(text="DOTABUFF", url=f"https://dotabuff.com/matches/{id}"),
            InlineKeyboardButton(text="OpenDota", url=f"https://www.opendota.com/matches/{id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back")
        ]
    ])
    return keyboard


def list_back(id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data=f"match_id:{id[0]}"),
            InlineKeyboardButton(text="2", callback_data=f"match_id:{id[1]}"),
            InlineKeyboardButton(text="3", callback_data=f"match_id:{id[2]}")
        ],
        [
            InlineKeyboardButton(text="4", callback_data=f"match_id:{id[3]}"),
            InlineKeyboardButton(text="5", callback_data=f"match_id:{id[4]}"),
            InlineKeyboardButton(text="6", callback_data=f"match_id:{id[5]}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back")
        ]
    ])
    return keyboard
