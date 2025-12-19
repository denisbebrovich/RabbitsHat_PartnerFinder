from sqlalchemy import DateTime, Text, ForeignKey, Integer, String, JSON, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList
from app.api.dao.database import Base
from datetime import datetime, timezone

class Email(Base):
    __tablename__ = 'emails'
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id', ondelete='CASCADE'))
    external_company_id: Mapped[int] # = Column(String, ForeignKey('companies.hh_id'))
    content: Mapped[str] = mapped_column(Text)
    final_content: Mapped[str] = mapped_column(Text)
    status: Mapped[str]
    is_approved: Mapped[bool]
    human_feedback: Mapped[str] = mapped_column(Text)
    generation_params: Mapped[str] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    company: Mapped["Company"] = relationship("Company", back_populates="emails", lazy="joined")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"
