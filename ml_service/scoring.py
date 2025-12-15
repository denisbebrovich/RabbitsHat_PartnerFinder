import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Company

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"

# Стек ПроКомпетенции
CORE_STACK = {"Python", "Java", "Go", "PostgreSQL", "Docker", "React", "Vue.js", "FastAPI", "Django"}

def calculate_score(company):
    score = 0.0

    if not company.tech_stack:
        return 0.0

    comp_stack_lower = {s.lower() for s in company.tech_stack}

    matches = 0
    for core_tech in CORE_STACK:
        if core_tech.lower() in comp_stack_lower:
            score += 15  # +15 за каждую "Золотую" технологию
            matches += 1

    # Если есть разнообразие, но не сборище мусора (чего попало)
    if 2 <= len(comp_stack_lower) <= 10:
        score += 5

    # Если подтвержденная IT компания
    if company.is_it_company:
        score += 20

    # Если есть длинное описание
    if company.description and len(company.description) > 150:
        score += 10

    # Система штрафов. Если нет технологий из списка, но есть стек
    if matches == 0 and len(comp_stack_lower) > 0:
        score -= 10

    return max(0.0, min(score, 100.0))


def run_scoring():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    companies = session.query(Company).all()
    print("Пересчет скоринга...")

    for comp in companies:
        comp.score = calculate_score(comp)

    session.commit()
    print("Скоринг завершен.")


if __name__ == "__main__":
    run_scoring()