import sys
import os
from sqlalchemy import create_engine, text
# ВРЕМЕННЫЙ СКРИПТ, ОН НЕ БУДЕТ ПОТОМ ИСПОЛЬЗОВАТЬСЯ
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"

def reset_database():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Удаление старых таблиц (DROP)...")
        conn.execute(text("DROP TABLE IF EXISTS emails CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS vacancies CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS companies CASCADE;"))
        conn.commit()
    print("Таблицы полностью удалены! Теперь запустите init_database.py.")

if __name__ == "__main__":
    confirm = input("Это удалит ВСЕ таблицы и данные. Вы уверены? (y/n): ")
    if confirm.lower() == 'y':
        reset_database()
    else:
        print("Отмена.")