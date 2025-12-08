from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from DB.models import Company, Vacancy

class DataAnalyzer:
    def __init__(self, db_url="postgresql://admin:password@localhost:5432/partner_finder"):
        self.db_engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.db_engine)
    
    def get_industry_stats(self):
        session = self.Session()
        
        all_companies = session.query(Company).all()
        
        industry_stats = {}
        for company in all_companies:
            if company.industries:
                for industry in company.industries:
                    if industry not in industry_stats:
                        industry_stats[industry] = {
                            'company_count': 0,
                            'total_tech_count': 0
                        }
                    industry_stats[industry]['company_count'] += 1
                    industry_stats[industry]['total_tech_count'] += len(company.tech_stack) if company.tech_stack else 0
        
        # Форматируем результат
        result = []
        for industry, stats in industry_stats.items():
            avg_tech_count = stats['total_tech_count'] / stats['company_count'] if stats['company_count'] > 0 else 0
            result.append({
                'industry': industry,
                'company_count': stats['company_count'],
                'avg_tech_count': round(avg_tech_count, 2)
            })
        
        session.close()
        return sorted(result, key=lambda x: x['company_count'], reverse=True)
    
    def get_popular_technologies(self, limit=10):
        session = self.Session()
        
        all_tech = []
        companies = session.query(Company).all()
        for company in companies:
            if company.tech_stack:
                all_tech.extend(company.tech_stack)
        
        from collections import Counter
        tech_counter = Counter(all_tech)
        
        session.close()
        return tech_counter.most_common(limit)
    
    def get_companies_for_partnership(self, required_techs, industry=None):
        session = self.Session()
        
        query = session.query(Company)
        
        # Фильтр по отрасли если указана
        if industry:
            companies = []
            for company in query.all():
                if company.industries and industry in company.industries:
                    companies.append(company)
        else:
            companies = query.all()
        
        # Ищем компании, у которых есть все требуемые технологии
        matching_companies = []
        for company in companies:
            if company.tech_stack and all(tech in company.tech_stack for tech in required_techs):
                matching_companies.append(company)
        
        session.close()
        return matching_companies
    
    def get_companies_by_industry(self, industry_name):
        session = self.Session()
        
        companies = []
        all_companies = session.query(Company).all()
        for company in all_companies:
            if company.industries and industry_name in company.industries:
                companies.append(company)
        
        session.close()
        return companies
    
    def get_technology_distribution(self):
        session = self.Session()
        
        distribution = {}
        companies = session.query(Company).all()
        
        for company in companies:
            if company.industries and company.tech_stack:
                for industry in company.industries:
                    if industry not in distribution:
                        distribution[industry] = {}
                    
                    for tech in company.tech_stack:
                        distribution[industry][tech] = distribution[industry].get(tech, 0) + 1
        
        session.close()
        return distribution
    
    def get_top_companies_by_tech_stack(self, min_tech_count=3):
        session = self.Session()
        
        companies = session.query(Company).all()
        filtered_companies = [
            company for company in companies 
            if company.tech_stack and len(company.tech_stack) >= min_tech_count
        ]
        
        # Сортируем по количеству технологий
        sorted_companies = sorted(
            filtered_companies, 
            key=lambda x: len(x.tech_stack), 
            reverse=True
        )
        
        session.close()
        return sorted_companies
    
    def get_vacancy_stats(self):
        session = self.Session()
        
        total_vacancies = session.query(func.count(Vacancy.hh_id)).scalar()
        
        # Вакансии по опыту
        experience_stats = session.query(
            Vacancy.experience,
            func.count(Vacancy.hh_id)
        ).group_by(Vacancy.experience).all()
        
        # Вакансии по типу занятости
        employment_stats = session.query(
            Vacancy.employment,
            func.count(Vacancy.hh_id)
        ).group_by(Vacancy.employment).all()
        
        session.close()
        
        return {
            'total_vacancies': total_vacancies,
            'experience_distribution': dict(experience_stats),
            'employment_distribution': dict(employment_stats)
        }
    
    def calculate_company_score(self, company):
        score = 0
        
        tech_count = len(company.tech_stack) if company.tech_stack else 0
        score += min(tech_count * 4, 40)  
        
        if company.is_it_company:
            score += 30
                
        return min(score, 100)
