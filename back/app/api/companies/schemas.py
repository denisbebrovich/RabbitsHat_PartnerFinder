from pydantic import BaseModel, ConfigDict, EmailStr, Json, Field, field_validator, model_validator, computed_field
from app.api.auth.utils import get_password_hash


class SCompanyInfo(BaseModel):
    id: int = Field(description="ID в БД")
    external_id: int = Field(description="ID на сайте")
    name: str = Field(description="Имя компании")
    is_it_company: bool = Field(description="Компания из сферы ИТ")
    industries: list[str] = Field(description="Индустрии, в которых работает компания")
    region: str = Field(description="Регион компании")
    tech_stack: list[str] = Field(description="Технический стек компании")
    description: str = Field(description="Описание компании")
    site_url: str = Field(description="URL на сайт компании")

class SCompanyDelete(BaseModel):
    id: int = Field(description="ID в БД")

class SCompanyUpdate(BaseModel):
    external_id: int | None = None
    name: str | None = None
    is_it_company: bool | None = None
    industries: list[str] | None = None
    region: str | None = None
    tech_stack: list[str] | None = None
    description: str | None = None
    site_url: str | None = None
