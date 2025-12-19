from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from DB.models import Company, Vacancy
from collections import Counter

class DataAnalyzer:
    def __init__(self, db_url="postgresql://admin:password@localhost:5432/partner_finder"):
        self.db_engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.db_engine)
    
    def get_industry_stats(self):
        session = self.Session()
        try:
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
            
            result = []
            for industry, stats in industry_stats.items():
                avg_tech_count = stats['total_tech_count'] / stats['company_count'] if stats['company_count'] > 0 else 0
                result.append({
                    'industry': industry,
                    'company_count': stats['company_count'],
                    'avg_tech_count': round(avg_tech_count, 2)
                })
            return sorted(result, key=lambda x: x['company_count'], reverse=True)
        finally:
            session.close()
    
    def get_popular_technologies(self, limit=10):
        session = self.Session()
        try:
            all_tech = []
            companies = session.query(Company).all()
            for company in companies:
                if company.tech_stack:
                    all_tech.extend(company.tech_stack)
            tech_counter = Counter(all_tech)
            return tech_counter.most_common(limit)
        finally:
            session.close()

    def get_competence_gap_analysis(self, program_stack):
        session = self.Session()
        try:
            vacancies = session.query(Vacancy).all()
            market_skills = []
            for v in vacancies:
                if v.requirements:
                    market_skills.extend(v.requirements)
            
            tech_counter = Counter(market_skills)
            program_stack_low = [s.lower() for s in program_stack]
            
            gaps = []
            for skill, count in tech_counter.most_common(30):
                if skill.lower() not in program_stack_low:
                    gaps.append({
                        "skill": skill,
                        "market_demand": count
                    })
                if len(gaps) >= 10:
                    break
            return gaps
        finally:
            session.close()

    def get_stack_comparison_lists(self, company_id, program_stack):
        """Возвращает два списка компетенций для прямого сравнения."""
        session = self.Session()
        try:
            company = session.query(Company).filter_by(hh_id=company_id).first()
            if not company:
                return None
            
            company_stack = company.tech_stack if company.tech_stack else []
            return {
                "company_name": company.name,
                "urfu_stack": program_stack,
                "company_stack": company_stack
            }
        finally:
            session.close()
    
    def get_companies_for_partnership(self, required_techs, industry=None):
        session = self.Session()
        try:
            query = session.query(Company)
            companies = query.all()
            matching_companies = []
            for company in companies:
                if industry and (not company.industries or industry not in company.industries):
                    continue
                if required_techs:
                    if not company.tech_stack:
                        continue
                    company_stack_low = [t.lower() for t in company.tech_stack]
                    if not all(tech.lower() in company_stack_low for tech in required_techs):
                        continue
                matching_companies.append(company)
            return matching_companies
        finally:
            session.close()
    
    def calculate_company_score(self, company):
        score = 0
        tech_count = len(company.tech_stack) if company.tech_stack else 0
        score += min(tech_count * 4, 40)  
        if company.is_it_company:
            score += 30
        if company.description and len(company.description) > 100:
            score += 20
        if company.site_url:
            score += 10
        return min(score, 100)

    def get_vacancy_stats(self):
        session = self.Session()
        try:
            total_vacancies = session.query(func.count(Vacancy.hh_id)).scalar()
            experience_stats = session.query(Vacancy.experience, func.count(Vacancy.hh_id)).group_by(Vacancy.experience).all()
            employment_stats = session.query(Vacancy.employment, func.count(Vacancy.hh_id)).group_by(Vacancy.employment).all()
            return {
                'total_vacancies': total_vacancies,
                'experience_distribution': dict(experience_stats),
                'employment_distribution': dict(employment_stats)
            }
        finally:
            session.close()