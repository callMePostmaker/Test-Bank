from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main.api.configs.config import Config

# connect_timeout: не висеть десятки секунд, если БД недоступна (libpq по умолчанию ждёт бесконечно).
# client_encoding: всегда utf-8, чтобы текст ошибок сервера не зависел от локали Windows.
# pool_pre_ping: переподключение, если БД перезапустили между тестами.
engine = create_engine(
    Config.fetch('dataBaseUrl'),
    echo=False,
    pool_pre_ping=True,
    connect_args={
        'connect_timeout': 5,
        'client_encoding': 'utf8',
    },
)
SessionLocal = sessionmaker(bind=engine)
