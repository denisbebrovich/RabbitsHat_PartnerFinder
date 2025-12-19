import os
import sys
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time
import re

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from DB.models import Company, Vacancy


class HHExtractor:
    def __init__(self, db_url='postgresql://admin:password@localhost:5432/partner_finder'):
        self.db_engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.db_engine)
        self.base_url = 'https://api.hh.ru'

    def skills_extractor(self, vacancy_data):
        key_skills = vacancy_data.get('key_skills', [])
        if key_skills and isinstance(key_skills, list):
            skills_list = [skill['name'] for skill in key_skills]
            return skills_list
        else:
            return []

    def get_vacancies_by_query(self, query, area=3, per_page=100, page=0):
        url = f'{self.base_url}/vacancies'
        params = {
            'text': query,
            'area': area,
            'per_page': per_page,
            'page': page
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f'Ошибка API (Status {response.status_code})')
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
                return None
        except Exception as e:
            return None

    def extract_company_info(self, employer_data, employer_details=None):
        if employer_details:
            industries = employer_details.get('industries', [])
            industry_names = [industry['name'] for industry in industries] if industries else []

            area = employer_details.get('area', {})
            region = area.get('name', 'Екатеринбург')

            description = employer_details.get('description', '')
            if description:
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
            'description': vacancy_data.get('description'),
            'source': 'hh.ru',
            'requirements': skills,
            'experience': vacancy_data.get('experience', {}).get('name', ''),
            'employment': vacancy_data.get('employment', {}).get('name', ''),
            'location': vacancy_data.get('area', {}).get('name', ''),
            'professional_role': vacancy_data.get('professional_roles', [{}])[0].get('name', '') if vacancy_data.get(
                'professional_roles') else '',
            'published_at': vacancy_data.get('published_at')
        }

    def update_company_tech_stack(self, session, company_hh_id):
        company_vacancies = session.query(Vacancy).filter_by(company_id=company_hh_id).all()
        all_skills = []
        for vacancy in company_vacancies:
            if vacancy.requirements:
                all_skills.extend(vacancy.requirements)

        unique_skills = list(set(all_skills))
        company = session.query(Company).filter_by(hh_id=company_hh_id).first()
        if company:
            company.tech_stack = unique_skills

    def get_vacancy_details(self, vacancy_id):
        url = f'{self.base_url}/vacancies/{vacancy_id}'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    def run_etl(self):
        session = self.Session()
        employer_cache = {}

        queries = [
            'Python разработчик',
            'Java разработчик',
            'Frontend разработчик',
            'DevOps инженер',
            'Системный администратор',
            'C++ разработчик',
            'Data Scientist',
            'Аналитик данных'
        ]

        companies_added = 0
        vacancies_added = 0

        print("=== НАЧАЛО МАСШТАБНОГО СБОРА ДАННЫХ ===")

        for query in queries:
            print(f"\n🔎 Запрос: '{query}'")

            for page in range(5):
                print(f"   -> Страница {page}...")

                data = self.get_vacancies_by_query(query, area=3, per_page=100, page=page)

                if not data or 'items' not in data or not data['items']:
                    print("      Нет данных или конец списка.")
                    break

                print(f"      Найдено вакансий на странице: {len(data['items'])}")

                for vacancy_data in data['items']:
                    try:
                        employer_id = str(vacancy_data['employer']['id'])

                        if employer_id not in employer_cache:
                            employer_details = self.get_employer_details(employer_id)
                            employer_cache[employer_id] = employer_details
                            time.sleep(0.2)
                        else:
                            employer_details = employer_cache[employer_id]

                        company_info = self.extract_company_info(vacancy_data['employer'], employer_details)

                        if not session.query(Company).filter_by(hh_id=company_info['hh_id']).first():
                            company = Company(**company_info)
                            session.add(company)
                            session.flush()
                            companies_added += 1

                        if not session.query(Vacancy).filter_by(hh_id=str(vacancy_data['id'])).first():
                            vacancy_details = self.get_vacancy_details(vacancy_data['id'])
                            if vacancy_details:
                                vacancy_info = self.extract_vacancy_info(vacancy_details)
                            else:
                                vacancy_info = self.extract_vacancy_info(vacancy_data)

                            vacancy = Vacancy(**vacancy_info)
                            session.add(vacancy)
                            vacancies_added += 1

                    except Exception as e:
                        session.rollback()
                        continue

                session.commit()
                time.sleep(0.5)

        print("\n⏳ Обновляем технологические стеки компаний...")
        companies = session.query(Company).all()
        for company in companies:
            self.update_company_tech_stack(session, company.hh_id)

        session.commit()
        session.close()

        print(f"\n=== ИТОГ ===")
        print(f"Всего компаний в БД: {len(companies)}")
        print(f"Новых компаний добавлено в этом запуске: {companies_added}")
        print(f"Новых вакансий добавлено в этом запуске: {vacancies_added}")

if __name__ == "__main__":
    extractor = HHExtractor()
    extractor.run_etl()