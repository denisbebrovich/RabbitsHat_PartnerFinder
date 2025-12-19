from app.api.dao.base import BaseDAO
from .models import Company

class CompanyDAO(BaseDAO):
    model = Company
