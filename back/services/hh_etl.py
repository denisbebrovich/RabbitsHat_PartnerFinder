# -*- coding: utf-8 -*-
import os
import sys
import requests
import time
import re
import html
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Настройка путей для корректного импорта из папки back
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

    def clean_html(self, raw_text):
        if not raw_text:
            return ""
        clean_text = re.sub('<[^<]+?>', '', raw_text)
        return html.unescape(clean_text).strip()

    def skills_extractor(self, vacancy_data):
        key_skills = vacancy_data.get('key_skills', [])
        if key_skills and isinstance(key_skills, list):
            return [skill['name'] for skill in key_skills]
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
            return None
        except Exception as e:
            print(f"Ошибка при запросе вакансий: {e}")
            return None

    def get_vacancy_details(self, vacancy_id):
        url = f'{self.base_url}/vacancies/{vacancy_id}'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Ошибка запроса деталей вакансии {vacancy_id}: {e}")
            return None

    def get_employer_details(self, employer_id):
        url = f"{self.base_url}/employers/{employer_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Ошибка запроса данных компании {employer_id}: {e}")
            return None

    def extract_company_info(self, employer_data, employer_details=None):
        if employer_details:
            industries = employer_details.get('industries', [])
            industry_names = [i['name'] for i in industries] if industries else []
            area = employer_details.get('area', {})
            region = area.get('name', 'Екатеринбург')
            description = self.clean_html(employer_details.get('description', ''))
            
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
        clean_description = self.clean_html(vacancy_data.get('description', ''))
        
        return {
            'hh_id': str(vacancy_data['id']),
            'title': vacancy_data['name'],
            'company_id': str(vacancy_data['employer']['id']),
            'description': clean_description,
            'source': 'hh.ru',
            'requirements': skills,
            'experience': vacancy_data.get('experience', {}).get('name', ''),
            'employment': vacancy_data.get('employment', {}).get('name', ''),
            'location': vacancy_data.get('area', {}).get('name', ''),
            'professional_role': vacancy_data.get('professional_roles', [{}])[0].get('name', '') if vacancy_data.get('professional_roles') else '',
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

    def run_etl(self, queries=['Python', 'Backend', 'Data Scientist'], pages=2):
        session = self.Session()
        employer_cache = {}
        companies_added = 0
        vacancies_added = 0
        
        for query in queries:
            for page in range(pages):
                print(f"\n[!] Поиск: '{query}', Страница: {page}")
                data = self.get_vacancies_by_query(query, area=3, per_page=100, page=page)
                
                if not data or 'items' not in data:
                    break
                    
                for v_short in data['items']:
                    try:
                        employer_id = str(v_short['employer']['id'])
                        if employer_id not in employer_cache:
                            details = self.get_employer_details(employer_id)
                            employer_cache[employer_id] = details
                            company_info = self.extract_company_info(v_short['employer'], details)
                            existing_company = session.query(Company).filter_by(hh_id=company_info['hh_id']).first()
                            if not existing_company:
                                company = Company(**company_info)
                                session.add(company)
                                session.flush()
                                companies_added += 1
                                print(f" [+] Компания: {company_info['name']}")

                        v_full = self.get_vacancy_details(v_short['id'])
                        if v_full:
                            vacancy_info = self.extract_vacancy_info(v_full)
                            if not session.query(Vacancy).filter_by(hh_id=vacancy_info['hh_id']).first():
                                session.add(Vacancy(**vacancy_info))
                                vacancies_added += 1
                        time.sleep(0.2)
                    except Exception as e:
                        session.rollback()
                        continue
        
        print("\n[!] Обновление стеков...")
        session.expire_all()
        for company in session.query(Company).all():
            self.update_company_tech_stack(session, company.hh_id)
        
        session.commit()
        session.close()
        print(f"[SUCCESS] Добавлено: {companies_added} комп., {vacancies_added} вак.")

if __name__ == "__main__":
    extractor = HHExtractor()
    target_queries = ['Python', 'Backend', 'Frontend', 'Data Engineer', 'DevOps', 'SQL', 'FastAPI']
    extractor.run_etl(queries=target_queries, pages=2)