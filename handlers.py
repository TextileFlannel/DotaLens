import json

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import STRATZ_TOKEN, STEAM_API_KEY
from keyboard import *
from graphql_queries import *
import aiohttp
import re
from datetime import datetime

router = Router()

user_data = {}
items = {}

async def make_graphql_request(query: str, variables: dict):
    url = "https://api.stratz.com/graphql"
    headers = {
        "Authorization": f"Bearer {STRATZ_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "STRATZ_API"
    }

    payload = {
        "query": query,
        "variables": variables
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            print(response)
            return await response.json()


async def get_steam_id_from_url(profile_url: str) -> str:
    # Проверяем, является ли ссылка прямой с SteamID64
    if "/profiles/" in profile_url:
        # Извлекаем SteamID64 из ссылки
        steam_id = re.search(r"/profiles/(\d+)", profile_url)
        if steam_id:
            return str(int(steam_id.group(1)) - 76561197960265728)

    # Если это пользовательский URL, используем Steam API для получения SteamID64
    if "/id/" in profile_url:
        # Извлекаем username из ссылки
        username = re.search(r"/id/([^/]+)", profile_url)
        if username:
            username = username.group(1)
            # Используем Steam API для получения SteamID64
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={STEAM_API_KEY}&vanityurl={username}") as response:
                    data = await response.json()
                    if data.get("response", {}).get("success") == 1:
                        return str(int(data["response"]["steamid"]) - 76561197960265728)

    return None


async def validate_steam_id(steam_id: str) -> bool:
    try:
        response = await make_graphql_request(
            VALIDATE_STEAM_ID_QUERY,
            {"steamId": int(steam_id)}
        )
        return response.get('data', {}).get('player', {}).get('steamAccount') is not None
    except:
        return False


@router.message(Command("start"))
async def start(message: Message):
    global items, user_data
    user_data[message.from_user.id] = None
    if not items:
        with open('items.json', 'r') as f:
            items = json.load(f)
    await message.answer(
        "Привет! Я бот для отслеживания статистики Dota 2.\n"
        "Отправь мне ссылку на твой Steam профиль (например, https://steamcommunity.com/id/Young_Flexe или https://steamcommunity.com/profiles/76561198875033785):"
    )


@router.message(Command("info"))
async def info(message: Message):
    await message.answer(
        "ℹ️ Информация о боте:\n\n"
        "Основные команды:\n"
        "/start - Запустить бота\n"
        "/info - Информация о боте\n\n"
        "Бот использует STRATZ API для получения статистики Dota 2."
    )


@router.message(F.text)
async def process_steam_url(message: Message):
    # Проверяем, является ли сообщение ссылкой
    if not re.match(r"https?://steamcommunity\.com/(profiles/\d+|id/\w+)", message.text):
        await message.answer("Это не похоже на ссылку на Steam профиль. Попробуй ещё раз.")
        return

    # Извлекаем SteamID64 из ссылки
    steam_id = await get_steam_id_from_url(message.text)
    if not steam_id:
        await message.answer("Не удалось извлечь Steam ID из ссылки. Проверь ссылку и попробуй ещё раз.")
        return

    # Проверяем валидность Steam ID через STRATZ API
    if await validate_steam_id(steam_id):
        user_data[message.from_user.id] = steam_id
        await message.answer("Авторизация успешна!", reply_markup=main_menu())
    else:
        await message.answer("Неверный Steam ID. Попробуй ещё раз.")


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    try:
        steam_id = user_data.get(callback.from_user.id)

        response = await make_graphql_request(
            PROFILE_QUERY,
            {"steamId": int(steam_id)}
        )
        data = response.get('data', {}).get('player', {})
        if not data:
            return await callback.message.edit_text("Данные не найдены")

        steam_account = data.get('steamAccount', {})
        name = steam_account.get('name', 'Неизвестно')
        mas = ["Рекрут", "Страж", "Рыцарь", "Герой", "Легенда", "Властелин", "Божество", "Титан"]
        mmr = steam_account.get('seasonRank', 'Неизвестно')
        avatar = steam_account.get('avatar', None)
        if avatar == 'https://avatars.steamstatic.com/0000000000000000000000000000000000000000_full.jpg' or avatar == None:
            avatar = 'https://avatars.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg'
        matches = data.get('matchCount', 0)
        wins = data.get('winCount', 0)
        behavior = data.get('behaviorScore', 'Неизвестно')
        if mmr != None:
            rank = f"{mas[mmr // 10 - 1]} {['I', 'II', 'III', 'IV', 'V'][mmr % 10 - 1]}" if mmr < 75 else "Immortal"
        else:
            rank = None

        text = (
            f"👤 Профиль игрока:\n"
            f"├ Имя: {name}\n"
            f"├ Звание: {rank}\n"
            f"├ Сыграно матчей: {matches}\n"
            f"├ Побед: {wins}\n"
            f"└ Behavior Score: {behavior}"
        )
        await callback.message.delete()

        await callback.message.answer_photo(
            photo=avatar,
            caption=text,
            reply_markup=back_button()
        )
    except Exception as e:
        await callback.message.delete()
        await callback.message.edit_text(
            "Ошибка получения данных",
            reply_markup=back_button()
        )
    finally:
        await callback.answer()


@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ Настройки",
        reply_markup=settings_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "change_steam_id")
