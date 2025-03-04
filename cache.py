import redis
from config import REDIS_URL
import logging

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self):
        self.active = True
        try:
            self.redis = redis.Redis.from_url(REDIS_URL, socket_timeout=3)
            self.redis.ping()  # Проверка соединения
        except Exception as e:
            self.active = False
            logger.warning(f"Redis недоступен: {e}. Кэширование отключено.")

    def get(self, key):
        if not self.active: return None
        try:
            return self.redis.get(key)
        except:
            return None

    def set(self, key, value, ttl=None):
        if not self.active: return
        try:
            self.redis.set(key, value, ex=ttl)
        except:
            pass

    def delete(self, key):
        if not self.active: return
        try:
            self.redis.delete(key)
        except:
            pass


cache = Cache()
