import redis
from app.config import settings

# Создаем подключение к Redis
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,  # Автоматически декодировать ответы в строки
    socket_connect_timeout=5,
    socket_timeout=5
)

# Функция для проверки подключения к Redis
def test_redis_connection():
    try:
        redis_client.ping()
        print("✅ Redis подключение успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к Redis: {e}")
        return False