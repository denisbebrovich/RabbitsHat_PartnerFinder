from app.api.dao.base import BaseDAO
from .models import User, Role


class UsersDAO(BaseDAO):
    model = User


class RoleDAO(BaseDAO):
    model = Role
