from app.api.dao.base import BaseDAO
from .models import Vacancy


class VacancyDAO(BaseDAO):
    model = Vacancy
