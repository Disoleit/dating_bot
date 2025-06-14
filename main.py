from vk_dating_bot.bot import DatingBot
from database.databasework import create_tables
from sqlalchemy.exc import OperationalError

from database.databasework import engine, Session
from sqlalchemy import text

if __name__ == "__main__":
    try:
        # Проверка подключения к БД
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            print(f"✅ Подключение к БД: {result.scalar()}")

            # Проверка существования таблицы users
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """))
            print(f"✅ Таблица users существует: {result.scalar()}")

        # Создание таблиц
        create_tables()
        print("✅ Таблицы БД успешно созданы/проверены")

        # Запуск бота
        bot = DatingBot()
        bot.start()

    except OperationalError as e:
        print(f"❌ Ошибка подключения к БД: {e}")
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")
        import traceback

        traceback.print_exc()