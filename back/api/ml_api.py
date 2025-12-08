from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DB.models import Company

router = APIRouter(prefix="/api/ml", tags=["ml"])

# Движок для БД
engine = create_engine('postgresql://admin:password@localhost:5432/partner_finder')
SessionLocal = sessionmaker(bind=engine)

def get_company_score(company):
    score = 0
    
    # 1. Количество технологий
    tech_count = len(company.tech_stack) if company.tech_stack else 0
    score += min(tech_count * 4, 40)
    
    # 2. IT-компания
    if company.is_it_company:
        score += 30
    
    # 3. Количество вакансий (пока заглушка)
    # TODO: Добавить подсчет вакансий
    vacancy_bonus = min(len(company.vacancies) * 2, 30) if hasattr(company, 'vacancies') else 0
    score += vacancy_bonus
    
    return min(score, 100)

@router.get("/company/{company_id}")
async def get_company_for_ml(company_id: str):
    """Данные компании для генерации письма"""
    session = SessionLocal()
    
    try:
        company = session.query(Company).filter_by(hh_id=company_id).first()
        
        if not company:
            return {"error": "Компания не найдена"}
        
        return {
            "company_id": company.hh_id,
            "name": company.name,
            "industries": company.industries,
            "tech_stack": company.tech_stack,
            "description": company.description,
            "is_it_company": company.is_it_company,
            "region": company.region,
            "site_url": company.site_url,
            "score": get_company_score(company)  # <-- ДОБАВЛЯЕМ SCORE
        }
    finally:
        session.close()

@router.get("/companies/for-generation")
async def get_companies_for_generation(
    min_score: int = 50,
    limit: int = 20
):
    """Список компаний для массовой генерации писем"""
    session = SessionLocal()
    
    try:
        all_companies = session.query(Company).all()
        
        # Сортируем по score
        companies_with_score = []
        for company in all_companies:
            score = get_company_score(company)
            if score >= min_score:
                companies_with_score.append({
                    "company_id": company.hh_id,
                    "name": company.name,
                    "score": score,
                    "tech_stack": company.tech_stack[:5] if company.tech_stack else []  # первые 5 технологий
                })
        
        # Сортируем по убыванию score и берем limit
        sorted_companies = sorted(companies_with_score, key=lambda x: x["score"], reverse=True)
        return sorted_companies[:limit]
        
    finally:
        session.close()