# StockFlow API

REST API для складского учёта: товары, склады, остатки и журнал поступлений/списаний.

> **Статус:** первый этап разработки (MVP). Это учебный backend-проект, не готовая промышленная WMS.

## Что реализовано

- Справочники товаров и складов.
- Просмотр остатков с фильтрацией по товару и складу.
- Поступления и списания через единый сервис бизнес-логики.
- Запрет списания при недостаточном остатке.
- Атомарное изменение остатков и запись в журнал операций.
- Разграничение доступа: авторизованные пользователи читают, `is_staff` изменяют.
- Swagger/OpenAPI и базовые API-тесты.

## Стек

Python 3.12, Django 5.2, Django REST Framework, PostgreSQL 16, Docker Compose, pytest, drf-spectacular.

## Запуск с Docker

1. Скопируйте `.env.example` в `.env` (Windows: `copy .env.example .env`; Linux/macOS: `cp .env.example .env`). Измените `DJANGO_SECRET_KEY` и пароль БД.
2. Запустите `docker compose up --build -d`.
3. Создайте сотрудника: `docker compose exec api python manage.py createsuperuser`.
4. Откройте `http://localhost:8000/api/docs/`. Для входа используйте `http://localhost:8000/api-auth/login/`.

Для остановки: `docker compose down` (данные PostgreSQL сохраняются в volume).

## Локальный запуск без Docker

```bash
python -m venv .venv
# Активируйте виртуальное окружение для своей ОС
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Без `POSTGRES_HOST` в окружении используется SQLite для локальной разработки. Для проверки конкурентных операций используйте PostgreSQL.

## API

| Метод | Путь | Назначение |
| --- | --- | --- |
| GET, POST | `/api/v1/products/` | Список / создание товаров |
| GET, POST | `/api/v1/warehouses/` | Список / создание складов |
| GET | `/api/v1/stocks/?warehouse=1` | Остатки |
| GET, POST | `/api/v1/movements/` | Журнал / новая операция |
| GET | `/api/docs/` | Swagger UI |

### Пример поступления

`POST /api/v1/movements/` (пользователь с `is_staff`):

```json
{
  "product": 1,
  "warehouse": 1,
  "kind": "receipt",
  "quantity": 10,
  "note": "Первая поставка"
}
```

Списание: замените `kind` на `issue`. Если остатка не хватает, API возвращает HTTP 400 и не записывает движение.

## Тесты

```bash
pytest -q
python manage.py check
```

## Архитектура

- `inventory/models.py` — структура данных и ограничения.
- `inventory/services.py` — транзакционная бизнес-логика изменения остатков.
- `inventory/serializers.py` — валидация входных данных и JSON.
- `inventory/views.py` — HTTP-слой и права доступа.
- `inventory/tests/` — сценарии API.

## Ограничения MVP и следующие шаги

- Нет резервирования заказов и перемещений между складами.
- Пока используется сессионная/Basic-аутентификация; JWT не добавлен.
- Конкурентность на PostgreSQL реализована блокировкой строки, но стресс-тесты ещё не добавлены.
- Нужны миграции, созданные Django, и подтверждение успешного запуска полного набора тестов в CI.
- Redis/Celery подключим, когда появятся реальные фоновые операции.

## Безопасность

Не коммитьте `.env`, секреты и реальные данные. Настройки и авторизация демонстрационные; перед публичным развёртыванием необходимы отдельные production-настройки, HTTPS и аудит безопасности.
