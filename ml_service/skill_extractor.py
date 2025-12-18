import spacy
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Добавляем путь для импорта моделей, если запускаем как скрипт
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from back.DB.models import Vacancy, Company
except ImportError:
    pass  # Чтобы не падало, если импорт не нужен при внешнем вызове

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"

# Словарь для нормализации (синоним -> каноническое имя)
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


def normalize_skill(skill_raw):
    lower = skill_raw.lower().strip()
    return CANONICAL_NAMES.get(lower, skill_raw.strip().capitalize())


class SkillExtractor:
    def __init__(self):
        print("Загрузка модели Spacy...")
        try:
            self.nlp = spacy.load("ru_core_news_lg")
        except OSError:
            print("❌ Модель spacy не найдена. Выполните: python -m spacy download ru_core_news_lg")
            sys.exit(1)

    def extract_skills(self, text):
        """
        Извлекает навыки из текста и возвращает список канонических названий.
        """
        if not text:
            return []

        # Ограничиваем длину текста, чтобы spacy не завис на огромных описаниях
        doc = self.nlp(text[:100000].lower())
        found_raw = set()

        for token in doc:
            if token.text in SEARCH_TERMS:
                found_raw.add(token.text)

        return [normalize_skill(s) for s in found_raw]


# --- Функция для ручного запуска (как скрипт) ---
def run_enrichment():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    extractor = SkillExtractor()

    print("--- 1. Обогащение вакансий ---")
    vacancies = session.query(Vacancy).all()
    for vac in vacancies:
        extracted = set(extractor.extract_skills(vac.description))
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
        # Фильтруем слишком длинные мусорные теги
        comp.tech_stack = [s for s in all_stack if len(s) < 20]

    session.commit()
    print("Готово! Навыки обновлены.")


if __name__ == "__main__":
    run_enrichment()