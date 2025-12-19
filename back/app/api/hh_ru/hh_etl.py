import os
import sys
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import time
from loguru import logger
import re

from app.api.companies.models import Company
from app.api.companies.dao import CompanyDAO
from app.api.vacancies.models import Vacancy
from app.api.vacancies.dao import VacancyDAO
from .schemas import CompanyFilter, VacancyFilter


class HHExtractor:
    def __init__(self, company_dao: CompanyDAO, vacancy_dao: VacancyDAO):
        self.base_url = 'https://api.hh.ru'
        self.company_dao = company_dao
        self.vacancy_dao = vacancy_dao
    
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
                logger.error(f'Ошибка API: {response.status_code}')
                return None
        except Exception as e:
            logger.error(f'Ошибка при запросе: {e}')
            return None 

    def get_employer_details(self, employer_id):
        url = f"{self.base_url}/employers/{employer_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка API employers для {employer_id}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Ошибка запроса employers для {employer_id}: {e}")
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
                'external_id': int(employer_data['id']),
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
                'external_id': int(employer_data['id']),
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
            'external_id': int(vacancy_data['id']),
            'title': vacancy_data['name'],
            'external_company_id': str(vacancy_data['employer']['id']),
            'description': vacancy_data.get('description'),
            'source': 'hh.ru',
            'requirements': skills,
            'experience': vacancy_data.get('experience', {}).get('name', ''),
            'employment': vacancy_data.get('employment', {}).get('name', ''),
            'location': vacancy_data.get('area', {}).get('name', ''),
            'professional_role': vacancy_data.get('professional_roles', [{}])[0].get('name', '') if vacancy_data.get('professional_roles') else '',
            'published_at': datetime.strptime(vacancy_data.get('published_at'), '%Y-%m-%dT%H:%M:%S%z')
        }
    
    async def update_company_tech_stack(self, company_hh_id):
        # Получаем все вакансии компании
        vacancy_filter = VacancyFilter(company_id=company_hh_id)
        company_vacancies = await self.vacancy_dao.find_all(vacancy_filter) #session.query(Vacancy).filter_by(company_id=company_hh_id).all()
        
        # Собираем все навыки из всех вакансий
        all_skills = []
        for vacancy in company_vacancies:
            if vacancy.requirements:
                all_skills.extend(vacancy.requirements)
        
        # Убираем дубликаты
        unique_skills = list(set(all_skills))
        
        # Обновляем компанию
        company_filter = CompanyFilter(external_id=company_hh_id)
        company = await self.company_dao.find_one_or_none(company_filter) # session.query(Company).filter_by(hh_id=company_hh_id).first()
        if company:
            company.tech_stack = unique_skills
            await self.company_dao.bulk_update([CompanyFilter(**company.to_dict())])
            logger.info(f"Обновлен стек технологий для {company.name}: {len(unique_skills)} навыков")

    async def run_etl(self, queries=['Python разработчик']):
        # session = self.Session()
        
        # Словарь для кэширования данных о компаниях
        employer_cache = {}
        
        # Счетчики для статистики
        companies_added = 0
        vacancies_added = 0
        
        for query in queries:
            logger.info(f"Собираем вакансии по запросу: '{query}' в Екатеринбурге")
            
            # Получаем вакансии по запросу
            data = self.get_vacancies_by_query(query, area=3, per_page=20)
            if not data or 'items' not in data:
                logger.info(f"Нет данных для запроса: {query}")
                continue
                
            logger.info(f"Найдено вакансий: {len(data['items'])}")
            
            for vacancy_data in data['items']:
                try:
                    employer_id = str(vacancy_data['employer']['id'])
                    
                    # Получаем детальную информацию о компании
                    if employer_id not in employer_cache:
                        logger.info(f"Получаем информацию о компании {employer_id}...")
                        employer_details = self.get_employer_details(employer_id)
                        employer_cache[employer_id] = employer_details
                        time.sleep(0.5)
                    else:
                        employer_details = employer_cache[employer_id]
                    
                    # Извлекаем данные компании
                    company_info = self.extract_company_info(
                        vacancy_data['employer'], 
                        employer_details
                    )
                    
                    # Проверяем и добавляем компанию
                    company_filter = CompanyFilter(external_id=company_info['external_id'])
                    existing_company = await self.company_dao.find_one_or_none(company_filter) # session.query(Company).filter_by(hh_id=company_info['hh_id']).first()
                    if not existing_company:
                        company = CompanyFilter(**company_info)
                        # session.add(company)
                        # session.flush()
                        await self.company_dao.add(company)
                        companies_added += 1
                        logger.info(f"Добавлена компания: {company_info['name']}")
                    
                    # Получаем полную информацию о вакансии с навыками
                    vacancy_details = self.get_vacancy_details(vacancy_data['id'])
                    if vacancy_details:
                        vacancy_info = self.extract_vacancy_info(vacancy_details)
                        logger.info(f"Навыки вакансии '{vacancy_info['title']}': {vacancy_info['requirements']}")
                    else:
                        vacancy_info = self.extract_vacancy_info(vacancy_data)
                        logger.info(f"Нет навыков для вакансии '{vacancy_info['title']}'")
                    
                    # Извлекаем и добавляем вакансию
                    vacancy_filter = VacancyFilter(external_id=vacancy_info['external_id'])
                    existing_vacancy = await self.vacancy_dao.find_one_or_none(vacancy_filter) # session.query(Vacancy).filter_by(hh_id=vacancy_info['hh_id']).first()
                    if not existing_vacancy:
                        vacancy = VacancyFilter(**vacancy_info)
                        company = await self.company_dao.find_one_or_none(CompanyFilter(external_id=company_info['external_id']))
                        vacancy.company_id = company.id
                        # session.add(vacancy)
                        await self.vacancy_dao.add(vacancy)
                        vacancies_added += 1
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    # session.rollback()
                    logger.error(f"Ошибка обработки вакансии: {e}")
                    continue
                
            time.sleep(1)
        
        #  Принудительно обновляем сессию для новых компаний
        logger.info("Обновляем технологические стеки компаний...")
        # session.expire_all()  # обновляем состояние всех объектов в сессии
        
        # Теперь получаем ВСЕ компании с актуальными данными
        companies = await self.company_dao.find_all() # session.query(Company).all()
        logger.info(f"Всего компаний для обновления стеков: {len(companies)}")
        
        for company in companies:
            await self.update_company_tech_stack(company.external_id)
        
        # Сохраняем все изменения
        # session.commit()
        # session.close()
        
        # Выводим статистику
        logger.info(f"ETL процесс завершен!")
        logger.info(f"Компаний добавлено: {companies_added}")
        logger.info(f"Вакансий добавлено: {vacancies_added}")
        logger.info(f"Всего компаний в БД: {len(companies)}")

    def get_vacancy_details(self, vacancy_id):
        url = f'{self.base_url}/vacancies/{vacancy_id}'
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f'Ошибка API вакансии {vacancy_id}: {response.status_code}')
                return None
        except Exception as e:
            logger.error(f'Ошибка запроса вакансии {vacancy_id}: {e}')
            return None

# Запуск ETL
# if __name__ == "__main__":
#     extractor = HHExtractor()
#     extractor.run_etl()