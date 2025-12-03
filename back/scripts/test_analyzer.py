import os
import sys

# Добавляем корень проекта в Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from services.data_analyzer import DataAnalyzer

def test_analyzer():
    print("Тестируем DataAnalyzer...")
    analyzer = DataAnalyzer()
    
    # Тест статистики отраслей - ТОЛЬКО 3 САМЫХ ПОПУЛЯРНЫХ
    print("\n=== ТОП-3 ОТРАСЛИ ПО КОЛИЧЕСТВУ КОМПАНИЙ ===")
    industry_stats = analyzer.get_industry_stats()
    for stat in industry_stats[:3]:  # Только первые 3
        print(f"{stat['industry']}: {stat['company_count']} компаний, в среднем {stat['avg_tech_count']} технологий")
    
    # Тест популярных технологий
    print("\n=== ТОП-5 ПОПУЛЯРНЫХ ТЕХНОЛОГИЙ ===")
    popular_tech = analyzer.get_popular_technologies(5)
    for tech, count in popular_tech:
        print(f"{tech}: {count} компаний")
    
    # Тест поиска компаний - ТОЛЬКО НАЗВАНИЯ КОМПАНИЙ
    print("\n=== КОМПАНИИ ДЛЯ ПАРТНЕРСТВА (Python, Linux) ===")
    companies = analyzer.get_companies_for_partnership(['Python', 'Linux'])
    print(f"Найдено компаний с Python и Linux: {len(companies)}")
    for company in companies:
        print(f"- {company.name}")  # Только название
    
    # Тест статистики вакансий - ТОЛЬКО РАСПРЕДЕЛЕНИЕ ПО ЗАНЯТОСТИ В СТОЛБЕЦ
    print("\n=== РАСПРЕДЕЛЕНИЕ ВАКАНСИЙ ПО ТИПУ ЗАНЯТОСТИ ===")
    vacancy_stats = analyzer.get_vacancy_stats()
    print(f"Всего вакансий: {vacancy_stats['total_vacancies']}")
    
    employment_distribution = vacancy_stats['employment_distribution']
    for employment_type, count in employment_distribution.items():
        percentage = (count / vacancy_stats['total_vacancies']) * 100
        print(f"{employment_type}: {count} вакансий ({percentage:.1f}%)")
    
    print("\nВсе тесты пройдены!")

if __name__ == "__main__":
    test_analyzer()