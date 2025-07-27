"""
Redis клиент для кеширования
"""
import redis
from app.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def test_redis_connection():
    try:
        redis_client.ping()
        print("Redis подключение успешно!")
        return True
    except Exception as e:
        print(f"Ошибка подключения к Redis: {e}")
        return False


if __name__ == "__main__":
    test_redis_connection()