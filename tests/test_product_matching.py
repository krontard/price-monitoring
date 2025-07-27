"""
Тестирование системы сопоставления товаров
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.product_matcher import ProductMatchingService


async def test_product_matching():
    """Тест основной функциональности поиска товаров"""
    
    test_queries = [
        "iPhone 13",
        "Samsung Galaxy S23",
        "Xiaomi Mi Band 7"
    ]
    
    async with ProductMatchingService() as matcher:
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f" ТЕСТИРУЕМ ЗАПРОС: '{query}'")
            print(f"{'='*60}")
            
            match = await matcher.find_product_everywhere(query)
            
            print(f"\n РЕЗУЛЬТАТЫ ПОИСКА:")
            print(f"   Найдено товаров: {match.found_count}")
            
            if match.wildberries:
                print(f"\nWILDBERRIES:")
                print(f"   Название: {match.wildberries.name}")
                print(f"   Цена: {match.wildberries.price:.2f} ₽")
                print(f"   ID: {match.wildberries.product_id}")
                print(f"   Рейтинг: {match.wildberries.rating}")
                print(f"   Отзывы: {match.wildberries.reviews_count}")
                print(f"   URL: {match.wildberries.url}")
            
            if match.ozon:
                print(f"\n  OZON:")
                print(f"   Название: {match.ozon.name}")
                print(f"   Цена: {match.ozon.price:.2f} ₽")
                print(f"   ID: {match.ozon.product_id}")
            
            if match.yandex_market:
                print(f"\nЯНДЕКС.МАРКЕТ:")
                print(f"   Название: {match.yandex_market.name}")
                print(f"   Цена: {match.yandex_market.price:.2f} ₽")
                print(f"   ID: {match.yandex_market.product_id}")
            
            if match.found_count >= 2:
                print(f"\nАНАЛИЗ АРБИТРАЖА:")
                print(f"   Минимальная цена: {match.min_price:.2f} ₽")
                print(f"   Максимальная цена: {match.max_price:.2f} ₽")
                print(f"   Возможность арбитража: {match.arbitrage_opportunity:.2f} ₽")
                
                if match.arbitrage_opportunity > 1000:
                    print(f"   ОТЛИЧНАЯ ВОЗМОЖНОСТЬ!")
                elif match.arbitrage_opportunity > 500:
                    print(f"   Хорошая возможность")
                else:
                    print(f"   Небольшая разница")
            
            is_valid = await matcher.validate_product_match(match)
            print(f"\nВАЛИДАЦИЯ: {'Товары схожи' if is_valid else 'Товары слишком разные'}")
            
            urls = matcher.get_urls_for_database(match)
            ids = matcher.get_ids_for_monitoring(match)
            
            print(f"\nСОХРАНЕНИЕ В БД:")
            print(f"   Wildberries URL: {urls['wildberries_url']}")
            print(f"   Ozon URL: {urls['ozon_url']}")
            print(f"   Яндекс.Маркет URL: {urls['yandex_market_url']}")
            
            print(f"\nID ДЛЯ МОНИТОРИНГА:")
            print(f"   Wildberries ID: {ids['wildberries_id']}")
            print(f"   Ozon ID: {ids['ozon_id']}")
            print(f"   Яндекс.Маркет ID: {ids['yandex_market_id']}")


async def test_similarity_algorithm():
    """Тест алгоритма определения схожести товаров"""
    
    from app.external.base_api import ProductMatcher
    
    print(f"\n{'='*60}")
    print(f"ТЕСТ АЛГОРИТМА СХОЖЕСТИ")
    print(f"{'='*60}")
    
    test_cases = [
        ("iPhone 13", "Apple iPhone 13 Pro 128GB"),
        ("Samsung Galaxy S23", "Samsung Galaxy S23 Ultra 256GB"),
        ("Xiaomi Mi Band 7", "Mi Smart Band 7 Pro"),
        ("MacBook Air", "Apple MacBook Air 13 M2"),
        ("iPhone 13", "Samsung Galaxy S23"),
    ]
    
    matcher = ProductMatcher()
    
    for query, product_name in test_cases:
        similarity = matcher.calculate_similarity(query, product_name)
        
        print(f"\nЗапрос: '{query}'")
        print(f"Товар: '{product_name}'")
        print(f"Схожесть: {similarity:.2f}")
        
        if similarity >= 0.7:
            print(f"Отличное совпадение!")
        elif similarity >= 0.4:
            print(f"Хорошее совпадение")
        else:
            print(f"Плохое совпадение")


async def main():
    """Основная функция тестирования"""
    
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ СОПОСТАВЛЕНИЯ ТОВАРОВ")
    
    try:
        await test_similarity_algorithm()
        
        await test_product_matching()
        
        print(f"\n{'='*60}")
        print("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\nОшибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 