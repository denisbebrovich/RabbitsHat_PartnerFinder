import spacy
import sys

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
    _instance = None
    _nlp = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SkillExtractor, cls).__new__(cls)
            print("Загрузка модели Spacy...")
            try:
                cls._nlp = spacy.load("ru_core_news_lg")
            except OSError:
                print("❌ Модель spacy не найдена. Выполните: python -m spacy download ru_core_news_lg")
                sys.exit(1)
        return cls._instance

    def extract_skills(self, text: str) -> list[str]:
        if not text:
            return []

        doc = self._nlp(text[:150000].lower())
        found_raw = set()

        for token in doc:
            if token.text in SEARCH_TERMS:
                found_raw.add(token.text)

        return [normalize_skill(s) for s in found_raw]