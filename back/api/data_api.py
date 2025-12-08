from fastapi import APIRouter, Query
from services.data_analyzer import DataAnalyzer

router = APIRouter(prefix="/api/data", tags=["data"])

@router.get("/companies")
async def get_companies(
    industry: str = None,
    techs: str = Query(None, description="Технологии через запятую: python,sql,react"),
    min_score: float = 0
):
    analyzer = DataAnalyzer()
    
    tech_list = techs.split(',') if techs else []
    companies = analyzer.get_companies_for_partnership(tech_list, industry)
    
    return [{
        "id": company.hh_id,
        "name": company.name,
        "industries": company.industries,
        "tech_stack": company.tech_stack,
        "score": analyzer.calculate_company_score(company) 
    } for company in companies if analyzer.calculate_company_score(company) >= min_score]

@router.get("/analytics/industries")
async def get_industry_stats():
    analyzer = DataAnalyzer()
    return analyzer.get_industry_stats()

@router.get("/analytics/technologies")
async def get_tech_stats(limit: int = 10):
    analyzer = DataAnalyzer()
    return analyzer.get_popular_technologies(limit)