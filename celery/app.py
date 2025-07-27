"""
Celery приложение для фоновых задач
"""
from celery import Celery

app = Celery('arbitration')

app.config_from_object('celery.config')

app.autodiscover_tasks([
    "celery.price_monitoring",
    "celery.notifications",
    "celery.analytics",
])

app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'monitor-prices-every-hour': {
            'task': 'celery.price_monitoring.monitor_all_products',
            'schedule': 3600.0,
        },
    },
)


def test_celery_connection():
    try:
        result = app.control.inspect().stats()
        if result:
            print("Celery подключение успешно!")
            return True
    except Exception as e:
        print(f"Ошибка подключения к Celery: {e}")
        return False


if __name__ == '__main__':
    test_celery_connection()