async def change_steam_id(callback: CallbackQuery):
    await callback.message.edit_text(
        "Введи новый Steam ID:",
        reply_markup=back_button()
    )
    await callback.answer()


@router.callback_query(F.data == "back")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.delete()

    await callback.message.answer(
        "Главное меню",
        reply_markup=main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "stats")
async def show_stats_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 Статистика",
        reply_markup=stats_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "match_history")
async def show_match_history(callback: CallbackQuery):
    try:
        steam_id = user_data.get(callback.from_user.id)
        response = await make_graphql_request(
            MATCH_HISTORY_QUERY,
            {"steamId": int(steam_id), "take": 6}
        )

        matches = response.get('data', {}).get('player', {}).get('matches', [])
        if not matches:
            return await callback.message.edit_text(
                "История матчей не найдена",
                reply_markup=back_button()
            )

        text = "📜 Последние 6 матчей:\n\n"
        ids = []
        for match in matches:
            player = next((p for p in match['players']), None)
            if not player:
                continue

            ids.append(match['id'])
            result = "Победа" if player['isVictory'] else "Поражение"
            duration = f"{divmod(match['durationSeconds'], 60)[0]}:{divmod(match['durationSeconds'], 60)[1]:02}"
            date = datetime.fromtimestamp(match['startDateTime'])

            text += (
                f"🕒 {date}\n"
                f"🧙‍♂️ Герой: {player['hero']['displayName']}\n"
                f"⚔️ K/D/A: {player['kills']}/{player['deaths']}/{player['assists']}\n"
                f"⏱ Длительность: {duration}\n"
                f"🏆 Результат: {result}\n"
                f"🆔 {match['id']}\n"
                f"──────────────────\n"
            )
        await callback.message.edit_text(
            text,
            reply_markup=list_back(ids)
        )
    except Exception as e:
        await callback.message.edit_text(
            "Ошибка получения истории матчей",
            reply_markup=back_button()
        )
    finally:
        await callback.answer()


