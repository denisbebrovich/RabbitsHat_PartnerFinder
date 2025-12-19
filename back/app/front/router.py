from typing import List
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.utils import authenticate_user, set_tokens
from app.api.dependencies.auth_dep import get_current_user, get_current_admin_user, check_refresh_token
from app.api.dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException
from app.api.companies.dao import CompanyDAO
from app.api.companies.router import get_all_companies
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="app/front/templates")

resources = [
    {"name": "Авторизация", "url": "/auth"},
    {"name": "Компании", "url": "/companies"},
    {"name": "Вакансии", "url": "/vacancies"}]

@router.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse(
        name="base.html",
        request=request,
        context={"resources": resources}
    )

@router.get("/companies")
async def get_companies(request: Request, page: int = 0, per_page: int = 10, session: AsyncSession = Depends(get_session_with_commit)):
    receive_data = await get_all_companies(page, per_page, session)
    companies = receive_data['items']
    rows = [{"id": company.id, "data": company} for company in companies]
    rows.sort(key=lambda x: x["id"])
    return templates.TemplateResponse(
        name="companies.html",
        request=request,
        context={
            "title": "Компании",
            "create_item_url": "/companies/create",
            "resources": resources,
            "table_headers" : ["ID", "External ID", "Name"],
            # со списками некоторые проблемы (industries)
            "rows": rows,
            "page": page,
            "per_page": per_page,
            "total_pages": receive_data["total_pages"],
            "api_path": "/api/v1/companies"
        }
    )
