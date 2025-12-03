# Создай файл check_data.py
from sqlalchemy import create_engine, text

def check_data():
    engine = create_engine('postgresql://admin:password@localhost:5432/partner_finder')
    
    with engine.connect() as conn:
        # Проверяем компании
        result = conn.execute(text("SELECT name, industries, tech_stack FROM companies LIMIT 10"))
        print("=== КОМПАНИИ ===")
        for row in result:
            print(f"Название: {row[0]}")
            print(f"Отрасли: {row[1]}")
            print(f"Технологии: {row[2]}")
            print("---")
        
        # Проверяем вакансии
        result = conn.execute(text("SELECT title, description, requirements FROM vacancies LIMIT 3"))
        print("\n=== ВАКАНСИИ ===")
        for row in result:
            print(f"Должность: {row[0]}")
            print(f"Описание: {row[1][:100] if row[1] else 'ПУСТО'}")  # Первые 100 символов
            print(f"Требования: {row[2]}")
            print("---")

if __name__ == "__main__":
    check_data()