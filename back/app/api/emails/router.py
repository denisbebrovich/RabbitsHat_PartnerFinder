from typing import List
from fastapi import APIRouter, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.utils import authenticate_user, set_tokens
from app.api.dependencies.auth_dep import get_current_user, get_current_admin_user, check_refresh_token
from app.api.dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException
from .dao import EmailDAO

router = APIRouter()

@router.get("/")
async def get_all_vacancies(session: AsyncSession = Depends(get_session_with_commit)):
    return await EmailDAO(session).find_all()
