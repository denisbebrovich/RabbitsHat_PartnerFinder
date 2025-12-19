from app.api.dao.base import BaseDAO
from .models import Email


class EmailDAO(BaseDAO):
    model = Email
