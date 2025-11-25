import os
import sys
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import time
import re

# Ensure `back/` directory is available for imports when running as a script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from DB.models import Company, Vacancy


class HHExtractor:
    def __init__(self, db_url = 'postgresql://admin:password@postgres:5432/partner_finder'):
        self.db_engine = create_engine(db_url)
        self.Session = sessionmaker(bind = self.db_engine)
        self.base_url = 'https://api.hh.ru'
    
    def skills_extractor(self, vacancy_data):
        key_skills = vacancy_data.get('key_skills', [])
        if key_skills and isinstance(key_skills, list):
            skills_list = [skill['name'] for skill in key_skills]
            return skills_list
        else:
            return []

    def get_vacancies_by_query(self, query, area = 3, per_page=100):
        url = f'{self.base_url}/vacancies'
        params = {
            'text': query,
            'area': area,
            'per_page': per_page,
            'page': 0
        }

        try:
            response = requests.get(url, params =  params)
            if response.status_code == 200:
                return response.json()
            else:
                print (f'Ошибка API: {response.status_code}')
                return None
        except Exception as e:
            print(f'Ошибка при запросе: {e}')
            return None 

    def get_employer_details(self, employer_id):
        url = f"{self.base_url}/employers/{employer_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка API employers для {employer_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Ошибка запроса employers для {employer_id}: {e}")
            return None

    def extract_company_info(self, employer_data, employer_details=None):
        # Если есть детальная информация, используем её
        if employer_details:
            # Извлекаем отрасли
            industries = employer_details.get('industries', [])
            industry_names = [industry['name'] for industry in industries] if industries else []
            
            # Извлекаем регион
            area = employer_details.get('area', {})
            region = area.get('name', 'Екатеринбург')
            
            # Извлекаем описание (убираем HTML теги)
            description = employer_details.get('description', '')
            if description:
                import re
                description = re.sub('<[^<]+?>', '', description)
            
            return {
                'hh_id': str(employer_data['id']),
                'name': employer_data['name'],
                'is_it_company': employer_data.get('accredited_it_employer', False),
                'industries': industry_names,  
                'region': region,
                'tech_stack': [],
                'description': description,
                'site_url': employer_details.get('site_url')
            }
        else:
            # Если детальной информации нет, используем базовые данные
            return {
                'hh_id': str(employer_data['id']),
                'name': employer_data['name'],
                'is_it_company': employer_data.get('accredited_it_employer', False),
                'industries': ['IT'],  
                'region': 'Екатеринбург',
                'tech_stack': [],
                'description': None,
                'site_url': None
            }
    
    def extract_vacancy_info(self, vacancy_data):
        skills = self.skills_extractor(vacancy_data)
        
        return {
            'hh_id': str(vacancy_data['id']),
            'title': vacancy_data['name'],
            'company_id': str(vacancy_data['employer']['id']),
            'description': vacancy_data.get('snippet', {}).get('responsibility', ''),
            'source': 'hh.ru',
            'requirements': skills,
            'experience': vacancy_data.get('experience', {}).get('name', ''),
            'employment': vacancy_data.get('employment', {}).get('name', ''),
            'location': vacancy_data.get('area', {}).get('name', ''),
            'professional_role': vacancy_data.get('professional_roles', [{}])[0].get('name', '') if vacancy_data.get('professional_roles') else '',
            'published_at': vacancy_data.get('published_at')
        }
    def update_company_tech_stack(self, session, company_hh_id):
        # Получаем все вакансии компании
        company_vacancies = session.query(Vacancy).filter_by(company_id=company_hh_id).all()
        
        # Собираем все навыки из всех вакансий
        all_skills = []
        for vacancy in company_vacancies:
            if vacancy.requirements:
                all_skills.extend(vacancy.requirements)
        
        # Убираем дубликаты
        unique_skills = list(set(all_skills))
        
        # Обновляем компанию
        company = session.query(Company).filter_by(hh_id=company_hh_id).first()
        if company:
            company.tech_stack = unique_skills
            print(f"Обновлен стек технологий для {company.name}: {len(unique_skills)} навыков")

    def run_etl(self, queries=['Python разработчик', 'Java разработчик', 'JavaScript разработчик']):
        session = self.Session()
        
        # Словарь для кэширования данных о компаниях
        employer_cache = {}
        
        # Счетчики для статистики
        companies_added = 0
        vacancies_added = 0
        
        for query in queries:
            print(f"Собираем вакансии по запросу: '{query}' в Екатеринбурге")
            
            # Получаем вакансии по запросу
            data = self.get_vacancies_by_query(query, area=3, per_page=20)  # Уменьшил для теста
            if not data or 'items' not in data:
                print(f"Нет данных для запроса: {query}")
                continue
                
            print(f"Найдено вакансий: {len(data['items'])}")
            
            for vacancy_data in data['items']:
                try:
                    employer_id = str(vacancy_data['employer']['id'])
                    
                    # Получаем детальную информацию о компании
                    if employer_id not in employer_cache:
                        print(f"Получаем информацию о компании {employer_id}...")
                        employer_details = self.get_employer_details(employer_id)
                        employer_cache[employer_id] = employer_details
                        time.sleep(0.5)  # Пауза между запросами
                    else:
                        employer_details = employer_cache[employer_id]
                    
                    # Извлекаем данные компании
                    company_info = self.extract_company_info(
                        vacancy_data['employer'], 
                        employer_details
                    )
                    
                    # Проверяем и добавляем компанию
                    existing_company = session.query(Company).filter_by(hh_id=company_info['hh_id']).first()
                    if not existing_company:
                        company = Company(**company_info)
                        session.add(company)
                        session.flush()
                        companies_added += 1
                        print(f"Добавлена компания: {company_info['name']}")
                    
                    # 🔧 ИСПРАВЛЕНИЕ: Получаем полную информацию о вакансии с навыками
                    vacancy_details = self.get_vacancy_details(vacancy_data['id'])
                    if vacancy_details:
                        # Используем полные данные с навыками
                        vacancy_info = self.extract_vacancy_info(vacancy_details)
                        print(f"Навыки вакансии '{vacancy_info['title']}': {vacancy_info['requirements']}")
                    else:
                        # Запасной вариант - используем краткие данные
                        vacancy_info = self.extract_vacancy_info(vacancy_data)
                        print(f"Нет навыков для вакансии '{vacancy_info['title']}'")
                    
                    # Извлекаем и добавляем вакансию
                    existing_vacancy = session.query(Vacancy).filter_by(hh_id=vacancy_info['hh_id']).first()
                    if not existing_vacancy:
                        vacancy = Vacancy(**vacancy_info)
                        session.add(vacancy)
                        vacancies_added += 1
                    
                    # Пауза между запросами вакансий
                    time.sleep(0.3)
                    
                except Exception as e:
                    session.rollback()  # Сбрасываем сессию после ошибки
                    print(f"Ошибка обработки вакансии: {e}")
                    continue
                
            # Пауза между разными запросами
            time.sleep(1)
        
        # Обновляем технологические стеки всех компаний
        print("Обновляем технологические стеки компаний...")
        companies = session.query(Company).all()
        for company in companies:
            self.update_company_tech_stack(session, company.hh_id)
        
        # Сохраняем все изменения
        session.commit()
        session.close()
        
        # Выводим статистику
        print(f"\nETL процесс завершен!")
        print(f"Компаний добавлено: {companies_added}")
        print(f"Вакансий добавлено: {vacancies_added}")
        print(f"Всего компаний в БД: {len(companies)}")

    def get_vacancy_details(self, vacancy_id):
        url = f'{self.base_url}/vacancies/{vacancy_id}'
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f'Ошибка API вакансии {vacancy_id}: {response.status_code}')
                return None
        except Exception as e:
            print(f'Ошибка запроса вакансии {vacancy_id}: {e}')
            return None
# Запуск ETL
if __name__ == "__main__":
    extractor = HHExtractor()
    extractor.run_etl()