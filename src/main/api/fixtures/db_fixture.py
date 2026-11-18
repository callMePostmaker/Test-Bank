from __future__ import annotations

import socket

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError

from src.main.api.db.engine import SessionLocal, engine

DEFAULT_PG_PORT = 5432


def _endpoint() -> tuple[str | None, int]:
    """host:port из dataBaseUrl (engine.url), с дефолтным портом PostgreSQL."""
    url = engine.url
    return url.host, url.port or DEFAULT_PG_PORT


def _reason(error: BaseException) -> str:
    """Достаём читаемую причину: текст libpq может быть завёрнут в UnicodeDecodeError."""
    if isinstance(error, UnicodeDecodeError):
        return (
            'сервер/libpq ответил в однобайтовой кодировке (русская Windows, cp1251), '
            'поэтому текст ошибки потерялся. Чаще всего это значит, что PostgreSQL не запущен '
            'или не слушает указанный host:port'
        )
    return str(getattr(error, 'orig', error)).strip() or repr(error)


def _skip_unavailable(detail: str) -> None:
    pytest.skip(
        'PostgreSQL недоступен (dataBaseUrl из resources/urls.properties). '
        'Проверь, что БД запущена (docker compose up -d) и доступна по host/port/dbname/user/password. '
        f'Причина: {detail}'
    )


@pytest.fixture(scope='session')
def db_connection_available():
    """Один раз за сессию проверяем БД и отдаём понятную причину вместо трейса psycopg2."""
    host, port = _endpoint()

    # Дешёвая проверка TCP: если порт закрыт, psycopg2 на русской Windows падает
    # с UnicodeDecodeError вместо внятного "connection refused".
    if host:
        try:
            with socket.create_connection((host, port), timeout=3):
                pass
        except OSError as error:
            _skip_unavailable(f'{host}:{port} недоступен ({error.strerror or error})')

    try:
        with engine.connect() as connection:
            connection.execute(text('select 1'))
    except (OperationalError, UnicodeDecodeError) as error:
        _skip_unavailable(_reason(error))

    return True


@pytest.fixture(scope='function')
def db_session(db_connection_available):
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    try:
        yield session
    except DBAPIError:
        # Запрос упал: соединение уже в aborted-состоянии, откатываем и пробрасываем ошибку теста.
        transaction.rollback()
        raise
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
