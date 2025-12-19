from typing import List
from fastapi import APIRouter, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Company
from app.api.auth.utils import authenticate_user, set_tokens
from app.api.dependencies.auth_dep import get_current_user, get_current_admin_user, check_refresh_token
from app.api.dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException
from .dao import CompanyDAO
from .schemas import SCompanyDelete, SCompanyUpdate

router = APIRouter()

@router.post("/")
async def create_company():
    pass

@router.get("/")
async def get_all_companies(
    page: int = 0,
    per_page: int = 10,
    session: AsyncSession = Depends(get_session_with_commit)
    ):
    companies = await CompanyDAO(session).find_all()
    total_pages = len(companies) // per_page + (1 if len(companies) % per_page > 0 else 0)
    start = page * per_page
    end = start + per_page
    return {"total_pages": total_pages, "items": companies[start:end]}

@router.patch("/{id}") # fix
async def update_company(id: int, company_update: SCompanyUpdate, session: AsyncSession = Depends(get_session_with_commit)):
    dao = CompanyDAO(session)
    await dao.update(SCompanyDelete(id=id), company_update)
    return dao.find_one_or_none_by_id(id)

@router.delete("/{id}")
async def delete_company(id: int, session: AsyncSession = Depends(get_session_with_commit)):
    dao = CompanyDAO(session)
    company = await dao.find_one_or_none_by_id(id)
    company_delete = SCompanyDelete(id=id)
    await dao.delete(company_delete)
    return company
