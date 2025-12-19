from typing import List
from fastapi import APIRouter, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.companies.models import Company
from app.api.auth.utils import authenticate_user, set_tokens
from app.api.dependencies.auth_dep import get_current_user, get_current_admin_user, check_refresh_token
from app.api.dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException
from app.api.companies.dao import CompanyDAO
from app.api.vacancies.dao import VacancyDAO
from .hh_etl import HHExtractor

router = APIRouter()

@router.post("/receive-data")
async def receive_hh_ru_data(session: AsyncSession = Depends(get_session_with_commit)):
    hh_extractor = HHExtractor(CompanyDAO(session), VacancyDAO(session))
    await hh_extractor.run_etl()
    return
