import os

from dotenv import load_dotenv

load_dotenv()

DSN=os.getenv('DSN')

# Конфигурационные параметры
GROUP_TOKEN = os.getenv("GROUP_TOKEN")  # Токен сообщества
USER_TOKEN = os.getenv("USER_TOKEN")  # Токен приложения
GROUP_ID = os.getenv("GROUP_ID")  # ID сообщества
API_VERSION = "5.199"  # Версия VK API

# Параметры поиска по умолчанию
DEFAULT_AGE = 35
DEFAULT_CITY = 1  # Москва
DEFAULT_CITY_TITLE = "Москва"