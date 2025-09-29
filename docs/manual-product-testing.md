# Ручное тестирование списка товаров

Этот чек-лист помогает наполнить каталог 250 детерминированными товарами и вручную проверить фильтры, сортировки и пагинацию API/интерфейса.

## 1. Подготовка окружения
1. Активируйте виртуальное окружение backend и установите зависимости:
   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Примените миграции и запустите сидер с детерминированными данными:
   ```bash
   alembic upgrade head
   python -m app.db.seed
   ```
3. Убедитесь, что в таблице `products` появилось ровно 250 записей. Быстрая проверка через psql/SQLite или REST:
   ```bash
   http GET :8000/api/v1/products/ Authorization:"Bearer <token>" size=1
   ```
   Ответ должен содержать `total = 250` и `sort.by = "id"`.

## 2. Базовая sanity-проверка API
1. Запустите backend:
   ```bash
   uvicorn app.main:app --reload
   ```
2. Залогиньтесь (UI или REST) под `admin@oppo.kz / Admin123!` и получите access token.
3. Используйте Postman/HTTPie/браузер для следующих сценариев.

## 3. Мини-сценарии ручных тестов
1. **`contains` по названию** — GET `/api/v1/products?title_contains=Demo%20Product%20050`. Ожидайте ровно одну позицию `Demo Product 050`.
2. **`between` по цене** — GET `/api/v1/products?price_between=200,400`. Убедитесь, что все цены лежат в диапазоне, а `total` > 0.
3. **`in` по идентификаторам** — GET `/api/v1/products?id_in=1,2,3`. Проверьте, что вернулись именно товары `1-3` и `total = 3`.
4. **Мульти-сортировка** — GET `/api/v1/products?sort_by=price,id&sort_order=desc,asc`. Убедитесь, что цена убывает, а при равенстве ID растёт.
5. **Большие страницы** — GET `/api/v1/products?page=1&size=100`. Проверьте, что `size = 100`, `total = 250`, `next_offset = 100`.
6. **Несовпадающий фильтр** — GET `/api/v1/products?title_contains=Nope`. Ожидайте `total = 0`, `items = []`, `filters_applied` сохранён.
7. **Сброс фильтров** — Выполните предыдущий запрос, затем вызовите `/api/v1/products/reset` (или кнопка UI сброса). Список должен вернуться к 250 товарам.
8. **Возврат на страницу 1 после смены фильтра** — Откройте `/api/v1/products?page=3&size=25`, затем примените фильтр `in_stock=false`. Проверьте, что ответ пришёл с `page = 1` и корректным `total` (125).
9. **Ошибка на неверном операторе** — GET `/api/v1/products?price_foo=10`. Должен прийти `400` и `error_code = VALIDATION_ERROR`.
10. **Стабильная дефолтная сортировка** — GET `/api/v1/products` без параметров дважды. Убедитесь, что порядок (по `id asc`) одинаков и `sort` содержит `{ "by": "id", "order": "asc" }`.

## 4. Завершение
- Для повторной чистой проверки можно очистить таблицу и снова запустить `python -m app.db.seed` — набор данных детерминированный.
- При необходимости обновите access token через `/api/v1/auth/refresh`.

Удачного тестирования!
