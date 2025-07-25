from celery import Celery
from app.config import settings

# Создаем экземпляр Celery
celery_app = Celery(
    "arbitration",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
    include=[
        #"app.tasks.notifications",
        #"app.tasks.analytics",
        "app.tasks.price_monitoring"
    ]
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,  # 25 минут
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Функция для проверки подключения к Celery
def test_celery_connection():
    try:
        result = celery_app.control.inspect().active()
        print("✅ Celery подключение успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к Celery: {e}")
        return False