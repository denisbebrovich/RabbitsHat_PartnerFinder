from sqlalchemy import DateTime, Text, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList
from app.api.dao.database import Base
from datetime import datetime, timezone

class Vacancy(Base):
    __tablename__ = 'vacancies'
    external_id: Mapped[int] # Column(String, primary_key = True)
    title: Mapped[str] # = Column(String(500))
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id', ondelete='CASCADE'))
    external_company_id: Mapped[int] # = Column(String, ForeignKey('companies.hh_id'))
    description: Mapped[str] = mapped_column(Text, nullable=True) # = Column(Text)
    source: Mapped[str] = mapped_column(default=text('hh.ru')) # Column(String(100), default='hh.ru')
    requirements: Mapped[list[str]] = mapped_column(MutableList.as_mutable(ARRAY(String))) # = Column(JSON)
    experience: Mapped[str] # = Column(String(100))
    employment: Mapped[str] # = Column(String(100))
    location: Mapped[str] # = Column(String(100))
    professional_role: Mapped[str] # = Column(String(200))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc)) # Column(DateTime, default = datetime.utcnow)
    
    company: Mapped["Company"] = relationship("Company", back_populates="vacancies", lazy="joined")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"
