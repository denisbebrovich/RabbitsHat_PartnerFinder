from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from services.data_analyzer import DataAnalyzer
from DB.models import AgentBehaviorLog, Vacancy

router = APIRouter(prefix="/api/data", tags=["data"])

class LogCreate(BaseModel):
    company_id: str
    prompt_sent: str
    generated_letter: str
    user_edits: str = None
    is_approved: bool = False

@router.get("/companies")
async def get_companies(industry: str = None, techs: str = Query(None), min_score: float = 0):
    analyzer = DataAnalyzer()
    tech_list = techs.split(',') if techs else []
    companies = analyzer.get_companies_for_partnership(tech_list, industry)
    
    return [{
        "id": company.hh_id,
        "name": company.name,
        "industries": company.industries,
        "tech_stack": company.tech_stack,
        "description": company.description,
        "score": analyzer.calculate_company_score(company) 
    } for company in companies if analyzer.calculate_company_score(company) >= min_score]

@router.get("/comparison/{company_id}")
async def get_stack_comparison(company_id: str):
    """Возвращает список компетенций УрФУ и список компетенций компании."""
    analyzer = DataAnalyzer()
    program_stack = ["Python", "FastAPI", "PostgreSQL", "Docker", "Git", "SQL", "Linux"]
    
    result = analyzer.get_stack_comparison_lists(company_id, program_stack)
    if not result:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    return result

@router.get("/vacancies")
async def get_vacancies(company_id: str = None, limit: int = 50):
    analyzer = DataAnalyzer()
    session = analyzer.Session()
    try:
        query = session.query(Vacancy)
        if company_id:
            query = query.filter(Vacancy.company_id == company_id)
        vacancies = query.limit(limit).all()
        return vacancies
    finally:
        session.close()

@router.get("/analytics/industries")
async def get_industry_stats():
    return DataAnalyzer().get_industry_stats()

@router.get("/analytics/technologies")
async def get_tech_stats(limit: int = 10):
    return DataAnalyzer().get_popular_technologies(limit)

@router.get("/analytics/competence-gap")
async def get_competence_gap():
    program_stack = ["Python", "FastAPI", "PostgreSQL", "Docker"]
    return {
        "program_stack": program_stack,
        "market_demand_gaps": DataAnalyzer().get_competence_gap_analysis(program_stack)
    }

@router.post("/logs")
async def create_log(log_data: LogCreate):
    analyzer = DataAnalyzer()
    session = analyzer.Session()
    try:
        new_log = AgentBehaviorLog(**log_data.dict())
        session.add(new_log)
        session.commit()
        return {"status": "success", "id": new_log.id}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()