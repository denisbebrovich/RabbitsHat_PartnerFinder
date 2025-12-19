from pydantic import BaseModel, ConfigDict, EmailStr, Json, Field, field_validator, model_validator, computed_field
from app.api.auth.utils import get_password_hash
from datetime import datetime


class SEmailInfo(BaseModel):
    id: int = Field(description="ID в БД")
    company_id: int = Field(description="ID компании в БД")
    external_company_id: int = Field(description="ID компании на сайте")
    content: str = Field(description="Тело письма")
    final_content: str = Field()
    status: str
    is_approved: bool
    human_feedback: str
    generation_params: str
    created_at: datetime
    