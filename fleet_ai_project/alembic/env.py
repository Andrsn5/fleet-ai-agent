# Настройка Alembic для проекта Fleet AI Agent
# 
# Инструкция по использованию миграций:
# 1. Убедись, что установлен Alembic: pip install alembic
# 2. Инициализируй alembic (если еще не сделано): alembic init alembic
# 3. Замени содержимое alembic/env.py на этот файл
# 4. Создай первую миграцию: alembic revision --autogenerate -m "Initial migration"
# 5. Примени миграцию: alembic upgrade head
#
# Примечание: DATABASE_URL берется из переменных окружения (.env).
# Для локального запуска по умолчанию используется SQLite (sqlite:///./fleet.db).
# В Docker/prod используйте PostgreSQL: postgresql://user:password@db:5432/fleet_db

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Добавляем корень проекта в sys.path, чтобы Alembic мог импортировать модули из app/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем нашу базу и модели
from app.database import Base
from app.models import Vehicle, Event

# Метаданные моделей для автогенерации миграций
target_metadata = Base.metadata

# Загружаем конфигурацию alembic.ini
config = context.config

# Устанавливаем URL базы данных из переменных окружения
# Это переопределяет значение из alembic.ini
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", "sqlite:///./fleet.db"))

# Интерпретируем конфиг файл для логирования Python.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Запуск миграций в 'offline' режиме (без подключения к БД)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Запуск миграций в 'online' режиме (с подключением к БД)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