@router.callback_query(F.data == "last_match")
async def show_last_match(callback: CallbackQuery):
    try:
        steam_id = user_data.get(callback.from_user.id)
        response = await make_graphql_request(
            LAST_MATCH_QUERY,
            {"steamId": int(steam_id)}
        )

        match = response.get('data', {}).get('player', {}).get('matches', [])
        if not match:
            return await callback.message.edit_text(
                "Последний матч не найден",
                reply_markup=back_button()
            )

        match = match[0]
        player = next((p for p in match['players']), None)
        if not player:
            return await callback.message.edit_text(
                "Данные игрока не найдены",
                reply_markup=back_button()
            )

        result = "Победа" if player['isVictory'] else "Поражение"
        duration = f"{divmod(match['durationSeconds'], 60)[0]}:{divmod(match['durationSeconds'], 60)[1]:02}"
        date = datetime.fromtimestamp(match['startDateTime'])
        hero = player['hero']
        hero_name = hero['displayName']
        hero_image = f"https://cdn.stratz.com/images/dota2/heroes/{hero['shortName']}_horz.png"
        it = [items[str(player[f'item{i}Id'])] for i in range(6) if player[f'item{i}Id']] + [items[str(player[f'backpack{i}Id'])] for i in range(3) if player[f'backpack{i}Id']]
        items_text = ' | '.join(it) if it else 'Нет данных'

        text = (
            f"🎮 Последний матч:\n\n"
            f"🕒 Дата: {date}\n"
            f"⏱ Длительность: {duration}\n"
            f"🏆 Результат: {result}\n\n"
            f"🌕{sum(match['radiantKills'])}⚔️{sum(match['direKills'])}🌑\n"
            f"🧙‍♂️ Герой: {hero_name}\n"
            f"⬆️ Уровень: {player['level']}\n"
            f"⚔️ K/D/A: {player['kills']}/{player['deaths']}/{player['assists']}\n"
            f"🟢 Добивания: {player['numLastHits']}\n"
            f"🔴 Не отдано: {player['numDenies']}\n"
            f"💎 Ценность: {player['networth']}\n"
            f"💰 GPM: {player['goldPerMinute']}\n"
            f"📈 XPM: {player['experiencePerMinute']}\n"
            f"💥 Урон: {player['heroDamage']}\n\n"
            f"🎒 Предметы:\n {items_text}\n\n"
            f"🆔 {match['id']}"
        )
        await callback.message.delete()

        await callback.message.answer_photo(
            photo=hero_image,
            caption=text,
            reply_markup=match_back(match['id'])
        )
    except Exception as e:
        await callback.message.delete()
        await callback.message.edit_text(
            "Ошибка получения данных о последнем матче",
            reply_markup=back_button()
        )
    finally:
        await callback.answer()



@router.callback_query(F.data.startswith("match_id:"))
async def show_match_ids(callback: CallbackQuery):
    try:
        _, id = callback.data.split(":")
        steam_id = user_data.get(callback.from_user.id)
        response = await make_graphql_request(
            MATCH_ID_QUERY,
            {"steamId": int(steam_id), "matchId": int(id)}
        )

        match = response.get('data', {}).get('player', {}).get('matches', [])
        if not match:
            return await callback.message.edit_text(
                "Матч не найден",
                reply_markup=back_button()
            )

        match = match[0]
        player = next((p for p in match['players']), None)
        if not player:
            return await callback.message.edit_text(
                "Данные игрока не найдены",
                reply_markup=back_button()
            )

        result = "Победа" if player['isVictory'] else "Поражение"
        duration = f"{divmod(match['durationSeconds'], 60)[0]}:{divmod(match['durationSeconds'], 60)[1]:02}"
        date = datetime.fromtimestamp(match['startDateTime'])
        hero = player['hero']
        hero_name = hero['displayName']
        hero_image = f"https://cdn.stratz.com/images/dota2/heroes/{hero['shortName']}_horz.png"
        it = [items[str(player[f'item{i}Id'])] for i in range(6) if player[f'item{i}Id']] + [items[str(player[f'backpack{i}Id'])] for i in range(3) if player[f'backpack{i}Id']]
        items_text = ' | '.join(it) if it else 'Нет данных'

        text = (
            f"🎮 Статистика матча:\n\n"
            f"🕒 Дата: {date}\n"
            f"⏱ Длительность: {duration}\n"
            f"🏆 Результат: {result}\n\n"
            f"🌕{sum(match['radiantKills'])}⚔️{sum(match['direKills'])}🌑\n"
            f"🧙‍♂️ Герой: {hero_name}\n"
            f"⬆️ Уровень: {player['level']}\n"
            f"⚔️ K/D/A: {player['kills']}/{player['deaths']}/{player['assists']}\n"
            f"🟢 Добивания: {player['numLastHits']}\n"
            f"🔴 Не отдано: {player['numDenies']}\n"
            f"💎 Ценность: {player['networth']}\n"
            f"💰 GPM: {player['goldPerMinute']}\n"
            f"📈 XPM: {player['experiencePerMinute']}\n"
            f"💥 Урон: {player['heroDamage']}\n\n"
            f"🎒 Предметы:\n {items_text}\n\n"
            f"🆔 {match['id']}"
        )
        await callback.message.delete()

        await callback.message.answer_photo(
            photo=hero_image,
            caption=text,
            reply_markup=match_back(match['id'])
        )
    except Exception as e:
        await callback.message.delete()
        await callback.message.edit_text(
            "Ошибка получения данных о матче",
            reply_markup=back_button()
        )
    finally:
        await callback.answer()