from celery import current_app
from celery.exceptions import CeleryError
from app.tasks.celery_app import celery_app
import requests
from datetime import datetime
import time

@celery_app.task(bind=True)
def test_task(self):
    print("Тест запущен")
    time.sleep(5)
    return {"status": "success", "message": "Тест прошел успешно!", "timestamp": str(datetime.now())}

@celery_app.task(bind=True)
def parse_amazon_price(self, product_name, url = None):
    print(f"Парсинг цены для {product_name}")

    fake_price = 1500 #заглушка

    return {
        "marketplace": "Amazon",
        "product_name": product_name,
        "price": fake_price,
        "currency": "RUB",
        "timestamp": str(datetime.now()),
        "url": url or f"https://www.amazon.com/s?k={product_name}"
    }

@celery_app.task(bind=True)
def parse_wildberries_price(self, product_name, url = None):
    print(f"Парсинг цены для {product_name}")

    fake_price = 1200 #заглушка

    return {
        "marketplace": "Wildberries",
        "product_name": product_name,
        "price": fake_price,
        "currency": "RUB",
        "timestamp": str(datetime.now()),
        "url": url or f"https://wildberries.ru/catalog/0/search.aspx?search={product_name}"
    }

@celery_app.task(bind=True)
def parse_ozon_price(self, product_name, url=None):
    """Парсинг цены с Ozon"""
    print(f"🔍 Парсим цену на Ozon для: {product_name}")
    
    # Пока что заглушка
    fake_price = 1350.00
    
    return {
        "marketplace": "Ozon",
        "product_name": product_name,
        "price": fake_price,
        "currency": "RUB",
        "timestamp": str(datetime.now()),
        "url": url or f"https://ozon.ru/search/?text={product_name}"
    }

@celery_app.task(bind=True)
def monitor_product_prices(self, product_id, product_name):
    print(f"🔍 Мониторинг цен для продукта: {product_name} (ID: {product_id})")

    amazon_result = parse_amazon_price(product_name)
    wildberries_result = parse_wildberries_price(product_name) 
    ozon_result = parse_ozon_price(product_name)

    prices = [amazon_result["price"], wildberries_result["price"], ozon_result["price"]]
    min_price = min(prices)
    max_price = max(prices)
    arbitrage_opportunity = max_price - min_price

    result = {
        "product_id": product_id,
        "product_name": product_name,
        "prices": {
            "amazon": amazon_result["price"],
            "wildberries": wildberries_result["price"],
            "ozon": ozon_result["price"]
        },
        "analytics": {
            "min_price": min_price,
            "max_price": max_price,
            "arbitrage_opportunity": arbitrage_opportunity
        },
        "timestamp": str(datetime.now())
    }

    print(f"🔍 Результат мониторинга для {product_name}: {result}")

    return result

@celery_app.task(bind=True)
def monitor_all_products(self):
    print("🔍 Запуск мониторинга всех продуктов")

    test_products = [
        {"id": 1, "name": "iPhone 15"},
        {"id": 2, "name": "Samsung Galaxy S24"},
        {"id": 3, "name": "MacBook Air M3"}
    ]

    results = []
    for product in test_products:
        task = monitor_product_prices.delay(product["id"], product["name"])
        results.append(task.id)
    
    return {
        "message": f"Запущен мониторинг {len(test_products)} товаров",
        "task_ids": results,
        "timestamp": str(datetime.now())
    }