import json
import random
from operator import itemgetter
import uuid
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from config import *
from database import get_user, create_or_update_user
from cache import cache
from keyboard import *
from graphql_queries import *
import aiohttp
import re
from datetime import datetime
import matplotlib.pyplot as plt
import io


router = Router()

items = {}
hero = {}


async def make_graphql_request(query: str, variables: dict):
    cache_key_data = json.dumps({"query": query, "variables": variables}, sort_keys=True)
    cache_key = f"stratz:{uuid.uuid5(uuid.NAMESPACE_URL, cache_key_data.encode('utf-8'))}"

    if cached := cache.get(cache_key):
        return json.loads(cached)

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
            data = await response.json()
            cache.set(cache_key, json.dumps(data), 3600)  # Кэш на 1 час
            return data


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
    global items
    if not items:
        with open('jsons/items.json', 'r') as f:
            items = json.load(f)

    user = get_user(message.from_user.id)
    if user:
        await message.answer("Вы уже авторизованы!", reply_markup=main_menu())
        return

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
    if not re.match(r"https?://steamcommunity\.com/(profiles/\d+|id/\w+)", message.text):
        await message.answer("Это не похоже на ссылку на Steam профиль. Попробуй ещё раз.")
        return

    steam_id = await get_steam_id_from_url(message.text)
    if not steam_id:
        await message.answer("Не удалось извлечь Steam ID из ссылки. Проверь ссылку и попробуй ещё раз.")
        return

    if await validate_steam_id(steam_id):
        create_or_update_user(message.from_user.id, steam_id)
        await message.answer("Авторизация успешна!", reply_markup=main_menu())
    else:
        await message.answer("Неверный Steam ID. Попробуй ещё раз.")


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    try:
        user = get_user(callback.from_user.id)

        steam_id = user[2]
        cache_key = f"profile:{steam_id}"

        if cached := cache.get(cache_key):
            response = json.loads(cached)
        else:
            response = await make_graphql_request(PROFILE_QUERY, {"steamId": int(steam_id)})
            cache.set(cache_key, json.dumps(response), 600)

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
            f"├ Процент побед: {wins / matches * 100:.2f}%\n"
            f"└ Порядочность: {behavior}"
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
        user = get_user(callback.from_user.id)

        steam_id = user[2]
        cache_key = f"match_history:{steam_id}"

        if cached := cache.get(cache_key):
            response = json.loads(cached)
        else:
            response = await make_graphql_request(MATCH_HISTORY_QUERY, {"steamId": int(steam_id), "take": 6})
            cache.set(cache_key, json.dumps(response), 300)  # 5 минут кэша

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
        user = get_user(callback.from_user.id)
        steam_id = user[2]
        cache_key = f"last_match:{steam_id}"

        if cached := cache.get(cache_key):
            response = json.loads(cached)
        else:
            response = await make_graphql_request(LAST_MATCH_QUERY, {"steamId": int(steam_id)})
            cache.set(cache_key, json.dumps(response), 300)

        match = response.get('data', {}).get('player', {}).get('matches', [])
        avg_stats = response.get('data', {}).get('heroStats', {}).get('stats', [])
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

        hero_id = player['hero']['id']
        data = analytics(match, avg_stats[hero_id - 1])

        result = "Победа" if player['isVictory'] else "Поражение"
        duration = f"{divmod(match['durationSeconds'], 60)[0]}:{divmod(match['durationSeconds'], 60)[1]:02}"
        date = datetime.fromtimestamp(match['startDateTime'])
        hero = player['hero']
        hero_name = hero['displayName']
        hero_image = f"https://cdn.stratz.com/images/dota2/heroes/{hero['shortName']}_horz.png"
        it = [items[str(player[f'item{i}Id'])] for i in range(6) if player[f'item{i}Id']] + [
            items[str(player[f'backpack{i}Id'])] for i in range(3) if player[f'backpack{i}Id']]
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
            f'🗿Среднее значение и отклонение от игроков:\n'
            f'KDA: {round((avg_stats[hero_id-1]['kills'] + avg_stats[hero_id-1]['assists']) / avg_stats[hero_id-1]['deaths'], 1)}({round(data[5][0], 1)}%)\n'
            f'GPM: {round(avg_stats[hero_id-1]['networth'] / avg_stats[hero_id-1]['time'], 1)}({round(data[5][2], 1)}%)\n'
            f'XPM: {round(avg_stats[hero_id-1]['xp'] / avg_stats[hero_id-1]['time'], 1)}({round(data[5][1], 1)}%)\n'
            f'Ценность: {round(avg_stats[hero_id-1]['networth'], 1)}({round(data[5][3], 1)}%)\n'
            f"🤖Итоговая оценка по версии DotaLens: {round(data[0], 1)} Score \n"
            #f"👾Итоговая оценка по версии Stratz:\nScore | {player['imp']} | "
        )

        if -40 >= player['imp']:
            text += f"Ужасное исполнение"
        elif -20 >= player['imp']:
            text += f"Очень слабое исполнение"
        elif -10 >= player['imp']:
            text += f"Слабое исполнение"
        elif 10 > player['imp']:
            text += f"Среднее исполнение"
        elif 20 > player['imp']:
            text += f"Хорошее исполнение"
        elif 40 > player['imp']:
            text += f"Очень хорошее исполнение"
        else:
            text += f"Превосходное исполнение"

        text += f'\n**(Средним исполнением является 0, учитывайте это!)\n\n'
        text += f"🆔 {match['id']}"

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
        user = get_user(callback.from_user.id)

        _, match_id = callback.data.split(":")
        cache_key = f"match:{match_id}"

        if cached := cache.get(cache_key):
            response = json.loads(cached)
        else:
            response = await make_graphql_request(MATCH_ID_QUERY, {"steamId": int(user[2]), "matchId": int(match_id)})
            cache.set(cache_key, json.dumps(response), 3600)

        match = response.get('data', {}).get('player', {}).get('matches', [])
        avg_stats = response.get('data', {}).get('heroStats', {}).get('stats', [])

        match = match[0]
        player = next((p for p in match['players']), None)
        if not player:
            return await callback.message.edit_text(
                "Данные игрока не найдены",
                reply_markup=back_button()
            )

        hero_id = player['hero']['id']
        data = analytics(match, avg_stats[hero_id - 1])

        result = "Победа" if player['isVictory'] else "Поражение"
        duration = f"{divmod(match['durationSeconds'], 60)[0]}:{divmod(match['durationSeconds'], 60)[1]:02}"
        date = datetime.fromtimestamp(match['startDateTime'])
        hero = player['hero']
        hero_name = hero['displayName']
        hero_image = f"https://cdn.stratz.com/images/dota2/heroes/{hero['shortName']}_horz.png"
        it = [items[str(player[f'item{i}Id'])] for i in range(6) if player[f'item{i}Id']] + [
            items[str(player[f'backpack{i}Id'])] for i in range(3) if player[f'backpack{i}Id']]
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
            f'🗿Среднее значение и отклонение от игроков:\n'
            f'KDA: {round((avg_stats[hero_id-1]['kills'] + avg_stats[hero_id-1]['assists']) / avg_stats[hero_id-1]['deaths'], 1)}({round(data[5][0], 1)}%)\n'
            f'GPM: {round(avg_stats[hero_id-1]['networth'] / avg_stats[hero_id-1]['time'], 1)}({round(data[5][2], 1)}%)\n'
            f'XPM: {round(avg_stats[hero_id-1]['xp'] / avg_stats[hero_id-1]['time'], 1)}({round(data[5][1], 1)}%)\n'
            f'Ценность: {round(avg_stats[hero_id-1]['networth'], 1)}({round(data[5][3], 1)}%)\n'
            f"🤖Итоговая оценка по версии DotaLens: {round(data[0], 1)} Score \n"
            #f"👾Итоговая оценка по версии Stratz:\nScore | {player['imp']} | "
        )

        if -40 >= player['imp']:
            text += f"Ужасное исполнение"
        elif -20 >= player['imp']:
            text += f"Очень слабое исполнение"
        elif -10 >= player['imp']:
            text += f"Слабое исполнение"
        elif 10 > player['imp']:
            text += f"Среднее исполнение"
        elif 20 > player['imp']:
            text += f"Хорошее исполнение"
        elif 40 > player['imp']:
            text += f"Очень хорошее исполнение"
        else:
            text += f"Превосходное исполнение"

        text += f'\n**(Средним исполнением является 0, учитывайте это!)\n\n'
        text += f"🆔 {match['id']}"

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


