import sys
import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# ВРЕМЕННЫЙ СКРИПТ, ОН НЕ БУДЕТ ПОТОМ ИСПОЛЬЗОВАТЬСЯ
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Company

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"


def check_stats():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    total_companies = session.query(Company).count()
    print(f"\n=== СТАТИСТИКА БАЗЫ (Всего компаний: {total_companies}) ===")

    try:
        threshold = float(input("Введите минимальный рейтинг (например, 40): "))
    except ValueError:
        print("Ошибка: введите число.")
        return

    target_count = session.query(Company).filter(Company.score >= threshold).count()

    print(f"\n>>> Компаний с рейтингом >= {threshold}: {target_count}")

    if total_companies > 0:
        percent = (target_count / total_companies) * 100
        print(f">>> Это {percent:.1f}% от всей базы.")

    if target_count > 0:
        print("\nТоп-5 подходящих компаний:")
        top_companies = session.query(Company).filter(Company.score >= threshold) \
            .order_by(Company.score.desc()).limit(5).all()

        for comp in top_companies:
            print(f"- {comp.name} (Score: {comp.score}) | Стек: {', '.join(comp.tech_stack[:3])}...")


if __name__ == "__main__":
    check_stats()