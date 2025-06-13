from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from config import DSN

# Создание движка и фабрики сессий
engine = create_engine(DSN, echo=True)
Session = sessionmaker(bind=engine)

def create_tables():
    """Создание таблиц (вызывается один раз при старте бота)"""
    Base.metadata.create_all(engine)