@router.callback_query(F.data == "meta")
async def show_meta(callback: CallbackQuery):
    try:
        response = await make_graphql_request(META_QUERY, {})
        heroes = response.get('data', {}).get('heroStats', {}).get('winMonth', [])

        if not heroes:
            return await callback.message.edit_text(
                "Данные меты не найдены",
                reply_markup=back_button()
            )

        win_rate = []
        for hero in heroes:
            win_rate.append({'id': str(hero['heroId']), 'winRate': hero['winCount'] / hero['matchCount']})

        win_rate = sorted(win_rate, key=itemgetter('winRate'), reverse=True)
        meta = {"Carry": [],
                "Initiator": [],
                "Escape": [],
                "Nuker": [],
                "Durable": [],
                "Disabler": [],
                "Pusher": [],
                "Support": []}

        with open('jsons/heroes.json', 'r') as f:
            file = json.load(f)
            for i in win_rate:
                id_ = i['id']
                win_ = i['winRate']
                roles = file[id_][2]
                for r in roles:
                    if r.capitalize() in meta:
                        meta[r.capitalize()].append({file[id_][1]: win_})
        text = '📊 Текущая мета по позициям:\n\n'
        medals = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
        for pos, h in meta.items():
            text += f'{chr(random.randint(0x1F600, 0x1F64F))}{pos}:\n'
            for i, val in enumerate(h[:5]):
                for k, v in val.items():
                    text += f'{medals[i]} {k} - {v * 100:.2f}%\n'
            text += '\n'

        await callback.message.delete()
        await callback.message.answer(
            text,
            reply_markup=back_button()
        )

    except Exception as e:
        await callback.message.delete()
        await callback.message.answer(
            "Ошибка получения данных меты",
            reply_markup=back_button()
        )
    finally:
        await callback.answer()


