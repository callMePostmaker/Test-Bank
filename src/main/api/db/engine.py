from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main.api.configs.config import Config

# engine = create_engine(Config.fetch('dataBaseUrl'), echo=False)

db_url = Config.fetch("dataBaseUrl")

raise ValueError(repr(db_url))

engine = create_engine(db_url, echo=False)
SessionLocal = sessionmaker(bind=engine)