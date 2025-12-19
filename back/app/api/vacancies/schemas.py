from pydantic import BaseModel, ConfigDict, EmailStr, Json, Field, field_validator, model_validator, computed_field
from app.api.auth.utils import get_password_hash
from datetime import datetime


class SVacancyInfo(BaseModel):
    id: int = Field(description="ID в БД")
    external_id: int = Field(description="ID на сайте")
    title: str = Field(description="Название вакансии")
    company_id: int = Field(description="ID компании в БД")
    external_company_id: int = Field(description="ID компании на сайте")
    description: str = Field(description="Описание компании")
    source: str = Field(description="Источник (сайт) с вакансиями")
    requirements: list[str] = Field(description="Требования к соискателю")
    experience: str = Field(description="Опыт работы")
    employment: str = Field()
    location: str = Field(description="Местоположение")
    professional_role: str = Field()
    published_at: datetime = Field(description="Время публикации")
    