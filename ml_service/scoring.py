CORE_STACK = {"Python", "Java", "Go", "PostgreSQL", "Docker", "React", "Vue.js", "FastAPI", "Django"}

def calculate_score(company_data: dict) -> float:
    score = 0.0

    tech_stack = company_data.get('tech_stack', [])
    if not tech_stack:
        return 0.0

    comp_stack_lower = {s.lower() for s in tech_stack}

    matches = 0
    for core_tech in CORE_STACK:
        if core_tech.lower() in comp_stack_lower:
            score += 15
            matches += 1

    # Бонус за разнообразие стека
    if 2 <= len(comp_stack_lower) <= 10:
        score += 5

    # Бонус за IT аккредитацию
    if company_data.get('is_it_company'):
        score += 20

    # Бонус за описание
    description = company_data.get('description', "")
    if description and len(description) > 150:
        score += 10

    # Штраф: если стек есть, но ничего из нашего
    if matches == 0 and len(comp_stack_lower) > 0:
        score -= 10

    return max(0.0, min(score, 100.0))