@router.callback_query(F.data == "top_heroes")
async def show_top_heroes(callback: CallbackQuery):
    try:
        user = get_user(callback.from_user.id)
        steam_id = user[2]
        cache_key = f"top_heroes:{steam_id}"

        take = 25
        if cached := cache.get(cache_key):
            response = json.loads(cached)
        else:
            response = await make_graphql_request(TOP_HEROES, {"steamId": int(steam_id), "take": take})
            cache.set(cache_key, json.dumps(response), 1800)

        matches = response.get('data', {}).get('player', {}).get('matches', [])
        avg_stats = response.get('data', {}).get('heroStats', {}).get('stats', [])

        win, kills, deaths, assists, scores = 0, 0, 0, 0, []
        with open('jsons/heroes.json', 'r') as f:
            file = json.load(f)
            for match in matches:
                hero_id = match['players'][0]['hero']['id']
                data = analytics(match, avg_stats[hero_id - 1])
                win += data[1]
                kills += data[2]
                deaths += data[3]
                assists += data[4]
                scores.append({'id': hero_id, 'score': data[0], 'shortName': file[str(hero_id)][0],
                               'displayName': file[str(hero_id)][1]})

        scores_sorted = sorted(scores, key=itemgetter('score'), reverse=True)

        text = ('Рейтинг (score) - это формула, основанная на тщательном расчёте эффективности героя в игре.\n\n'
                '✨Ваш Тирлист Героев\n\n'
                f'🥇{scores_sorted[0]["displayName"]} {round(scores_sorted[0]["score"], 1)}\n'
                f'🥈{scores_sorted[1]["displayName"]} {round(scores_sorted[1]["score"], 1)}\n'
                f'🥉{scores_sorted[2]["displayName"]} {round(scores_sorted[2]["score"], 1)}\n\n'
                f'🎮Было проанализировано {take} матчей.\n\n'
                f'📊Ваша общая статистика\n\n'
                f'🏆Процент побед: {round(win / take * 100, 1)}\n'
                f'⚔️KDA (K + A / D): {round((kills + assists) / deaths, 1)}\n'
                f'🗡️Среднее кол-во убийств: {round(kills / take, 1)}\n'
                f'☠️Среднее кол-во смертей: {round(deaths / take, 1)}\n'
                f'🤝Среднее кол-во ассистов: {round(assists / take, 1)}\n'
                f'📢Ваши показатели средние или ниже. Есть возможность улучшить свои результаты и стать более эффективным для команды.\n'
                )

        plot_buf = plot_graph(scores)
        photo = BufferedInputFile(
            plot_buf.getvalue(),
            filename="heroes_chart.png"
        )

        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=back_button()
        )
    except Exception as e:
        await callback.message.delete()
        await callback.message.answer(
            "Ошибка получения данных о героях",
            reply_markup=back_button()
        )
    finally:
        #plot_buf.close()
        await callback.answer()


