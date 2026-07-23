# Запуск Fleet AI Project

## Требования
- Установленный **Docker**
- Установленный **Docker Compose** (обычно поставляется вместе с Docker Desktop)

## Переменные окружения

Создайте файл `.env` в корне проекта (рядом с `docker-compose.yml`) или экспортируйте переменную в терминале:

```bash
GIGACHAT_CREDENTIALS=твой_ключ_GigaChat
```

Без этого переменная AI-агент будет использовать заглушку, но эндпоинты `/agent/ask` и `/reports/generate` не смогут работать с реальной моделью.

## Запуск через Docker Compose

1. **Откройте терминал** и перейдите в корневую директорию проекта (там, где находится `docker-compose.yml`):
   ```powershell
   cd fleet_ai_project
   ```

2. **Соберите и запустите все сервисы**:
   ```powershell
   docker-compose up -d --build
   ```
   *(Если у вас Docker Compose V2, команда может выглядеть как `docker compose up -d --build`)*

   Запускаются следующие сервисы:
   - `api` — FastAPI-приложение (порт 8000)
   - `redis` — брокер сообщений для Celery (порт 6379)
   - `celery_worker` — исполнитель фоновых задач
   - `celery_beat` — планировщик ежедневных проверок (каждый день в 08:00 UTC)

3. **Проверка работы**:
   После успешного запуска приложение будет доступно по адресам:
   - **Dashboard (UI)**: [http://localhost:8000/](http://localhost:8000/)
   - **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

4. **Остановка приложения**:
   ```powershell
   docker-compose down
   ```

## Дополнительно

- База данных (SQLite) сохраняется в Docker volume `db_data`. Данные не теряются при перезапуске контейнеров.
- Для просмотра логов конкретного сервиса:
  ```powershell
  docker-compose logs -f api
  docker-compose logs -f celery_worker
  docker-compose logs -f celery_beat
  ```
- Celery Beat запускает задачу `check_upcoming_events_and_notify` ежедневно в 08:00 UTC. Она проверяет сроки мероприятий за 30, 14, 7 и 1 день до наступления, а также просроченные события, и выводит уведомления в логи воркера.
- Для локального запуска без Docker установите зависимости из `requirements.txt` и выполните:
  ```powershell
  uvicorn app.main:app --reload
  ```
