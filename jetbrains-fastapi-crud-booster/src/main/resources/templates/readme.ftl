# ${entity.name} module

Сгенерировано FastAPI CRUD Booster.

# >>> FASTAPI_CRUD_BOOSTER
## Маршруты
- `GET /api/v1/${entity.name?lower_case}s/` — список с пагинацией и фильтрами.
- `POST /api/v1/${entity.name?lower_case}s/` — создание сущности.
- `GET /api/v1/${entity.name?lower_case}s/{id}` — получение по идентификатору.
- `PUT /api/v1/${entity.name?lower_case}s/{id}` — обновление.
- `DELETE /api/v1/${entity.name?lower_case}s/{id}` — удаление.

## Настройки
- SQLAlchemy ${settings.sqlalchemyMajor}.x
- Pydantic v${settings.pydanticMajor}
<#if settings.enablePagination>- Пагинация включена.
</#if><#if settings.enableFilters>- Фильтры включены.
</#if><#if settings.enableFeatureFlags>- Feature flag: `enable_${entity.name?lower_case}_module`
</#if>

## Guard-блоки
Все файлы содержат блоки `# >>> FASTAPI_CRUD_BOOSTER` для безопасной регенерации.
# <<< FASTAPI_CRUD_BOOSTER
