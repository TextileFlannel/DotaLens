import json
import aiohttp
from config import STRATZ_TOKEN
from graphql_queries import HERO


async def make_graphql_request(query: str):
    url = "https://api.stratz.com/graphql"
    headers = {
        "Authorization": f"Bearer {STRATZ_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "STRATZ_API"
    }
    payload = {
        "query": query
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Request failed with status {response.status}")
            return await response.json()


async def fetch_and_save_items():
    try:
        # Выполняем запрос к API
        response = await make_graphql_request(HERO)

        # Извлекаем данные о предметах
        hero_mas = response.get('data', {}).get('constants', {}).get('heroes', [])
        print(hero_mas)
        heroes = {hero['id']: [hero['shortName'], hero['displayName'], [i['roleId'] for i in hero['roles']]] for hero in
                  hero_mas}

        # Сохраняем результат в файл
        with open('../jsons/heroes.json', 'w', encoding='utf-8') as file:
            json.dump(heroes, file, ensure_ascii=False, indent=4)
        print("Hero successfully saved to items.json")

    except Exception as e:
        print(f"An error occurred: {e}")


# Для запуска асинхронной функции
if __name__ == "__main__":
    import asyncio

    asyncio.run(fetch_and_save_items())
