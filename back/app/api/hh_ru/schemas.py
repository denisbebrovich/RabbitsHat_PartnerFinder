from pydantic import BaseModel, ConfigDict, EmailStr, Json, Field, field_validator, model_validator, computed_field
from app.api.auth.utils import get_password_hash
from datetime import datetime


class CompanyFilter(BaseModel):
    id: int | None = None
    external_id: int | None = None
    name: str | None = None
    is_it_company: bool | None = None
    industries: list[str] | None = None
    region: str | None = None
    tech_stack: list[str] | None = None
    description: str | None = None
    site_url: str | None = None

class VacancyFilter(BaseModel):
    id: int | None = None
    external_id: int | None = None
    title: str | None = None
    company_id: int | None = None
    external_company_id: int | None = None
    description: str | None = None
    source: str | None = None
    requirements: list[str] | None = None
    experience: str | None = None
    employment: str | None = None
    location: str | None = None
    professional_role: str | None = None
    published_at: datetime | None = None