def analytics(match: dict, stat: dict):
    match = match['players'][0]
    kda = (((match['kills'] + match['assists']) / match['deaths']) - (
            (stat['kills'] + stat['assists']) / stat['deaths']))
    xpm = (match['experiencePerMinute'] - stat['xp'] / stat['time']) / 100
    gpm = (match['goldPerMinute'] - stat['networth'] / stat['time']) / 100
    net = (match['networth'] - stat['networth']) / 3000

    kda_p = (((match['kills'] + match['assists']) / match['deaths']) - (
            (stat['kills'] + stat['assists']) / stat['deaths'])) / (
                    (stat['kills'] + stat['assists']) / stat['deaths']) * 100
    xpm_p = (match['experiencePerMinute'] - stat['xp'] / stat['time']) / (stat['xp'] / stat['time']) * 100
    gpm_p = (match['goldPerMinute'] - stat['networth'] / stat['time']) / (stat['networth'] / stat['time']) * 100
    net_p = (match['networth'] - stat['networth']) / stat['networth'] * 100

    score = (0.3 * kda + 0.25 * gpm + 0.25 * xpm + 0.2 * net) * 10

    return (score, match['isVictory'], match['kills'], match['deaths'], match['assists'], [kda_p, xpm_p, gpm_p, net_p])


def plot_graph(s):
    hero_names = [item['displayName'] for item in s]
    scores = [item['score'] for item in s]

    # Определяем цвета столбцов: зеленый для положительных, красный для отрицательных
    colors = ['green' if score >= 0 else 'red' for score in scores]

    # Создаем фигуру и оси
    fig, ax = plt.subplots(figsize=(12, 6))  # Увеличенный размер для читаемости

    # Строим столбчатую диаграмму
    bars = ax.bar(hero_names, scores, color=colors)

    # Настройка визуализации
    ax.set_xlabel('Герой')
    ax.set_ylabel('Score')
    ax.set_title('Рейтинг героев по Score')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Поворот подписей оси X для лучшей читаемости
    plt.xticks(rotation=45, ha='right')

    # Добавляем значения над столбцами
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # Смещение над столбцом
                    textcoords="offset points",
                    ha='center', va='bottom')

    # Добавляем легенду
    ax.bar([], [], color='green', label='Положительный Score')
    ax.bar([], [], color='red', label='Отрицательный Score')
    ax.legend()

    # Сохраняем график в буфер и закрываем фигуру
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)

    return buf