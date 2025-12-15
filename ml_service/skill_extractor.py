import spacy
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Vacancy, Company

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"

CANONICAL_NAMES = {
    "python": "Python", "java": "Java", "go": "Go", "golang": "Go",
    "cpp": "C++", "c++": "C++", "c#": "C#", "csharp": "C#",
    "js": "JavaScript", "javascript": "JavaScript", "typescript": "TypeScript", "ts": "TypeScript",
    "php": "PHP", "sql": "SQL", "postgres": "PostgreSQL", "postgresql": "PostgreSQL",
    "docker": "Docker", "k8s": "Kubernetes", "kubernetes": "Kubernetes",
    "react": "React", "vue": "Vue.js", "django": "Django", "fastapi": "FastAPI",
    "git": "Git", "linux": "Linux", "html": "HTML", "css": "CSS",
    "rest": "REST API", "rest api": "REST API", "soap": "SOAP",
    "ml": "ML", "machine learning": "ML", "ai": "AI"
}

SEARCH_TERMS = set(CANONICAL_NAMES.keys())

try:
    nlp = spacy.load("ru_core_news_lg")
except:
    print("Модель не найдена. Установить: python -m spacy download ru_core_news_lg")
    sys.exit(1)


def normalize_skill(skill_raw):
    lower = skill_raw.lower().strip()
    return CANONICAL_NAMES.get(lower, skill_raw.strip().capitalize())


def extract_skills_smart(text):
    if not text: return []
    doc = nlp(text.lower())
    found_raw = set()
    for token in doc:
        if token.text in SEARCH_TERMS:
            found_raw.add(token.text)
    return [normalize_skill(s) for s in found_raw]


def run_enrichment():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("--- 1. Обогащение вакансий ---")
    vacancies = session.query(Vacancy).all()
    for vac in vacancies:
        extracted = set(extract_skills_smart(vac.description))
        current = set()
        if vac.requirements:
            for r in vac.requirements:
                current.add(normalize_skill(r))

        combined = current.union(extracted)
        vac.requirements = list(combined)

    print("--- 2. Обновление стека компаний ---")
    companies = session.query(Company).all()
    for comp in companies:
        all_stack = set()
        for v in comp.vacancies:
            if v.requirements:
                for r in v.requirements:
                    all_stack.add(r)
        comp.tech_stack = [s for s in all_stack if len(s) < 20]

    session.commit()
    print("Готово! Дубликаты (Python/python) устранены.")


if __name__ == "__main__":
    run_enrichment()