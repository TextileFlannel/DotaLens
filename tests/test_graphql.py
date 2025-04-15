import pytest
from unittest.mock import AsyncMock, patch
from scripts.hero import make_graphql_request

# Фикстура для мокирования aiohttp
@pytest.fixture
def mock_aiohttp():
    with patch("aiohttp.ClientSession.post") as mock_post:
        yield mock_post

# Тестовые данные
TEST_QUERY = """
query {
  constants {
    hero(id: 1) {
      displayName
    }
  }
}
"""

TEST_RESPONSE = {
    "data": {
        "constants": {
            "hero": {
                "displayName": "Anti-Mage"
            }
        }
    }
}

@pytest.mark.asyncio
async def test_make_graphql_request(mock_aiohttp):
    # Настройка мокированного ответа
    mock_response = AsyncMock()
    mock_response.status = 200  # Указываем статус ответа
    mock_response.json.return_value = TEST_RESPONSE  # Указываем JSON-ответ
    mock_aiohttp.return_value.__aenter__.return_value = mock_response  # Мокируем сессию

    # Вызов тестируемой функции
    result = await make_graphql_request(TEST_QUERY)

    # Проверка результата
    assert result == TEST_RESPONSE
    assert result["data"]["constants"]["hero"]["displayName"] == "Anti-Mage"