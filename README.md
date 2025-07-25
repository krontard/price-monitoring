# 🚀 Arbitration Price Monitoring

> ⚠️ **УЧЕБНЫЙ ПРОЕКТ** - не используйте в продакшене без дополнительной настройки безопасности!

Система мониторинга цен для арбитража товаров между маркетплейсами (Amazon, Wildberries, Ozon).

## 📋 Описание

Проект позволяет:
- 🔍 Мониторить цены товаров на разных маркетплейсах
- 📊 Анализировать возможности арбитража  
- 📈 Отслеживать историю изменения цен
- ⚡ Асинхронная обработка через Celery

## 🛠 Технологии

- **Backend**: FastAPI + Python 3.11+
- **База данных**: PostgreSQL + SQLAlchemy + Alembic
- **Очереди**: Celery + Redis + RabbitMQ
- **API документация**: Swagger UI

## 📁 Структура проекта

```
arbitration/
├── app/
│   ├── api/v1/endpoints/    # API endpoints
│   ├── models/              # SQLAlchemy модели
│   ├── schemas/             # Pydantic схемы
│   ├── tasks/               # Celery задачи
│   ├── utils/               # Утилиты
│   ├── config.py            # Конфигурация
│   ├── database.py          # Подключение к БД
│   └── main.py              # FastAPI приложение
├── alembic/                 # Миграции БД
├── requirements.txt         # Зависимости
└── README.md
```

## 🚀 Быстрый старт

### 1. Клонирование и установка
```bash
git clone https://github.com/your-username/arbitration.git
cd arbitration
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. Настройка окружения
Создайте файл `.env` на основе `.env.example`:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/arbitration_db
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
SECRET_KEY=your-super-secret-key
DEBUG=True
```

### 3. Запуск инфраструктуры (Docker)
```bash
docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15
docker run -d --name redis -p 6379:6379 redis:7
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

### 4. Миграции и запуск
```bash
alembic upgrade head
celery -A app.tasks.celery_app worker --loglevel=info &
uvicorn app.main:app --reload
```

## 📚 API Документация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔗 Основные endpoints

### Мониторинг цен:
- `POST /api/v1/monitoring/start` - Запуск мониторинга
- `GET /api/v1/monitoring/tasks` - Список активных задач
- `GET /api/v1/monitoring/result/{task_id}` - Результат задачи
- `GET /api/v1/monitoring/health` - Статус системы

## 🧪 Тестирование

```bash
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/monitoring/health" -Method GET

# Linux/Mac
curl http://localhost:8000/api/v1/monitoring/health
```

## 🚧 Известные проблемы (TODO)

- ❌ Пароли не хешируются (см. `app/api/v1/endpoints/users.py:28`)
- ❌ Конфигурация содержит пароли в коде
- ❌ Широкие CORS настройки (`allow_origins=["*"]`)
- ❌ Парсеры используют заглушки (`fake_price`)
- ❌ Общий перехват исключений (`except Exception as e`)

## 🎯 Статус разработки

- ✅ Базовая архитектура FastAPI
- ✅ Модели базы данных (User, Product, PriceHistory, TaskHistory)
- ✅ Система мониторинга задач через Celery
- ✅ PostgreSQL + Alembic миграции
- 🔄 Парсеры маркетплейсов (заглушки)
- ❌ Система аутентификации
- ❌ Реальные парсеры
- ❌ Веб-интерфейс

## 🤝 Участие в разработке

1. Fork проекта
2. Создайте feature branch
3. Commit изменения
4. Push и создайте Pull Request

## 📝 Лицензия

MIT License - см. файл LICENSE

## ⚠️ Дисклеймер

Это учебный проект для изучения FastAPI, Celery и архитектуры микросервисов. 
Не используйте в продакшене без серьезной доработки безопасности! 