import psycopg2 as pg
from config import DSN


def delete_tables(dsn):
    """
    Удаляет таблицы 'users_candidates', 'interactions', 'photos', 'candidates', 'users'
    из базы данных, используя DSN подключение.

    :param dsn: Параметры подключения к базе данных
    """
    try:
        # Установка соединения с использованием параметров из DSN
        conn = pg.connect(dsn)
        cursor = conn.cursor()

        # Удаление таблиц в правильном порядке (с учетом foreign keys)
        tables_to_delete = [
            'users_candidates',  # сначала удаляем таблицы с внешними ключами
            'interactions',
            'photos',
            'candidates',
            'users'            # затем удаляем основные таблицы
        ]

        for table in tables_to_delete:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"Таблица '{table}' успешно удалена")
            except Exception as e:
                print(f"Ошибка при удалении таблицы '{table}': {e}")

        # Подтверждение изменений
        conn.commit()

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
    finally:
        # Закрытие соединения
        if 'conn' in locals():
            conn.close()
            print("Соединение с базой данных закрыто")


if __name__ == "__main__":
    delete_tables(DSN)