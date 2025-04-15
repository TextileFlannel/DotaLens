import pytest
from cache import Cache

@pytest.fixture
def cache():
    return Cache()

def test_cache_set_set(cache):
    cache.set("test_key", "test_value", 3600)
    assert cache.get("test_key")